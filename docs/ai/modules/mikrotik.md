# MikroTik

## Responsibility

This module owns the early MikroTik executor.

Current action surface is intentionally narrow:

- `show_interfaces`
- `show_routes`
- `export_firewall`

## Main Files

- `src/homelab_agent/executors/mikrotik/adapter.py`
- `src/homelab_agent/executors/mikrotik/executor.py`
- related router registration in `src/homelab_agent/bootstrap.py`

## Notes

- The user explicitly asked to leave router work for later compared with local Docker and Unraid.
- Treat this module as read-mostly until the write-safety and rollback model is stronger.
- New router actions should come with unusually clear audit and recovery notes.

## Common Change Types

- tightening read action parsing
- adding more inspection-only actions
- preparing write-action design without landing risky behavior yet

## Verification

- targeted executor tests
- live router verification only when the task explicitly needs it and the safety boundary is clear
