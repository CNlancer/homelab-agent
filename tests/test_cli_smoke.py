from pathlib import Path

from homelab_agent.cli import build_parser, task_from_args


def test_cli_smoke_for_unraid_profile_name():
    parser = build_parser()
    args = parser.parse_args(
        [
            "--target-type",
            "unraid",
            "--target-name",
            "unraid",
            "--action",
            "list_containers",
            "--arguments",
            '{"all_containers": true}',
            "--risk-level",
            "safe_read",
            "--audit-log",
            str(Path("var") / "audit.jsonl"),
        ]
    )

    task = task_from_args(args)

    assert task.target_type == "unraid"
    assert task.target_name == "unraid"
    assert task.action == "list_containers"
    assert task.arguments == {"all_containers": True}
