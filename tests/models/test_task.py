import pytest
from pydantic import ValidationError

from homelab_agent.models.risk import RiskLevel
from homelab_agent.models.task import TaskSpec


def test_task_spec_accepts_supported_fields():
    task = TaskSpec(
        target_type="unraid_docker",
        target_name="tower",
        action="restart_container",
        arguments={"name": "jellyfin"},
        risk_level=RiskLevel.SAFE_WRITE,
        confirmation_required=True,
    )

    assert task.target_type == "unraid_docker"
    assert task.arguments == {"name": "jellyfin"}
    assert task.confirmation_required is True


def test_task_spec_rejects_empty_action():
    with pytest.raises(ValidationError):
        TaskSpec(
            target_type="unraid",
            target_name="tower",
            action="",
            arguments={},
            risk_level=RiskLevel.SAFE_READ,
            confirmation_required=False,
        )
