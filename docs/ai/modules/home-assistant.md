# Home Assistant

## Responsibility

This module captures live Home Assistant operating knowledge for the
Unraid-hosted instance.

Use it when changing:

- automations in `/config/automations.yaml`
- core config in `/config/configuration.yaml`
- entity, device, or area registry data under `/config/.storage/`
- room-facing behavior such as curtains, lights, dashboards, and startup safety

## Current Deployment

- Primary instance: Home Assistant on Unraid at `10.0.0.11`
- Container: `home-assistant`
- Remote config path: `/mnt/user/appdata/home-assistant`
- In-container config path: `/config`
- Local operational audit log: `var/ops-log.jsonl`

Keep credentials in `local/secrets/`. Do not copy tokens, cookies, or SSH
passwords into docs, prompts, or audit records.

## Safe Change Pattern

For live config edits:

1. Capture current evidence from the real instance.
2. Back up the target file on the remote host before editing.
3. Apply the smallest config change.
4. Run:

```sh
docker exec home-assistant python -m homeassistant --script check_config --config /config
```

5. Reload the affected integration if a reliable authenticated API path exists.
   Otherwise restart the `home-assistant` container.
6. Verify HTTP reachability and the relevant registered entities/states.
7. Append a sanitized record to `var/ops-log.jsonl`.

The quickest host-side check remains:

```sh
curl http://10.0.0.11:8123
```

Use `GET`, not only `HEAD`; this instance may return `405` to `HEAD` while the
UI is healthy.

## Morning And Evening Curtain Automation

The current bedroom automation set uses:

- workday morning at `06:00`
- rest-day morning at `08:00`
- every evening at `22:00`

The workday condition is `binary_sensor.zhong_guo_fa_ding_gong_zuo_ri`, a
template sensor layered on top of the existing `binary_sensor.gong_zuo_ri`
Workday integration.

Why the template exists:

- The existing Workday integration is configured for `country: CN`.
- Its `python-holidays` source handles Chinese public holidays.
- Weekend make-up workdays still need explicit yearly overrides for this home.
- For 2026, the override list was taken from the State Council holiday notice:
  `2026-01-04`, `2026-02-14`, `2026-02-28`, `2026-05-09`,
  `2026-09-20`, and `2026-10-10`.

Maintenance rule: when a new annual State Council holiday schedule is
published, update the template sensor override list before relying on the
automation for that year.

Current entities used by the morning/evening routine:

- `cover.curtain_4`: bedroom curtain target
- `cover.curtain_5`: closet curtain target, assigned to the `衣柜` area
- `light.bedroom_left_bedside_light`: virtual light for the left bedside key
- `light.bedroom_right_bedside_light`: virtual light for the right bedside key

Do not include `cover.curtain_3` in this routine unless the user explicitly
changes the requirement. It was intentionally excluded because it appears to be
the bedroom sheer curtain and the user said the bedroom sheer curtain should not
open.

Do not use `light.wo_shi_deng` for the morning routine. It is a broad bedroom
light group and can turn on the ceiling light, bed strip, airer light, and other
unwanted bedroom/closet-adjacent lights. The desired morning light behavior is
only the left and right bedside virtual lights. The middle key is the ceiling
light and should stay off in the morning routine.

Known room corrections from the bedroom audit:

- `light.lightbulb_9` is `衣柜吸顶灯`, not a bedroom ceiling light. Its device
  belongs in `closet`, and `configuration.yaml` should expose it as `衣柜吸顶灯`
  / `衣柜灯`.
- `light.heater_lightbulb` is `主卫浴霸灯`, not a bedroom heater light. The
  Aqara `AX021` heater device belongs in `main_bathroom`, and the main-bathroom
  light group should include this light.
- `light.wo_shi_deng` should not include closet or main-bathroom fixtures.

## Entity Modeling Rules

Model physical controls separately from the semantic device they operate.

For wall switches:

- Physical HomeKit switch entities keep switch-key names.
  - Example: `switch.wall_switch_switch1_5` is `卧室开关左键`.
  - Example: `switch.wall_switch_switch2_5` is `卧室开关中键`.
  - Example: `switch.wall_switch_switch3_2` is `卧室开关右键`.
- User-facing light controls should be `light.*` entities.
  - Example: `light.bedroom_left_bedside_light` is `卧室左床头灯`.
  - Example: `light.bedroom_ceiling_light` is `卧室顶灯`.
  - Example: `light.bedroom_right_bedside_light` is `卧室右床头灯`.
- Use `switch_as_x` when a physical switch controls a light or fan but HA
  imports it as `switch.*`.
- Automations, room light groups, and HomeKit exposure should target the
  semantic `light.*` entity, not the raw physical `switch.*`, unless the task is
  explicitly about the switch hardware itself.
- Maintenance entities such as HomeKit `Identify` buttons should be disabled
  when they clutter a user-facing device. Keep rollback cheap by setting
  `disabled_by: user` rather than deleting them.

