import pytest

from homelab_agent.executors.local_docker.executor import LocalDockerExecutor


class StubDockerAdapter:
    def __init__(self) -> None:
        self.calls = []

    def list_containers(self, all_containers: bool = False) -> list[dict]:
        self.calls.append(("list_containers", all_containers))
        return [{"name": "jellyfin", "state": "running"}]

    def restart_container(self, name: str) -> dict:
        self.calls.append(("restart_container", name))
        return {"name": name, "result": name}

    def ensure_runtime(self) -> dict:
        self.calls.append(("ensure_runtime",))
        return {"runtime": "orbstack", "docker_context": "orbstack"}

    def ensure_home_assistant(
        self,
        *,
        config_dir,
        timezone: str,
        port: int,
        container_name: str,
        image: str,
    ) -> dict:
        self.calls.append(
            (
                "ensure_home_assistant",
                str(config_dir),
                timezone,
                port,
                container_name,
                image,
            )
        )
        return {
            "name": container_name,
            "image": image,
            "config_dir": str(config_dir),
            "port": port,
            "status": "created",
            "result": "container-id",
        }


def test_executor_exposes_list_containers_action():
    adapter = StubDockerAdapter()
    executor = LocalDockerExecutor(adapter=adapter)

    result = executor.run("list_containers", {"all_containers": True})

    assert adapter.calls == [("list_containers", True)]
    assert result == {
        "target_type": "local_docker",
        "action": "list_containers",
        "containers": [{"name": "jellyfin", "state": "running"}],
    }


def test_executor_exposes_restart_container_action():
    adapter = StubDockerAdapter()
    executor = LocalDockerExecutor(adapter=adapter)

    result = executor.run("restart_container", {"name": "jellyfin"})

    assert adapter.calls == [("restart_container", "jellyfin")]
    assert result == {
        "target_type": "local_docker",
        "action": "restart_container",
        "container": {"name": "jellyfin", "result": "jellyfin"},
    }


def test_executor_rejects_unknown_action():
    executor = LocalDockerExecutor(adapter=StubDockerAdapter())

    with pytest.raises(KeyError):
        executor.run("remove_container", {"name": "jellyfin"})


def test_executor_exposes_bootstrap_runtime_action():
    adapter = StubDockerAdapter()
    executor = LocalDockerExecutor(adapter=adapter)

    result = executor.run("bootstrap_runtime", {})

    assert adapter.calls == [("ensure_runtime",)]
    assert result == {
        "target_type": "local_docker",
        "action": "bootstrap_runtime",
        "runtime": {"runtime": "orbstack", "docker_context": "orbstack"},
    }


def test_executor_exposes_deploy_home_assistant_action():
    adapter = StubDockerAdapter()
    executor = LocalDockerExecutor(adapter=adapter)

    result = executor.run(
        "deploy_home_assistant",
        {
            "config_dir": "local/home-assistant/config",
            "timezone": "Asia/Shanghai",
            "port": 8123,
            "container_name": "home-assistant",
            "image": "ghcr.io/home-assistant/home-assistant:stable",
        },
    )

    assert adapter.calls == [
        (
            "ensure_home_assistant",
            "local/home-assistant/config",
            "Asia/Shanghai",
            8123,
            "home-assistant",
            "ghcr.io/home-assistant/home-assistant:stable",
        )
    ]
    assert result == {
        "target_type": "local_docker",
        "action": "deploy_home_assistant",
        "deployment": {
            "name": "home-assistant",
            "image": "ghcr.io/home-assistant/home-assistant:stable",
            "config_dir": "local/home-assistant/config",
            "port": 8123,
            "status": "created",
            "result": "container-id",
        },
    }
