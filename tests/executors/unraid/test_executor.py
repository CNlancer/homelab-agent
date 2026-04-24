import pytest
from typing import Optional

from homelab_agent.config.models import TargetConfig
from homelab_agent.executors.unraid.executor import UnraidExecutor


class StubSshAdapter:
    def __init__(self) -> None:
        self.calls = []

    def read_system_info(self, config: TargetConfig) -> dict:
        self.calls.append(("read_system_info", config.label, config.ssh_host))
        return {"hostname": config.ssh_host, "kernel": "Linux"}

    def list_containers(self, config: TargetConfig, all_containers: bool = False) -> list[dict]:
        self.calls.append(("list_containers", config.label, all_containers))
        return [{"name": "jellyfin", "state": "running"}]

    def configure_docker_registry_mirror(
        self,
        config: TargetConfig,
        mirror_url: str,
        restart_docker: bool = False,
    ) -> dict:
        self.calls.append(("configure_docker_registry_mirror", config.label, mirror_url, restart_docker))
        return {"mirror_url": mirror_url, "docker_restarted": str(restart_docker).lower()}

    def configure_community_applications_proxy(
        self,
        config: TargetConfig,
        proxy_host: str,
        proxy_port: int,
        tunnel: bool = True,
    ) -> dict:
        self.calls.append(("configure_community_applications_proxy", config.label, proxy_host, proxy_port, tunnel))
        return {"proxy_url": "http://{0}:{1}".format(proxy_host, proxy_port), "tunnel": "1" if tunnel else "0"}

    def configure_docker_daemon_proxy(
        self,
        config: TargetConfig,
        proxy_url: str,
        no_proxy: str,
        restart_docker: bool = False,
    ) -> dict:
        self.calls.append(("configure_docker_daemon_proxy", config.label, proxy_url, no_proxy, restart_docker))
        return {"proxy_url": proxy_url, "docker_restarted": str(restart_docker).lower()}

    def install_boot_network_acceleration_hook(
        self,
        config: TargetConfig,
        mirror_url: str,
        proxy_host: str,
        proxy_port: int,
        no_proxy: str,
    ) -> dict:
        self.calls.append(
            (
                "install_boot_network_acceleration_hook",
                config.label,
                mirror_url,
                proxy_host,
                proxy_port,
                no_proxy,
            )
        )
        return {
            "go_path": "/boot/config/go",
            "script_path": "/boot/config/plugins/homelab-agent/apply-network-acceleration.sh",
            "hook_installed": "true",
        }

    def configure_webui_proxy(
        self,
        config: TargetConfig,
        proxy_url: str,
        no_proxy: str,
        restart_webui: bool = True,
    ) -> dict:
        self.calls.append(("configure_webui_proxy", config.label, proxy_url, no_proxy, restart_webui))
        return {"proxy_url": proxy_url, "webui_restarted": str(restart_webui).lower()}

    def backup_boot_config_to_local(
        self,
        config: TargetConfig,
        local_backup_root: str,
        timestamp: Optional[str] = None,
    ) -> dict:
        self.calls.append(("backup_boot_config_to_local", config.label, local_backup_root, timestamp))
        return {
            "local_backup_path": "/tmp/unraid-backup",
            "remote_path": "/boot/config",
            "backup_timestamp": timestamp or "generated",
        }


def test_executor_reads_system_info_from_target_host():
    adapter = StubSshAdapter()
    config = TargetConfig(
        label="unraid",
        ssh_host="10.0.0.11",
        ssh_username="root",
        ssh_password="secret",
    )
    executor = UnraidExecutor(adapter=adapter, target_configs={"unraid": config})

    payload = executor.run("read_system_info", target_name="unraid", arguments={})

    assert adapter.calls == [("read_system_info", "unraid", "10.0.0.11")]
    assert payload == {
        "target_type": "unraid",
        "action": "read_system_info",
        "system_info": {"hostname": "10.0.0.11", "kernel": "Linux"},
    }


def test_executor_lists_containers_from_target_host():
    adapter = StubSshAdapter()
    config = TargetConfig(
        label="unraid",
        ssh_host="10.0.0.11",
        ssh_username="root",
        ssh_password="secret",
    )
    executor = UnraidExecutor(adapter=adapter, target_configs={"unraid": config, "tower": config})

    payload = executor.run("list_containers", target_name="tower", arguments={"all_containers": True})

    assert adapter.calls == [("list_containers", "unraid", True)]
    assert payload == {
        "target_type": "unraid",
        "action": "list_containers",
        "containers": [{"name": "jellyfin", "state": "running"}],
    }


def test_executor_configures_docker_registry_mirror():
    adapter = StubSshAdapter()
    config = TargetConfig(
        label="unraid",
        ssh_host="10.0.0.11",
        ssh_username="root",
        ssh_password="secret",
    )
    executor = UnraidExecutor(adapter=adapter, target_configs={"unraid": config, "tower": config})

    payload = executor.run(
        "configure_docker_registry_mirror",
        target_name="tower",
        arguments={"mirror_url": "https://docker.1ms.run", "restart_docker": True},
    )

    assert adapter.calls == [
        ("configure_docker_registry_mirror", "unraid", "https://docker.1ms.run", True),
    ]
    assert payload == {
        "target_type": "unraid",
        "action": "configure_docker_registry_mirror",
        "docker_registry_mirror": {
            "mirror_url": "https://docker.1ms.run",
            "docker_restarted": "true",
        },
    }