This keeps UI and voice control aligned with the real-world object while still
preserving the underlying switch-key identity.

For newly created semantic entities, prefer English `entity_id` values and
Chinese display names. Existing imported entity IDs may remain stable unless
there is a deliberate migration plan.

The bedroom three-key switch should have exactly six active user-facing
entities:

- three physical switch-key entities:
  - `switch.wall_switch_switch1_5`: `卧室开关左键`
  - `switch.wall_switch_switch2_5`: `卧室开关中键`
  - `switch.wall_switch_switch3_2`: `卧室开关右键`
- three semantic virtual light entities:
  - `light.bedroom_left_bedside_light`: `卧室左床头灯`
  - `light.bedroom_ceiling_light`: `卧室顶灯`
  - `light.bedroom_right_bedside_light`: `卧室右床头灯`

If this device shows more active entities, check for stale `switch_as_x`
experiments. In the May 2026 cleanup, orphan virtual lights with old unique IDs
like `01KBEDROOM...` and entity IDs like
`light.wo_shi_san_jian_kai_guan_*` were removed from the active registry, while
the `Identify` button was disabled.

Kitchen switch mapping follows the same physical-control rule:

- `switch.wall_switch_switch1_2` is the physical `厨房开关左键`.
- `switch.wall_switch_switch2_2` is the physical `厨房开关右键`.
- `light.wall_switch_switch1_2` is the semantic virtual `厨房顶灯`.
- `light.yeelink_cn_581782069_vf3_s_3_light` is the Xiaomi `厨房凉霸灯`.

The kitchen right key is not modeled as a light. It remains a physical switch
key and automation `1770000400000` / `厨房右键切换凉霸灯` toggles the Liangba
light when the right-key switch state changes between `on` and `off`.

The kitchen motion automation `1731500393158` / `厨房动作灯光联动` should target
`light.yeelink_cn_581782069_vf3_s_3_light`, not the virtual kitchen ceiling
light. The user explicitly wanted the occupied-kitchen automation to operate
the Liangba light.

Kitchen automatic-light state is tracked separately from entryway automatic
light state:

- `input_boolean.xuan_guan_auto_light_active`: entryway automation helper
- `input_boolean.chu_fang_auto_light_active`: kitchen automation helper

Do not reuse the entryway helper in kitchen automations. Cross-room helper
reuse can make a restart cleanup automation turn off the wrong room. The
kitchen motion automation should turn `input_boolean.chu_fang_auto_light_active`
on before turning on the Liangba light, turn it off after the no-motion cleanup,
and rely on automation `1770000500000` / `重启后厨房凉霸灯防误亮` to clean up
only when that kitchen helper restored as `on`.

Known wall-switch display-name cleanups:

- living-room device `ab594805479294fe3c09a945be9d17f8` is `客厅三键开关`;
  physical keys are named `客厅开关左键`, `客厅开关中键`, and `客厅开关右键`.
- guest-bathroom device `9b7393d0df1d220a8978b146f9ce2f31` is
  `客卫墙面开关`; physical keys are named `客卫开关左键` and `客卫开关右键`.
- HomeKit `Identify` buttons for the living-room, kitchen, and guest-bathroom
  wall switches are disabled by user because they are maintenance controls, not
  daily user-facing controls.

## Entity Discovery Notes

For curtain and light work, use live registry plus state history rather than
names alone. Several HomeKit curtains currently share the same original name
`Curtain`, so the useful signals are:

- area from `core.area_registry`
- device metadata from `core.device_registry`
- entity IDs from `core.entity_registry`
- recent state history in `home-assistant_v2.db`
- user-provided intent, especially exclusions like "do not open the sheer"

Useful live inspection shape:

```sh
docker exec home-assistant python -c '<read /config/.storage registries and query /config/home-assistant_v2.db>'
```

Avoid broad registry rewrites for routine automations. Prefer YAML automation
edits when the desired behavior can be expressed there.

## Area And UI Naming

Use English internal IDs for areas and keep user-facing names in Chinese.

Current area ID pattern:

- `living_room`: `客厅`
- `bedroom`: `卧室`
- `kitchen`: `厨房`
- `entryway`: `玄关`
- `guest_bathroom`: `客卫`
- `main_bathroom`: `主卫`
- `closet`: `衣柜`
- `devices`: `设备`
- `virtual`: `虚拟`
- `home`: `鞍山新村`

Do not use pinyin area IDs such as `ke_ting`, `wo_shi`, or `yi_ju` for new
work. Keep entity IDs stable unless there is a specific migration plan, because
automations and history can depend on them.

For UI labels, prefer clear Chinese names. HomeKit imports often surface raw
names like `Curtain`, `Lightbulb`, `Wall Switch`, `Identify`, or
`Battery Sensor`; convert those display names to Chinese while preserving the
underlying entity ID.

