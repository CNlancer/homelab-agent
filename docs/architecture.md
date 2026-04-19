# Homelab Agent Architecture Brief

## Summary

`Homelab Agent` is a repo-local infrastructure execution layer for Codex. It accepts structured tasks and executes them against a narrow set of supported homelab targets through controlled executors.

The first version is intentionally narrow:

- local Docker
- Unraid host access over SSH
- Docker management on Unraid
- MikroTik access over SSH

## Core Thesis

The core problem is not "build a general-purpose agent."

The core problem is "provide Codex with a safe, auditable, structured way to perform homelab operations."

That leads to four design decisions:

- execution is action-based, not prompt-to-shell
- target support is explicit
- dangerous operations are visible and gated
- auditability is a first-class output

## Main Components

### Core

The core layer owns:

- task parsing and validation
- target routing
- risk classification
- confirmation flow
- execution envelopes
- audit logging

The core layer does not know target-specific command syntax.

### Executors

Each executor owns one target family:

- `local_docker`
- `unraid`
- `mikrotik`

Each executor exposes a small registered action surface. Executors are responsible for translating action requests into concrete API calls, Docker SDK operations, or SSH command invocations.

### Adapters

Adapters isolate low-level transport details:

- local Docker adapter
- SSH adapter
- target-specific CLI helpers

This keeps executors focused on action semantics instead of connection plumbing.

## Task Model

Each execution request should resolve to a structured task with fields equivalent to:

- `target_type`
- `target_name`
- `action`
- `arguments`
- `risk_level`
- `confirmation_required`

The model layer should reject malformed or unsupported action requests before execution begins.

## Risk Model

Suggested initial risk levels:

- `safe_read`
- `safe_write`
- `high_risk`
- `blocked`

Examples:

- listing containers: `safe_read`
- restarting one known container: `safe_write`
- deleting a container or changing router firewall rules: `high_risk`
- arbitrary command passthrough: `blocked`

## Audit Model

Every execution should record:

- timestamp
- target
- action
- arguments summary
- executor used
- risk level
- confirmation status
- success or failure
- sanitized stdout and stderr summary

The audit log should be machine-readable.

For operations that change settings on another service, host, or device, the
audit trail must also preserve enough local state to recover after conversation
context is lost:

- exact setting paths or files changed
- old value summary, when safe to record
- new value summary, when safe to record
- backup path, snapshot id, or rollback instruction
- verification command or observed result

Structured repository actions should write these records to `var/audit.jsonl`.
If a one-off manual operation is unavoidable, it should append a sanitized JSONL
entry to `var/ops-log.jsonl`. Logs must never contain credentials, tokens,
passwords, private keys, or sensitive proxy secrets.

## Why No UI

This project assumes the user is already working inside the repository with Codex. A separate UI would add complexity without improving the core workflow.

The correct control loop is:

- user asks Codex
- Codex selects a structured action
- the repository executes it

## Why No Arbitrary SSH Tool

Raw shell freedom would blur the safety boundary and make auditing weak. The repository should expose clear actions instead:

- good: `restart_container(name="jellyfin")`
- bad: `ssh unraid "whatever command seems right"`

This design is stricter, but that is the point.

## Delivery Order

1. Define models and risk policy
2. Implement audit logging and the router
3. Ship local Docker support
4. Ship Unraid host and Unraid Docker support
5. Ship MikroTik read actions
6. Add carefully-scoped write actions
