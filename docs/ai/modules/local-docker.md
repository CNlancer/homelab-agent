# Local Docker

## Responsibility

This module owns local Docker actions on the development machine.

Current actions include:

- `list_containers`
- `restart_container`
- `bootstrap_runtime`
- `deploy_home_assistant`

## Main Files

- `src/homelab_agent/executors/local_docker/adapter.py`
- `src/homelab_agent/executors/local_docker/executor.py`
- tests under `tests/executors/local_docker/`

## Notes

- The user preference on macOS is a lighter CLI-first Docker workflow, historically biased toward Colima or similar lightweight runtimes.
- Keep this executor focused on explicit actions, not arbitrary shell wrappers.
- If a local action changes Docker or service settings, the audit and operator docs should make rollback legible.
- Do not transfer local Docker habits directly to Unraid DockerMan-managed
  containers. Local `docker rm && docker run` rebuilds are fine for disposable
  local runtimes, but on Unraid they can detach a container from its template and
  break update-status visibility.

## Common Change Types

- adding a local safe-read action
- adding a narrowly scoped safe-write action
- improving runtime bootstrap or Home Assistant deployment flows
- refining argument validation for container-scoped actions

## Verification

- targeted executor tests for local Docker
- live `docker ps` or equivalent only when needed and safe for the current machine state
