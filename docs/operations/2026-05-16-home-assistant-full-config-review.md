# Home Assistant Full Config Review

This note records a full-config review of the Unraid-hosted Home Assistant
instance at `10.0.0.11`, using the entity and automation modeling rules learned
from the May 2026 bedroom, closet, bathroom, and kitchen cleanup sessions.

## Scope

Reviewed live config surfaces:

- `/config/configuration.yaml`
- `/config/automations.yaml`
- `/config/.storage/core.area_registry`
- `/config/.storage/core.device_registry`
- `/config/.storage/core.entity_registry`
- `/config/.storage/core.config_entries`
- latest state evidence from `/config/home-assistant_v2.db`

The review focused on:

- room and area IDs
- physical switch versus semantic light modeling
- bedroom and kitchen automation targets
- restart-safe automation cleanup
- raw HomeKit import names still visible in user-facing controls
- obvious stale entity references from active YAML

## Findings

### Kitchen motion automation reused the entryway helper

Before the review, `厨房动作灯光联动` used
`input_boolean.xuan_guan_auto_light_active` even though it now operates the
kitchen Liangba light.

Risk:

- the entryway restart cleanup could treat a kitchen automation as an entryway
  automation
- cross-room helper state made future debugging misleading

Fix:

- added `input_boolean.chu_fang_auto_light_active`
- changed `厨房动作灯光联动` to use the kitchen helper
- added `重启后厨房凉霸灯防误亮`
- the kitchen restart cleanup only turns off `厨房凉霸灯` when the kitchen helper
  restored as `on`

### Kitchen occupied-light target is now correct

`厨房动作灯光联动` now turns on and later turns off
`light.yeelink_cn_581782069_vf3_s_3_light`, the Xiaomi `厨房凉霸灯`.

It no longer targets `light.wall_switch_switch1_2`, the virtual kitchen ceiling
light.

### Kitchen right key stays a switch

`switch.wall_switch_switch2_2` remains the physical `厨房开关右键`.

Automation `1770000400000` / `厨房右键切换凉霸灯` toggles
`light.yeelink_cn_581782069_vf3_s_3_light` when the right-key switch state
changes between `on` and `off`.

This preserves the local modeling rule: physical switch keys stay `switch.*`,
semantic lights stay `light.*`.

### Wall-switch naming cleanup

Visible raw HomeKit switch names were removed for known wall switches:

- `客厅三键开关`
  - `switch.wall_switch_switch1`: `客厅开关左键`
  - `switch.wall_switch_switch2`: `客厅开关中键`
  - `switch.wall_switch_switch3`: `客厅开关右键`
- `客卫墙面开关`
  - `switch.wall_switch_switch1_3`: `客卫开关左键`
  - `switch.wall_switch_switch2_3`: `客卫开关右键`
- `厨房墙面开关`
  - `switch.wall_switch_switch1_2`: `厨房开关左键`
  - `switch.wall_switch_switch2_2`: `厨房开关右键`
  - `light.wall_switch_switch1_2`: `厨房顶灯`

HomeKit `Identify` buttons for these wall switches are disabled by user. They
are maintenance controls and were cluttering user-facing device pages.

### Area IDs are aligned

Current area IDs follow the English-internal, Chinese-display rule:

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

Kitchen and entryway still intentionally have no primary temperature or
humidity sensor assignments.

## Verification

After changes:

- Home Assistant `check_config` exited successfully
- `GET http://10.0.0.11:8123` returned `200`
- live automation `1731500393158` uses
  `input_boolean.chu_fang_auto_light_active` and
  `light.yeelink_cn_581782069_vf3_s_3_light`
- live automation `1770000500000` exists for kitchen restart cleanup
- live automation `1770000400000` still toggles the Liangba light from the
  kitchen right switch
- the known wall-switch devices and key entities have Chinese display names

Remote backup:

`/mnt/user/appdata/home-assistant/backups/homelab-agent-hass-review-refine-20260516_090127`

## Open Review Items

No obvious broken YAML entity references were found after excluding service
names such as `light.turn_on`, `cover.open_cover`, and
`input_boolean.turn_on`.

Future review can go deeper into advanced Xiaomi entities, but that should be a
separate UI-noise pass. Many ugly Xiaomi controls are unique maintenance or
diagnostic controls, not duplicates.
