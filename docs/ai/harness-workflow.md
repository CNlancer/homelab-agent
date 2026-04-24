# Harness Workflow

This repository is intended to work well with many short, targeted agent sessions instead of a few giant context-heavy sessions.

## Preferred Session Types

### 1. Project-init session

Use for:

- setting up docs,
- clarifying module boundaries,
- shaping the roadmap,
- creating templates and collaboration rules.

### 2. Module session

Use for:

- one subsystem,
- one bug cluster,
- one integration boundary.

### 3. Roadmap-item session

Use for:

- one concrete next task from `docs/roadmap.md`.

## Recommended Read Budget

Before editing:

1. `AGENTS.md`
2. `docs/roadmap.md`
3. one or two matching module docs
4. `docs/architecture.md` when the task changes execution flow or safety boundaries

Only add:

- a relevant spec,
- a relevant plan,
- a handoff note if the task depends on recent unfinished work.

## Preferred Module Boundaries

- `core-runtime`: task model, router, service, audit, config loading
- `local-docker`: local Docker actions and macOS runtime bootstrap
- `unraid`: SSH adapter, Docker-on-Unraid actions, backup/proxy flows
- `mikrotik`: read-only router inspection until explicitly expanded
- `operations-docs`: runbooks, handoffs, and operator-facing procedure notes

Keep changes inside one boundary unless the task is explicitly about integration across boundaries.

## Safety Bias

- Default to read-first and dry-run-friendly changes.
- Preserve auditable outputs for any remote or configuration-changing action.
- If a session changes behavior on an external host, update both the code path and the operator docs that explain how to verify or roll it back.

## Recommended Write-Back

At the end of a meaningful task, update:

- the relevant module doc,
- `docs/roadmap.md`,
- `docs/operations/session-handoff.md` if future sessions need the nuance.

If adopting or refining the shared harness approach exposes a missing pattern, record it here and consider filing a GitHub issue back to `Team-Cyan/harness-agent-kit`.
