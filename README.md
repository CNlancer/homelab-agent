# Homelab Agent

`Homelab Agent` is a repo-local execution toolkit for Codex to operate local Docker and an Unraid host over SSH through controlled actions.

## What This Project Is

This repository is not a UI product, dashboard, or standalone chat agent.

It is a constrained execution layer that Codex can use from inside this repo:

- You give Codex an instruction in this repository
- Codex maps that request to a structured action
- The repository executes the action through a target-specific executor
- The repository returns a structured result and records an audit trail

## Initial Scope

The current implementation focuses on two target types:

- Local Docker on this machine
- Unraid over SSH

There is an early MikroTik skeleton in the repository, but it is not the current priority.

For local Docker on macOS, the intended backend is `docker CLI` against a lightweight runtime such as `Colima`.

Version 1 explicitly does not include:

- Web UI automation
- A web dashboard
- Background monitoring
- Arbitrary shell execution generated directly by the model

## Design Principles

- Controlled actions only: the model should call registered actions, not invent raw commands
- SSH where appropriate: Unraid and MikroTik are accessed primarily through SSH-backed executors
- Safety first: destructive or high-risk actions require confirmation
- Audit everything: every execution should leave a structured record
- Keep the core generic: system-specific behavior belongs in executors, not in the routing layer

## Proposed Architecture

```text
homelab-agent/
  README.md
  CLAUDE.md
  docs/
    architecture.md
  src/homelab_agent/
    cli.py
    core/
      router.py
      executor.py
      confirmations.py
      audit.py
      credentials.py
    models/
      task.py
      target.py
      result.py
      risk.py
    executors/
      local_docker/
        executor.py
        actions.py
      unraid/
        executor.py
        ssh_client.py
        host_actions.py
        docker_actions.py
      mikrotik/
        executor.py
        ssh_client.py
        actions.py
  tests/
```

## Execution Model

The intended runtime flow is:

1. Codex receives a user instruction in this repo
2. Codex converts that request into a structured task
3. The core router selects a target and action
4. Risk rules determine whether confirmation is required
5. The executor performs the action
6. The system returns a structured result and writes an audit record

## Example Actions

Examples of actions that fit this model today:

- `local_docker.list_containers`
- `local_docker.restart_container`
- `unraid.read_system_info`
- `unraid.list_containers`

High-risk actions should be modeled separately and marked as confirmation-required.

## Why This Exists

General-purpose agent runtimes are broader than needed for this use case. This repository is intended to stay narrow:

- predictable execution
- explicit target support
- auditable behavior
- low operational complexity

## Development

This repository uses `uv` for environment and package management.

Common commands:

```bash
uv sync
uv run pytest
uv run homelab-agent --target-type local_docker --target-name local --action list_containers --risk-level safe_read
```

Local Docker development on macOS is expected to work with:

```bash
brew install docker
brew install --cask orbstack
orb start
docker context use orbstack
docker ps
```

Add dependencies with:

```bash
uv add pydantic
uv add --dev pytest
```

Example invocation:

```bash
uv run homelab-agent \
  --target-type local_docker \
  --target-name local \
  --action restart_container \
  --arguments '{"name":"jellyfin"}' \
  --risk-level safe_write \
  --confirm
```

Unraid uses a local profile file under `local/secrets/`.

Example `local/secrets/unraid.json`:

```json
{
  "label": "unraid",
  "base_url": "http://10.0.0.11/",
  "ssh_host": "10.0.0.11",
  "ssh_username": "root",
  "ssh_password": "replace-me"
}
```

Example Unraid invocations:

```bash
uv run homelab-agent \
  --target-type unraid \
  --target-name unraid \
  --action read_system_info \
  --risk-level safe_read
```

```bash
uv run homelab-agent \
  --target-type unraid \
  --target-name unraid \
  --action list_containers \
  --arguments '{"all_containers": true}' \
  --risk-level safe_read
```

`target-name` for Unraid is the local profile name, not the raw SSH host.

## Backup Workflow (Mac-Centric)

For long-term maintainability (including future router backups), backup
orchestration should run on the Mac, not on Unraid cron.

Manual Unraid boot config backup to local:

```bash
uv run homelab-agent \
  --target-type unraid \
  --target-name unraid \
  --action backup_boot_config_to_local \
  --arguments '{"local_backup_root":"var/backups/unraid"}' \
  --risk-level safe_read
```

Convenience runner:

```bash
commands/backups/run-unraid-backup.sh
```

Install daily launchd schedule on macOS (03:20 every day):

```bash
commands/backups/install-daily-backup-launchd.sh
```

Remove schedule:

```bash
commands/backups/uninstall-daily-backup-launchd.sh
```

## Troubleshooting Notes

- [Unraid Docker update check troubleshooting](docs/operations/2026-04-24-unraid-docker-update-check-troubleshooting.md)
- [Home Assistant restart-triggered light false positives](docs/operations/2026-04-24-home-assistant-restart-light-false-positives.md)

- [Unraid Docker update check troubleshooting](/Users/lancer/projects/homelab-agent/docs/operations/2026-04-24-unraid-docker-update-check-troubleshooting.md)
