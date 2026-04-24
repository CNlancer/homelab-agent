from homelab_agent.core.router import ActionRouter
from homelab_agent.models.risk import RiskLevel
from homelab_agent.models.task import TaskSpec


def test_router_returns_registered_executor_and_action():
    router = ActionRouter()
    task = TaskSpec(
        target_type="local_docker",
        target_name="local",
        action="list_containers",
        arguments={},
        risk_level=RiskLevel.SAFE_READ,
        confirmation_required=False,
    )

    def execute(task: TaskSpec) -> dict:
        return {"ok": True, "arguments": task.arguments, "target_name": task.target_name}

    router.register("local_docker", "list_containers", execute)

    registered_action = router.resolve(task)

    assert registered_action.executor_name == "local_docker"
    assert registered_action.action_name == "list_containers"
    assert registered_action.handler(task) == {"ok": True, "arguments": {}, "target_name": "local"}


def test_router_rejects_unregistered_action():
    router = ActionRouter()
    task = TaskSpec(
        target_type="mikrotik",
        target_name="edge-router",
        action="show_interfaces",
        arguments={},
        risk_level=RiskLevel.SAFE_READ,
        confirmation_required=False,
    )

    try:
        router.resolve(task)
    except KeyError as error:
        assert "mikrotik.show_interfaces" in str(error)
    else:
        raise AssertionError("expected missing action to raise KeyError")
