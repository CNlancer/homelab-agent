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
- Template-managed Docker containers on Unraid should remain DockerMan-managed.
  Do not repair or update them with ad hoc `docker rm && docker run` commands
  unless the user explicitly wants to abandon template management. Manual
  recreation can remove the metadata that lets the Unraid UI show normal update
  state.
- For DockerMan-managed containers, prefer Unraid's own script when a CLI repair
  is needed:

```sh
/usr/local/emhttp/plugins/dynamix.docker.manager/scripts/update_container <name>
```

- After a repair, verify `net.unraid.docker.managed=dockerman`, container
  health, and the image/version labels. The live `seed-agent` repair used this
  path to restore DockerMan management after an accidental manual recreate.
- If SSH password auth is needed from a script, avoid letting local SSH keys
  exhaust authentication attempts. Use explicit password-only SSH options such
  as `PreferredAuthentications=password` and `PubkeyAuthentication=no` with the
  repo's askpass pattern.
- Clean up Docker image residue narrowly. Removing unused
  `ghcr.io/team-cyan/seed-agent:<none>` images is acceptable when that exact
  repository is the target, but avoid broad `docker system prune` operations on
  the NAS host.
- When another repo has already pushed a new container image and the user says
  they will update Unraid themselves, stop at the repo/GitHub boundary. Do not
  SSH into Unraid or click DockerMan updates on their behalf.
- For seed-agent style NAS services, separate three concerns in future sessions:
  code changes and Git push in the app repo, Docker image publishing by CI, and
  Unraid template update by the operator or an explicitly authorized Unraid
  action.

## Common Change Types

- adding new explicit Unraid host actions
- refining remote command construction
- improving backup, proxy, or rollback metadata
- tightening config/profile validation

## Verification

- `uv run pytest tests/executors/unraid -q`
- live host verification only when credentials are available and the change is intended for the real host
