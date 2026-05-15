# AGENTS.md

This file is the repository entrypoint for coding agents.

Keep this file short. Treat it as a table of contents, not the full knowledge base.

## Read Order

For most tasks, read in this order:

1. `docs/ai/project-overview.md`
2. `docs/roadmap.md`
3. The smallest relevant file under `docs/ai/modules/`
4. `docs/operations/session-handoff.md` only if the task depends on recent unfinished work
5. `docs/architecture.md` only when the task needs the broader code structure

Do not start by reading every module doc or every operations note.

## Repository Model

- `AGENTS.md`: thin agent entrypoint
- `.agents/`: repo-local agent assets and reusable prompts
- `docs/ai/`: reusable AI knowledge base
- `docs/roadmap.md`: current repository state and next work
- `docs/operations/`: operator workflows and handoff notes
- `docs/`: human-facing architecture and runbook material

## Working Rules

- Keep AI-facing docs in English.
- Reply to the human user in their preferred language.
- Prefer small, well-bounded sessions.
- Keep `.agents/` thin; keep durable knowledge in `docs/`.
- Preserve the controlled-action model instead of inventing unrestricted shell behavior.
- Update the most relevant doc when the safe operating model materially changes.

## Safety

- Keep secrets in gitignored local files such as `local/secrets/`.
- Do not commit credentials, tokens, or cookies.
- Record external configuration changes under `var/` with enough rollback context to repair them later.
- Prefer dry-run or read-only defaults for destructive or external side-effect operations.

## Project-Specific Notes

- This repo is a structured action runner, not a dashboard or a general autonomous shell agent.
- Target-specific behavior belongs in executors; keep the core router and audit surfaces generic.
- High-risk actions must remain explicit and confirmation-aware.

## Useful Docs

- `docs/README.md`
- `docs/ai/project-overview.md`
- `.agents/README.md`
- `docs/ai/harness-workflow.md`
- `docs/ai/reference-repos.md`
- `docs/ai/modules/*.md`
- `docs/roadmap.md`
- `docs/operations/session-handoff.md`
- `docs/architecture.md`
