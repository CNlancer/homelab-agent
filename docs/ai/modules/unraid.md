# Unraid

## Responsibility

This module owns SSH-backed execution against the Unraid host and Docker on that host.

Current action surface includes:

- `read_system_info`
- `list_containers`
- `configure_docker_registry_mirror`
- `configure_community_applications_proxy`
- `configure_docker_daemon_proxy`
- `install_boot_network_acceleration_hook`
- `configure_webui_proxy`
- `backup_boot_config_to_local`

## Main Files

- `src/homelab_agent/executors/unraid/adapter.py`
- `src/homelab_agent/executors/unraid/executor.py`
- `src/homelab_agent/config/loader.py`
- tests under `tests/executors/unraid/`
- design/planning notes in `docs/superpowers/specs/` and `docs/superpowers/plans/`

## Notes

- This is the richest operational surface in the repo right now.
- Changes here should preserve explicit rollback metadata and local audit context.
- The repo convention is to keep credentials local and gitignored, with `local/secrets/unraid.json` as the target profile entrypoint.

## Common Change Types

- adding new explicit Unraid host actions
- refining remote command construction
- improving backup, proxy, or rollback metadata
- tightening config/profile validation

## Verification

- `uv run pytest tests/executors/unraid -q`
- live host verification only when credentials are available and the change is intended for the real host
