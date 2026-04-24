from pathlib import Path
from typing import Any, Dict

from homelab_agent.executors.local_docker.adapter import DockerCliAdapter


class LocalDockerExecutor:
    def __init__(self, adapter: DockerCliAdapter) -> None:
        self._adapter = adapter

    def _string_argument(self, arguments: Dict[str, Any], key: str, default: str) -> str:
        value = arguments.get(key, default)
        if not isinstance(value, str) or not value.strip():
            raise ValueError("{0} must be a non-empty string".format(key))
        return value

    def _port_argument(self, arguments: Dict[str, Any], key: str, default: int) -> int:
        value = arguments.get(key, default)
        port = int(value)
        if port < 1 or port > 65535:
            raise ValueError("{0} must be between 1 and 65535".format(key))
        return port

    def run(self, action: str, arguments: Dict[str, Any]) -> dict:
        if action == "list_containers":
            containers = self._adapter.list_containers(
                all_containers=bool(arguments.get("all_containers", False))
            )
            return {
                "target_type": "local_docker",
                "action": action,
                "containers": containers,
            }

        if action == "restart_container":
            container = self._adapter.restart_container(str(arguments["name"]))
            return {
                "target_type": "local_docker",
                "action": action,
                "container": container,
            }

        if action == "bootstrap_runtime":
            runtime = self._adapter.ensure_runtime()
            return {
                "target_type": "local_docker",
                "action": action,
                "runtime": runtime,
            }

        if action == "deploy_home_assistant":
            deployment = self._adapter.ensure_home_assistant(
                config_dir=Path(
                    self._string_argument(
                        arguments,
                        "config_dir",
                        "local/home-assistant/config",
                    )
                ),
                timezone=self._string_argument(arguments, "timezone", "UTC"),
                port=self._port_argument(arguments, "port", 8123),
                container_name=self._string_argument(
                    arguments,
                    "container_name",
                    "home-assistant",
                ),
                image=self._string_argument(
                    arguments,
                    "image",
                    "ghcr.io/home-assistant/home-assistant:stable",
                ),
            )
            return {
                "target_type": "local_docker",
                "action": action,
                "deployment": deployment,
            }

        raise KeyError("unsupported local_docker action: {0}".format(action))
