from typing import Any, Dict

from homelab_agent.config.models import TargetConfig
from homelab_agent.executors.unraid.adapter import SshCommandAdapter


class UnraidExecutor:
    def __init__(self, adapter: SshCommandAdapter, target_configs: Dict[str, TargetConfig]) -> None:
        self._adapter = adapter
        self._target_configs = target_configs

    def run(self, action: str, target_name: str, arguments: Dict[str, Any]) -> dict:
        config = self._target_configs[target_name]

        if action == "read_system_info":
            system_info = self._adapter.read_system_info(config)
            return {
                "target_type": "unraid",
                "action": action,
                "system_info": system_info,
            }

        if action == "list_containers":
            containers = self._adapter.list_containers(
                config,
                all_containers=bool(arguments.get("all_containers", False)),
            )
            return {
                "target_type": "unraid",
                "action": action,
                "containers": containers,
            }

        if action == "configure_docker_registry_mirror":
            mirror = arguments.get("mirror_url")
            if not isinstance(mirror, str):
                raise ValueError("mirror_url is required")
            result = self._adapter.configure_docker_registry_mirror(
                config,
                mirror_url=mirror,
                restart_docker=bool(arguments.get("restart_docker", False)),
            )
            return {
                "target_type": "unraid",
                "action": action,
                "docker_registry_mirror": result,
            }

        if action == "configure_community_applications_proxy":
            proxy_host = arguments.get("proxy_host")
            proxy_port = arguments.get("proxy_port")
            if not isinstance(proxy_host, str):
                raise ValueError("proxy_host is required")
            if not isinstance(proxy_port, int):
                raise ValueError("proxy_port is required")
            result = self._adapter.configure_community_applications_proxy(
                config,
                proxy_host=proxy_host,
                proxy_port=proxy_port,
                tunnel=bool(arguments.get("tunnel", True)),
            )
            return {
                "target_type": "unraid",
                "action": action,
                "community_applications_proxy": result,
            }

        if action == "configure_docker_daemon_proxy":
            proxy_url = arguments.get("proxy_url")
            if not isinstance(proxy_url, str):
                raise ValueError("proxy_url is required")
            no_proxy = arguments.get(
                "no_proxy",
                "localhost,127.0.0.1,::1,10.0.0.0/8,192.168.0.0/16,172.16.0.0/12,.local",
            )
            if not isinstance(no_proxy, str):
                raise ValueError("no_proxy must be a string")
            result = self._adapter.configure_docker_daemon_proxy(
                config,
                proxy_url=proxy_url,
                no_proxy=no_proxy,
                restart_docker=bool(arguments.get("restart_docker", False)),
            )
            return {
                "target_type": "unraid",
                "action": action,
                "docker_daemon_proxy": result,
            }

        if action == "install_boot_network_acceleration_hook":
            mirror_url = arguments.get("mirror_url")
            proxy_host = arguments.get("proxy_host")
            proxy_port = arguments.get("proxy_port")
            if not isinstance(mirror_url, str):
                raise ValueError("mirror_url is required")
            if not isinstance(proxy_host, str):
                raise ValueError("proxy_host is required")
            if not isinstance(proxy_port, int):
                raise ValueError("proxy_port is required")
            no_proxy = arguments.get(
                "no_proxy",
                "localhost,127.0.0.1,::1,10.0.0.0/8,192.168.0.0/16,172.16.0.0/12,.local",
            )
            if not isinstance(no_proxy, str):
                raise ValueError("no_proxy must be a string")
            result = self._adapter.install_boot_network_acceleration_hook(
                config,
                mirror_url=mirror_url,
                proxy_host=proxy_host,
                proxy_port=proxy_port,
                no_proxy=no_proxy,
            )
            return {
                "target_type": "unraid",
                "action": action,
                "boot_network_acceleration": result,
            }

        if action == "configure_webui_proxy":
            proxy_url = arguments.get("proxy_url")
            if not isinstance(proxy_url, str):
                raise ValueError("proxy_url is required")
            no_proxy = arguments.get(
                "no_proxy",
                "localhost,127.0.0.1,::1,10.0.0.0/8,192.168.0.0/16,172.16.0.0/12,.local",
            )
            if not isinstance(no_proxy, str):
                raise ValueError("no_proxy must be a string")
            result = self._adapter.configure_webui_proxy(
                config,
                proxy_url=proxy_url,
                no_proxy=no_proxy,
                restart_webui=bool(arguments.get("restart_webui", True)),
            )
            return {
                "target_type": "unraid",
                "action": action,
                "webui_proxy": result,
            }

        if action == "backup_boot_config_to_local":
            local_backup_root = arguments.get("local_backup_root", "var/backups/unraid")
            timestamp = arguments.get("timestamp")
            if not isinstance(local_backup_root, str):
                raise ValueError("local_backup_root must be a string")
            if timestamp is not None and not isinstance(timestamp, str):
                raise ValueError("timestamp must be a string")
            result = self._adapter.backup_boot_config_to_local(
                config,
                local_backup_root=local_backup_root,
                timestamp=timestamp,
            )
            return {
                "target_type": "unraid",
                "action": action,
                "local_backup": result,
            }

        raise KeyError("unsupported unraid action: {0}".format(action))
