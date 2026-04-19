# Homelab Agent Instructions

## Project Positioning

This repository is a Codex-facing execution toolkit for homelab operations.

Do not treat this project as:

- a UI application
- a dashboard
- a monitoring platform
- a generic autonomous terminal agent

Treat it as:

- a structured action runner
- a target router
- a safety boundary for infrastructure operations

## Primary Use Case

The normal interaction model is:

1. The user gives Codex an instruction in this repository
2. Codex decides whether the request maps to a supported structured action
3. Codex calls repository code to execute that action
4. The repository records the action, result, and risk metadata

## Supported Targets

The current target set is:

- local Docker on the development machine
- Unraid over SSH
- Docker on the Unraid host
- MikroTik over SSH

## Architectural Rules

- Keep the core layer generic and small
- Put target-specific behavior inside executors
- Prefer structured actions over free-form commands
- Do not expose unrestricted shell execution to the model
- Require explicit confirmation for risky actions
- Preserve a complete audit trail for every execution

## Operational Change Logging

When this repository changes settings on another service, host, or device, it
must write a local audit record before the turn is considered complete.

This applies to changes such as:

- Unraid boot, Docker, Community Applications, plugin, or template settings
- Docker daemon, registry, proxy, network, or container runtime settings
- Surge, router, MikroTik, DNS, proxy, or routing settings
- Any other external service configuration changed through this repository

The record should be machine-readable and stored locally under `var/`, normally
in `var/audit.jsonl` for structured repo actions. If a one-off manual operation
is unavoidable, append a sanitized JSONL entry under `var/ops-log.jsonl`.

Each record must include:

- timestamp
- target service or host
- structured action name or manual operation name
- exact setting paths or files changed
- old value summary, when safe to record
- new value summary, when safe to record
- backup path, snapshot id, or rollback instruction
- verification command or observed result
- whether confirmation was required and received

Do not store credentials, tokens, passwords, private keys, or sensitive proxy
secrets in logs. Redact secrets while preserving enough context to repair or
roll back the change after conversation context is lost.

## Safety Rules

- Default to read-only actions when adding new target capabilities
- Model high-risk changes explicitly instead of hiding them in generic command helpers
- Keep credentials out of prompts, logs, and returned results
- Require host allowlists for SSH targets
- Add timeouts for all external operations

## Implementation Priorities

Build in this order unless there is a strong reason not to:

1. models
2. core router and audit logging
3. local Docker executor
4. Unraid SSH executor
5. Unraid Docker actions
6. MikroTik SSH executor

## Testing Expectations

- Unit test task routing and risk evaluation
- Unit test action argument validation
- Mock SSH and Docker clients in most tests
- Keep live integration tests opt-in and clearly separated

## Non-Goals For V1

- browser automation
- background jobs
- dashboards
- multi-user auth
- broad plugin ecosystems
