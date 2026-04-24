# Reference Repositories

These projects are references, not implementation templates.

## `Team-Cyan/harness-agent-kit`

- Source: `git@github.com:Team-Cyan/harness-agent-kit.git`
- Refer to for: root `AGENTS.md` shape, `docs/ai/` layout, session-handoff discipline, reusable repo-init templates
- Do not copy: placeholder wording without adapting it to real runtime and safety boundaries
- Useful when stuck on: how much AI-facing structure is enough for future narrow sessions

## `seed-agent`

- Source: `/Users/lancer/projects/seed-agent`
- Refer to for: docs-first harness structure, roadmap discipline, module docs, operations handoff style
- Do not copy: PT-specific domain assumptions, source-specific config or action semantics
- Useful when stuck on: how to keep a repo operationally agent-friendly without turning docs into a giant prompt dump

## OpenAI Harness Engineering Guidance

- Source: public OpenAI guidance referenced by `harness-agent-kit`
- Refer to for: thin `AGENTS.md`, structured docs as system of record, multi-session context minimization
- Do not copy: generic examples that ignore this repo's safety and audit requirements
- Useful when stuck on: deciding whether knowledge belongs in `AGENTS.md`, `docs/ai/`, specs, or operations docs

## Local Repository Docs

- Source: `README.md`, `AGENTS.md`, `CLAUDE.md`, `docs/architecture.md`
- Refer to for: actual repo behavior, supported targets, current operational constraints
- Do not copy: old assumptions into new docs without checking the current code path
- Useful when stuck on: reconciling template-level AI docs with the real repository surface
