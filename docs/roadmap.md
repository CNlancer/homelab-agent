# Roadmap

## Completed

- Core task model, router, execution service, and JSONL audit logging
- Local Docker executor with container listing, restart, runtime bootstrap, and Home Assistant deployment hooks
- Unraid SSH executor with system info, container listing, proxy acceleration helpers, web UI proxy support, and boot config backup export
- Early MikroTik executor for read-only inspection actions
- Thin root `AGENTS.md`, `.agents/`, and `CLAUDE.md` routing into the `docs/` knowledge base
- Shared harness kit bootstrap under `docs/ai/`
- First-pass module docs for core runtime, local Docker, Unraid, and MikroTik
- Expanded Home Assistant AI docs for frontend dashboard/sidebar storage,
  restart-safe automation timing, and recorder/trace-based debugging
- Reviewed the live HA config after the bedroom/kitchen automation cleanup and
  recorded the current switch, helper, and restart-safety rules

## In Progress

- Keep Unraid operational docs and code paths in sync as new actions land
- Tighten `docs/ai/` so future sessions can stay narrow without rediscovering safety assumptions
- Keep Home Assistant live-ops knowledge current as dashboard, sidebar, and
  automation patterns evolve

## Next

- Normalize older `docs/superpowers/` planning material into `docs/specs/` and `docs/plans/`
- Add stronger integration notes for local Docker plus Unraid live verification workflows

## Later

- Expand MikroTik beyond read-only inspection once the write-safety model is mature
- Add more operator runbooks for backups, rollback, and post-change verification
- Tighten config documentation for local secrets, SSH migration, and target allowlists
- Add module-owned plans for major executor families if the repo starts spanning many parallel sessions

## Deferred Or Not In Scope

- Dashboard or web UI control plane
- Background monitoring platform
- Arbitrary shell passthrough exposed directly to the model
- Broad plugin ecosystem before the core action model is stable
