from pathlib import Path

from homelab_agent.core.audit import AuditLogger
from homelab_agent.core.router import ActionRouter
from homelab_agent.core.service import ExecutionService
from homelab_agent.models.risk import RiskLevel
from homelab_agent.models.task import TaskSpec


def test_execution_service_returns_standard_result_and_writes_audit(tmp_path: Path):
    router = ActionRouter()
    audit_logger = AuditLogger(tmp_path / "audit.jsonl")
    service = ExecutionService(router=router, audit_logger=audit_logger)
    task = TaskSpec(
        target_type="local_docker",
        target_name="local",
        action="list_containers",
        arguments={"all_containers": True},
        risk_level=RiskLevel.SAFE_READ,
        confirmation_required=False,
    )

    router.register(
        "local_docker",
        "list_containers",
        lambda task: {"containers": [{"name": "jellyfin"}], "arguments": task.arguments},
    )

    result = service.execute(task)

    assert result.target_type == "local_docker"
    assert result.target_name == "local"
    assert result.action == "list_containers"
    assert result.success is True
    assert result.summary == "local_docker.list_containers completed successfully"
    assert result.output == {
        "containers": [{"name": "jellyfin"}],
        "arguments": {"all_containers": True},
    }
    assert "list_containers" in (tmp_path / "audit.jsonl").read_text()
