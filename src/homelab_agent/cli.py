import argparse
import json
from pathlib import Path

from homelab_agent.bootstrap import build_router
from homelab_agent.core.audit import AuditLogger
from homelab_agent.core.service import ExecutionService
from homelab_agent.models.risk import RiskLevel
from homelab_agent.models.task import TaskSpec


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="homelab-agent")
    parser.add_argument("--target-type", required=True)
    parser.add_argument("--target-name", required=True)
    parser.add_argument("--action", required=True)
    parser.add_argument("--arguments", default="{}")
    parser.add_argument("--risk-level", required=True, choices=[level.value for level in RiskLevel])
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--audit-log", default="var/audit.jsonl")
    return parser


def task_from_args(args: argparse.Namespace) -> TaskSpec:
    return TaskSpec(
        target_type=args.target_type,
        target_name=args.target_name,
        action=args.action,
        arguments=json.loads(args.arguments),
        risk_level=RiskLevel(args.risk_level),
        confirmation_required=args.confirm,
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    task = task_from_args(args)
    service = ExecutionService(
        router=build_router(),
        audit_logger=AuditLogger(Path(args.audit_log)),
    )
    result = service.execute(task)
    print(result.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