def test_executor_configures_community_applications_proxy():
    adapter = StubSshAdapter()
    config = TargetConfig(
        label="unraid",
        ssh_host="10.0.0.11",
        ssh_username="root",
        ssh_password="secret",
    )
    executor = UnraidExecutor(adapter=adapter, target_configs={"unraid": config})

    payload = executor.run(
        "configure_community_applications_proxy",
        target_name="unraid",
        arguments={"proxy_host": "10.0.0.2", "proxy_port": 6152, "tunnel": True},
    )

    assert adapter.calls == [("configure_community_applications_proxy", "unraid", "10.0.0.2", 6152, True)]
    assert payload["community_applications_proxy"]["proxy_url"] == "http://10.0.0.2:6152"


def test_executor_configures_docker_daemon_proxy():
    adapter = StubSshAdapter()
    config = TargetConfig(
        label="unraid",
        ssh_host="10.0.0.11",
        ssh_username="root",
        ssh_password="secret",
    )
    executor = UnraidExecutor(adapter=adapter, target_configs={"unraid": config})

    payload = executor.run(
        "configure_docker_daemon_proxy",
        target_name="unraid",
        arguments={
            "proxy_url": "http://10.0.0.2:6152",
            "no_proxy": "localhost,127.0.0.1,10.0.0.0/8",
            "restart_docker": False,
        },
    )

    assert adapter.calls == [
        (
            "configure_docker_daemon_proxy",
            "unraid",
            "http://10.0.0.2:6152",
            "localhost,127.0.0.1,10.0.0.0/8",
            False,
        )
    ]
    assert payload["docker_daemon_proxy"]["proxy_url"] == "http://10.0.0.2:6152"


def test_executor_installs_boot_network_acceleration_hook():
    adapter = StubSshAdapter()
    config = TargetConfig(
        label="unraid",
        ssh_host="10.0.0.11",
        ssh_username="root",
        ssh_password="secret",
    )
    executor = UnraidExecutor(adapter=adapter, target_configs={"unraid": config})

    payload = executor.run(
        "install_boot_network_acceleration_hook",
        target_name="unraid",
        arguments={
            "mirror_url": "https://docker.1ms.run",
            "proxy_host": "10.0.0.2",
            "proxy_port": 6152,
            "no_proxy": "localhost,127.0.0.1,::1,10.0.0.0/8",
        },
    )

    assert adapter.calls == [
        (
            "install_boot_network_acceleration_hook",
            "unraid",
            "https://docker.1ms.run",
            "10.0.0.2",
            6152,
            "localhost,127.0.0.1,::1,10.0.0.0/8",
        )
    ]
    assert payload["boot_network_acceleration"]["hook_installed"] == "true"


def test_executor_configures_webui_proxy():
    adapter = StubSshAdapter()
    config = TargetConfig(
        label="unraid",
        ssh_host="10.0.0.11",
        ssh_username="root",
        ssh_password="secret",
    )
    executor = UnraidExecutor(adapter=adapter, target_configs={"unraid": config})

    payload = executor.run(
        "configure_webui_proxy",
        target_name="unraid",
        arguments={
            "proxy_url": "http://10.0.0.2:6152",
            "no_proxy": "localhost,127.0.0.1,10.0.0.0/8",
            "restart_webui": True,
        },
    )

    assert adapter.calls == [
        (
            "configure_webui_proxy",
            "unraid",
            "http://10.0.0.2:6152",
            "localhost,127.0.0.1,10.0.0.0/8",
            True,
        )
    ]
    assert payload["webui_proxy"]["proxy_url"] == "http://10.0.0.2:6152"


def test_executor_runs_manual_unraid_boot_config_backup_to_local():
    adapter = StubSshAdapter()
    config = TargetConfig(
        label="unraid",
        ssh_host="10.0.0.11",
        ssh_username="root",
        ssh_password="secret",
    )
    executor = UnraidExecutor(adapter=adapter, target_configs={"unraid": config})

    payload = executor.run(
        "backup_boot_config_to_local",
        target_name="unraid",
        arguments={"local_backup_root": "/Users/lancer/projects/homelab-agent/var/backups/unraid"},
    )

    assert adapter.calls == [
        (
            "backup_boot_config_to_local",
            "unraid",
            "/Users/lancer/projects/homelab-agent/var/backups/unraid",
            None,
        )
    ]
    assert payload["local_backup"]["remote_path"] == "/boot/config"


def test_executor_rejects_unknown_action():
    config = TargetConfig(
        label="unraid",
        ssh_host="10.0.0.11",
        ssh_username="root",
        ssh_password="secret",
    )
    executor = UnraidExecutor(adapter=StubSshAdapter(), target_configs={"unraid": config, "tower": config})

    with pytest.raises(KeyError):
        executor.run("restart_array", target_name="tower", arguments={})
