# Core Runtime

## Responsibility

This module owns the generic execution flow:

- task parsing and validation
- target/action routing
- execution envelope assembly
- JSONL audit persistence
- config loading boundaries used by the bootstrap path

## Main Files

- `src/homelab_agent/cli.py`
- `src/homelab_agent/bootstrap.py`
- `src/homelab_agent/core/router.py`
- `src/homelab_agent/core/service.py`
- `src/homelab_agent/core/audit.py`
- `src/homelab_agent/config/loader.py`
- `src/homelab_agent/config/models.py`
- `src/homelab_agent/models/task.py`
- `src/homelab_agent/models/result.py`
- `src/homelab_agent/models/risk.py`

## Inputs And Outputs

- Input: CLI flags that become `TaskSpec`
- Input: local secret-backed target config, especially `local/secrets/unraid.json`
- Output: `ExecutionResult`
- Output: audit records in `var/audit.jsonl`

## Invariants

- The core layer should stay target-agnostic.
- Action registration belongs in `bootstrap.build_router()`.
- Every successful execution should flow through `AuditLogger.record(...)`.
- Risk and confirmation semantics should stay explicit in task data, not hidden in executor internals.

## Common Change Types

- adding a new action registration
- tightening task validation
- extending audit payloads
- changing how config profiles are loaded

## Verification

- `uv run pytest tests/test_cli.py tests/test_cli_smoke.py -q`
- broader executor tests if the router contract changes
