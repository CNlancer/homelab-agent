# Home Assistant Restart-Triggered Light False Positives

## Summary

This note captures a Home Assistant reliability issue on the Unraid-hosted HA
instance at `10.0.0.11` where hallway or entrance lights could stay on after a
restart, or a lock-linked light could turn on during startup even though no one
just opened the door.

Two different failure modes were involved:

- HA restarted while a motion/lock automation was mid-run, so the final
  `light.turn_off` step never executed.
- A `state` trigger on an `event.*` entity restored an old event timestamp on
  startup, which looked enough like a fresh event to risk a false trigger.

## Environment

- Home Assistant container: `home-assistant`
- Config path: `/mnt/user/appdata/home-assistant`
- Main file touched: `/mnt/user/appdata/home-assistant/automations.yaml`

## Symptoms

- After restarting HA, `light.magic_switch_s1e_d73a_switch_2` could remain on.
- Entrance lights controlled by `玄关动作灯光联动` could also remain on if HA
  restarted during the `wait_for_trigger` window.
- `门锁联动` used a `state` trigger on:

```text
event.loock_cn_1056643124_t1pro_lock_opened_e_2_1
```

- Recorder history showed the lock event entity bouncing through startup
  restore states around HA restarts, while the hallway light entity also hit
  `unavailable` during restart windows.

## Root Cause

### 1. Restart interrupts waiting automations

Automations like `玄关动作灯光联动` and `门锁联动` turn lights on first, then wait
for `no_motion` before turning them off.

If Home Assistant restarts during that wait:

- the running automation instance is lost
- the cleanup `light.turn_off` action never runs
- the light can stay on indefinitely

### 2. `event.*` state restore is not restart-safe by itself

`门锁联动` watched an `event.*` entity through a generic `state` trigger. On
startup, HA could restore the last timestamp-like state value for that entity.

Even when `unknown` and `unavailable` are filtered, startup restore behavior is
still risky because old event payloads can resemble a real new event.

For timestamp-like event-state entities, a recency guard is needed.

## Durable Fix

Two changes were applied.

### 1. Tighten `门锁联动`

The automation now only accepts lock-event state changes whose new state parses
as a timestamp within the last 15 seconds:

```jinja2
{% set event_ts = as_timestamp(trigger.to_state.state, 0) %}
{{ ... and event_ts > 0 and (as_timestamp(now()) - event_ts) < 15 }}
```

This keeps real lock events working while rejecting restored old timestamps
during startup.

### 2. Expand the startup safety automation

The old restart safeguard only turned off:

```text
light.magic_switch_s1e_d73a_switch_2
```

It was expanded into a broader delayed-off startup automation that also turns
off the three entrance-light devices used by `玄关动作灯光联动`.

This covers the "restart interrupted the previous automation" failure mode.

## Verification

Use this sequence after changes:

1. Run config validation:

```bash
docker exec home-assistant python -m homeassistant --script check_config --config /config
```

2. Restart HA:

```bash
docker restart home-assistant
```

3. Wait past the delayed-off window.

4. Verify:
   - HA UI returns `200` on `http://10.0.0.11:8123`
   - latest state chain for the hallway light shows restart recovery, e.g.
     `unavailable -> off`
   - no config errors appear in `home-assistant.log`

## Lessons Learned

- `mode: restart` helps overlap handling, but it does not protect an in-flight
  automation from HA itself restarting.
- Startup delayed-off automations are a valid safety net for lights that must
  never stay on after controller restarts.
- `event.*` entities are not the same as purpose-built device triggers; if
  forced to use a state trigger on them, add recency validation.
