# Project Overview

## What This Project Is

- A repo-local execution toolkit for Codex to operate homelab targets through structured actions.
- A narrow safety boundary around local Docker, Unraid, and early MikroTik operations.
- A docs-first operational repo where action routing, audit logging, and target-specific executors are first-class.

## What It Is Not

- Not a dashboard or UI product.
- Not a general autonomous shell agent.
- Not a background monitoring platform.
- Not an unrestricted plugin system for arbitrary remote command execution.

## Core Runtime Surfaces

- CLI / app entrypoint: `uv run homelab-agent ...`
- config: `local/secrets/*.json` target profiles, especially `local/secrets/unraid.json`
- state: local backup artifacts under `var/`, plus any target-side config snapshots returned by actions
- audit: `var/audit.jsonl` for structured actions and `var/ops-log.jsonl` for sanitized one-off operator notes

## Current Architecture

- CLI parses a task into `TaskSpec`, then hands it to the core service.
- `bootstrap.build_router()` registers supported actions for `local_docker`, `unraid`, and `mikrotik`.
- `ExecutionService` resolves the action through `ActionRouter`, executes the registered handler, and persists an `ExecutionResult` through `AuditLogger`.
- Target-specific behavior lives in executors and adapters under `src/homelab_agent/executors/`.
- Unraid currently has the richest action surface, including read actions, proxy acceleration helpers, and local backup export.

## Documentation Strategy

- root `AGENTS.md` for entry routing
- `docs/ai/` for reusable knowledge
- `docs/roadmap.md` for current state
- `docs/specs/` for durable design decisions
- `docs/plans/` for implementation sequencing
- `docs/operations/` for operator procedures

## Current Module Map

- `docs/ai/modules/core-runtime.md`: router, service, audit, and task model
- `docs/ai/modules/local-docker.md`: local Docker executor and bootstrap actions
- `docs/ai/modules/unraid.md`: SSH-backed Unraid host and Docker actions
- `docs/ai/modules/mikrotik.md`: early MikroTik read-only surface

## Reference Backpressure

If this repo learns something while adopting the shared harness kit, record the lesson locally and consider filing a GitHub issue back to `Team-Cyan/harness-agent-kit` so the kit improves for the next repository.
