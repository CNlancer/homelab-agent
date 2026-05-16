# Home Assistant Area Governance And Xiaomi Dedupe

## Summary

This note captures the durable lessons from a Home Assistant cleanup pass on the
Unraid-hosted HA instance at `10.0.0.11`.

The work covered four related topics:

- assigning HA entities and devices to real rooms
- separating physical rooms from non-room/system buckets
- removing stale Google Cast residue
- deduplicating Xiaomi Home entities without deleting real functionality

## Area Governance Rules

### 1. Distinguish real rooms from support buckets

For this host, the room model should not collapse everything into `虚拟`.

Use these buckets deliberately:

- real physical rooms: `客厅`, `卧室`, `厨房`, `玄关`, `客卫`, `主卫`, `衣柜`
- support/device bucket: `设备`
- non-physical/system bucket: `虚拟`
- location/home name bucket: `鞍山新村`

Recommended policy:

- phones and tablets go to `设备`
- fixed computers go to their real room
- HA bridges, service integrations, forecast, sun, Bluetooth adapters, and
  similar system objects go to `虚拟`
- do not abuse `虚拟` as a default for everything uncertain

### 2. Room light groups need their own `area_id`

The grouped room lights were materially better after assigning explicit areas:

- `light.ke_ting_deng` -> `客厅`
- `light.wo_shi_deng` -> `卧室`
- `light.xuan_guan_deng` -> `玄关`
- `light.chu_fang_deng` -> `厨房`
- `light.ke_wei_deng` -> `客卫`
- `light.zhu_wei_deng` -> `主卫`
- `light.quan_wu_deng` -> `虚拟`

Without this, Apple Home and room-aware views can treat them as floating or
misplace them.

### 3. Area primary temperature/humidity should only be filled when the sensor is real

Do not force `temperature_entity_id` or `humidity_entity_id` for every room.

Good rule:

- assign them when a room has a credible primary sensor
- leave them `null` when the room has no proper candidate

For this host:

- `客厅` and `卧室` use Qingping Air Monitor Lite sensors
- `主卫` and `客卫` use Xiaomi temperature/humidity meters
- `衣柜` has temperature only
- `厨房` and `玄关` currently stay empty because there is no trustworthy room
  sensor to assign

## Cast Cleanup Rules

### 1. `always unavailable` plus no meaningful references is enough to remove stale cast residue

The removed residue was:

- one `cast` config entry
- three dead devices
- three `media_player.*` entities

The safe-removal signals were:

- recent state history showed only `unavailable`
- no useful references from automation or room/group config
- the user explicitly said those devices were no longer used

### 2. Remove all three layers together

For stale Cast cleanup, do not only remove the config entry.

Also clean:

- `core.config_entries`
- `core.device_registry`
- `core.entity_registry`

That avoids leaving dead room clutter behind.

## Xiaomi Dedupe Rules

### 1. Light duplicates often come in raw-vs-translated pairs

For this host, the clearest safe dedupe class was Xiaomi lights where both of
these existed:

- a raw imported entity such as `light.xiaomi_cn_...`
- a translated or better-presented companion such as
  `light.xiaomi_cn_..._indicator_light`, `..._night_light`, or `..._light`

Safe policy:

- keep the translated human-facing entity
- disable the raw duplicate with `disabled_by=user`

### 2. Not every ugly Xiaomi entity is a duplicate

A large number of non-light Xiaomi entities are **not** duplicates. They are
single-instance advanced controls or telemetry, for example:

- TV remote buttons
- toilet feature triggers
- air-conditioner maintenance and developer-mode switches
- router events and throughput sensors
- drying rack position controls

These should be handled as **noise reduction**, not duplicate removal.

Good rule:

- duplicate removal is for same-function parallel entities
- advanced-function cleanup is a separate pass focused on hide/disable policy

### 3. Prefer disabling over deleting

When deduplicating Xiaomi entities, disable the noisier/raw entity instead of
deleting it outright.

Reason:

- lower rollback cost
- lower risk of breaking references unexpectedly
- easier to revisit later if a translated entity turns out to be incomplete

## Naming Rules

### 1. Rename device roots before polishing child entities

Readable device names make later room/entity review much easier.

Examples that helped on this host:

- `客厅空气传感器`
- `卧室空气传感器`
- `主卫温湿度计`
- `客卫温湿度计`
- `客厅空调`
- `客厅路由器`
- `卧室智能床`
- `卧室晾衣机`
- `卧室空调`
- `主卫马桶`
- `厨房凉霸`
- `客卫青空灯`
- `客卫马桶`
- `衣柜除湿机`

### 2. Rename room-facing sensors and visible light helpers

Examples:

- `sensor.air_monitor_lite_40b6_temperature` -> `客厅温度`
- `sensor.air_monitor_lite_3bdc_humidity` -> `卧室湿度`
- `light.xiaomi_cn_645757394_c36_s_6_indicator_light` -> `客厅空调指示灯`
- `light.zhimi_cn_681640604_pa5_s_4_night_light` -> `主卫马桶夜灯`

This is especially helpful for dashboards, entity pickers, and Apple Home
bridge curation.

## Practical Next-Step Guidance

After the duplicate light cleanup, the next reasonable Xiaomi pass is:

- keep daily-use controls and human-meaningful state
- hide or disable engineering-heavy `button`, `event`, `number`, and
  maintenance/developer entities that are unlikely to be used manually

Do this conservatively and treat it as UI-noise cleanup, not as structural
dedupe.
