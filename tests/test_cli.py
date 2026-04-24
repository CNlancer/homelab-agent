import json

from homelab_agent.cli import build_parser, task_from_args
from homelab_agent.models.risk import RiskLevel


def test_task_from_args_builds_task_spec():
    parser = build_parser()
    args = parser.parse_args(
        [
            "--target-type",
            "local_docker",
            "--target-name",
            "local",
            "--action",
            "list_containers",
            "--arguments",
            '{"all_containers": true}',
            "--risk-level",
            "safe_read",
        ]
    )

    task = task_from_args(args)

    assert task.target_type == "local_docker"
    assert task.target_name == "local"
    assert task.action == "list_containers"
    assert task.arguments == {"all_containers": True}
    assert task.risk_level == RiskLevel.SAFE_READ
    assert task.confirmation_required is False


def test_task_from_args_handles_confirmation_flag():
    parser = build_parser()
    args = parser.parse_args(
        [
            "--target-type",
            "local_docker",
            "--target-name",
            "local",
            "--action",
            "restart_container",
            "--arguments",
            json.dumps({"name": "jellyfin"}),
            "--risk-level",
            "safe_write",
            "--confirm",
        ]
    )

    task = task_from_args(args)

    assert task.risk_level == RiskLevel.SAFE_WRITE
    assert task.confirmation_required is True
