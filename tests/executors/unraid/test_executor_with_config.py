from homelab_agent.config.models import TargetConfig
from homelab_agent.executors.unraid.executor import UnraidExecutor


class StubSshAdapter:
    def __init__(self) -> None:
        self.calls = []

    def read_system_info(self, config: TargetConfig) -> dict:
        self.calls.append(("read_system_info", config.label, config.ssh_host, config.ssh_username))
        return {"hostname": "tower", "kernel": "Linux"}

    def list_containers(self, config: TargetConfig, all_containers: bool = False) -> list[dict]:
        self.calls.append(("list_containers", config.label, all_containers))
        return [{"name": "jellyfin", "state": "running"}]


def test_executor_uses_loaded_target_config_for_system_info():
    adapter = StubSshAdapter()
    config = TargetConfig(
        label="unraid-tower",
        ssh_host="10.0.0.11",
        ssh_username="root",
        ssh_password="secret",
    )
    executor = UnraidExecutor(adapter=adapter, target_configs={"unraid-tower": config})

    payload = executor.run("read_system_info", target_name="unraid-tower", arguments={})

    assert adapter.calls == [("read_system_info", "unraid-tower", "10.0.0.11", "root")]
    assert payload["system_info"]["hostname"] == "tower"


def test_executor_uses_loaded_target_config_for_container_listing():
    adapter = StubSshAdapter()
    config = TargetConfig(
        label="unraid-tower",
        ssh_host="10.0.0.11",
        ssh_username="root",
        ssh_password="secret",
    )
    executor = UnraidExecutor(adapter=adapter, target_configs={"unraid-tower": config})

    payload = executor.run("list_containers", target_name="unraid-tower", arguments={"all_containers": True})

    assert adapter.calls == [("list_containers", "unraid-tower", True)]
    assert payload["containers"] == [{"name": "jellyfin", "state": "running"}]