Room assignment is based on the real physical location, not the integration
source or where the parent bridge happens to sit. Known examples:

- `light.lightbulb_9` is `衣柜吸顶灯` and belongs to `closet`.
- `cover.curtain_5` is `衣柜窗帘` and belongs to `closet`.
- `light.heater_lightbulb` is `主卫浴霸灯` and belongs to `main_bathroom`.
- The bedroom three-key switch belongs to `bedroom`, but its semantic light
  entities also need to be exposed as lights, not treated only as switch keys.

When room assignment is uncertain, inspect registry data and user-visible names,
then present a small suspect list instead of bulk-moving devices.

## Dashboard And Sidebar Reality

Treat Home Assistant frontend work as two different storage surfaces:

- custom dashboards:
  - `/config/.storage/lovelace`
  - `/config/.storage/lovelace.rooms`
  - `/config/.storage/lovelace.control`
  - `/config/.storage/lovelace_dashboards`
- profile-specific built-in panel visibility:
  - `/config/.storage/frontend.user_data_<user_id>`

Important distinction:

- `首页` and `总控` are custom Lovelace dashboards and belong in
  `lovelace*` storage.
- built-in routes such as `/energy`, `/media-browser`, `/todo`, and the legacy
  `/home` overview are not Lovelace dashboards.
- built-in sidebar visibility is controlled per profile through
  `frontend.user_data_*`, typically under:

```json
{
  "sidebar": {
    "hiddenPanels": ["energy", "media-browser", "todo"]
  }
}
```

Do not try to hide built-in panels by editing `lovelace_dashboards`; that only
affects custom dashboards.

Useful live pattern:

1. inspect the actual sidebar links in the browser
2. separate custom routes from built-in routes
3. edit the correct storage surface
4. reload or restart HA
5. verify the sidebar again in the live browser

In this home, the custom dashboards currently resolve as:

- `http://10.0.0.11:8123/rooms/home`
- `http://10.0.0.11:8123/control/control`

Do not assume the visible route will exactly match the storage id.

## Restart-Safe Automation Lessons

For lights that can be turned on by automation and only turned off after a
later wait, `mode: restart` is not enough. A full HA restart still kills the
in-flight wait and loses the cleanup step.

The entryway-light session produced two durable rules:

1. If an automation starts a delayed auto-light flow, mark that flow with a
   durable helper such as `input_boolean.xuan_guan_auto_light_active`.
2. Startup cleanup should delay first, then evaluate helper/light state after
   HA restore timing has settled.

The failure that mattered here was subtle:

- the startup cleanup automation did trigger on `homeassistant.start`
- but it checked conditions too early
- `trace.saved_traces` showed `failed_conditions` because the helper had
  restored to `off` at that moment

Better pattern:

- auto-light path:
  - set helper `on`
  - turn lights on
  - wait for normal stop condition
  - turn lights off
  - set helper `off`
- startup cleanup path:
  - trigger on `homeassistant.start`
  - `delay` long enough for restore
  - then check helper state and/or whether the target light is still `on`
  - only then perform cleanup

If the startup condition is evaluated before the delay, restored state timing
can still defeat the safeguard.

For this environment, the highest-signal evidence sources are:

- `/config/.storage/trace.saved_traces`
- `/config/.storage/core.restore_state`
- `/config/home-assistant_v2.db`

Use those before guessing why a restart safeguard failed.

## Common Pitfalls

- Do not assume "Chinese legal workday" means Monday to Friday.
- Do not assume the Workday integration knows weekend make-up workdays for the
  current year without checking.
- Do not infer curtain identity from `friendly_name` alone when multiple covers
  expose the same HomeKit name.
- Do not mix up built-in HA panels with custom Lovelace dashboards.
- Do not evaluate restart-cleanup conditions too early on HA startup.
- Do not restart Home Assistant without first running `check_config`.
- Do not log secrets or private host details beyond already-established local
  operational identifiers.

## Verification

For automation changes, verify all of the following:

- `check_config` exits with status `0`
- `docker ps --filter name=home-assistant` shows the container running after
  reload or restart
- `GET http://10.0.0.11:8123` returns `200`
- new or changed automation entities are present in the entity registry
- relevant condition sensors show the expected current state
- for dashboard/sidebar work, the live browser reflects the intended route set
- for restart-safe automation work, `trace.saved_traces` or recorder state
  history confirms the startup automation reached the expected branch

For the bedroom routine, also confirm the workday automation block contains:

```yaml
at: "06:00:00"
entity_id: binary_sensor.zhong_guo_fa_ding_gong_zuo_ri
```

After the switch/light modeling cleanup, the morning automation should use:

```yaml
action: light.turn_on
entity_id:
  - light.bedroom_left_bedside_light
  - light.bedroom_right_bedside_light
```

It should not use:

- `light.wo_shi_deng`
- `switch.wall_switch_switch1_5`
- `switch.wall_switch_switch3_2`
