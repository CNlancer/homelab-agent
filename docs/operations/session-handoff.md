# Session Handoff

## Repository State

- current branch: unknown from docs-only bootstrap; check local git state before assuming tracked history
- important recent commit: not recorded here yet because this repo currently shows many untracked files in the working tree

## Durable Knowledge Already Recorded

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/README.md`
- `docs/architecture.md`
- `docs/ai/project-overview.md`
- `docs/ai/harness-workflow.md`
- `docs/ai/reference-repos.md`

## Current Focus

This repo is already functional enough to route structured tasks to local Docker, Unraid, and early MikroTik executors. The immediate docs focus is to make future sessions cheaper: read a thin entrypoint, map the real module boundaries, and keep operational safety plus audit expectations visible without forcing every session to rediscover them from source.

## What Changed Recently

- Added `docs/ai/modules/home-assistant.md` after the live bedroom
  morning/evening automation work. It records the Unraid-hosted HA change
  pattern, the `binary_sensor.zhong_guo_fa_ding_gong_zuo_ri` legal-workday
  template sensor, 2026 make-up workday override maintenance, bedroom curtain
  entity choices, and verification steps.
- Reviewed the live HA config end to end after the kitchen Liangba switch work.
  The review split kitchen automatic-light state from the entryway helper,
  added a kitchen restart cleanup automation, and normalized known wall-switch
  display names. See
  `docs/operations/2026-05-16-home-assistant-full-config-review.md`.
- Bootstrapped shared harness docs into `docs/ai/`, `docs/roadmap.md`, and `docs/operations/session-handoff.md`
- Replaced placeholder template language with repo-specific overview, workflow, roadmap, and reference notes
- Added first-pass module docs for `core-runtime`, `local-docker`, `unraid`, and `mikrotik`
- Slimmed the root routing docs so `docs/` is the durable system of record
- This repo should feed improvements back into `Team-Cyan/harness-agent-kit` when adoption exposes missing patterns

## Recommended Next Task

- Review whether to migrate legacy `docs/superpowers/specs` and `docs/superpowers/plans` into the newer `docs/specs` and `docs/plans` layout
- Add or refresh the highest-value module docs before broadening the operational surface further
