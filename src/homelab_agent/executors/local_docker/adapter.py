import json
import subprocess
from pathlib import Path
from typing import Callable, List, Optional


CommandRunner = Callable[[list[str]], str]


def run_command(command: list[str]) -> str:
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


class DockerCliAdapter:
    def __init__(self, command_runner: CommandRunner = run_command) -> None:
        self._command_runner = command_runner

    def _command_succeeds(self, command: list[str]) -> bool:
        try:
            self._command_runner(command)
        except subprocess.CalledProcessError:
            return False
        return True

    def _find_container(self, name: str) -> Optional[dict]:
        output = self._command_runner(
            [
                "docker",
                "ps",
                "-a",
                "--filter",
                "name=^{0}$".format(name),
                "--format",
                "{{json .}}",
            ]
        )
        for line in output.splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            return {
                "id": payload["ID"],
                "name": payload["Names"],
                "image": payload["Image"],
                "state": payload["State"],
                "status": payload["Status"],
            }
        return None

    def list_containers(self, all_containers: bool = False) -> List[dict]:
        command = ["docker", "ps"]
        if all_containers:
            command.append("-a")
        command.extend(["--format", "{{json .}}"])
        output = self._command_runner(command)
        containers = []
        for line in output.splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            containers.append(
                {
                    "id": payload["ID"],
                    "name": payload["Names"],
                    "image": payload["Image"],
                    "state": payload["State"],
                    "status": payload["Status"],
                }
            )
        return containers

    def restart_container(self, name: str) -> dict:
        output = self._command_runner(["docker", "restart", name])
        return {
            "name": name,
            "result": output.strip(),
        }

    def ensure_runtime(self) -> dict:
        installed_packages = []
        existing_packages = []

        if self._command_succeeds(["brew", "list", "--versions", "docker"]):
            existing_packages.append("docker")
        else:
            self._command_runner(["brew", "install", "docker"])
            installed_packages.append("docker")

        if self._command_succeeds(["brew", "list", "--cask", "--versions", "orbstack"]):
            existing_packages.append("orbstack")
        else:
            self._command_runner(["brew", "install", "--cask", "orbstack"])
            installed_packages.append("orbstack")

        orbstack_started = False
        if not self._command_succeeds(["orb", "status"]):
            self._command_runner(["orb", "start"])
            orbstack_started = True

        self._command_runner(["docker", "context", "use", "orbstack"])
        self._command_runner(["docker", "info"])
        return {
            "runtime": "orbstack",
            "installed_packages": installed_packages,
            "existing_packages": existing_packages,
            "orbstack_started": orbstack_started,
            "docker_context": "orbstack",
        }

    def ensure_home_assistant(
        self,
        *,
        config_dir: Path,
        timezone: str,
        port: int,
        container_name: str,
        image: str,
    ) -> dict:
        resolved_config_dir = config_dir.expanduser().resolve()
        resolved_config_dir.mkdir(parents=True, exist_ok=True)

        existing_container = self._find_container(container_name)
        if existing_container is not None:
            if existing_container["state"] == "running":
                return {
                    "name": container_name,
                    "image": image,
                    "config_dir": str(resolved_config_dir),
                    "port": port,
                    "status": "running",
                    "result": existing_container["status"],
                }

            output = self._command_runner(["docker", "start", container_name])
            return {
                "name": container_name,
                "image": image,
                "config_dir": str(resolved_config_dir),
                "port": port,
                "status": "started",
                "result": output.strip(),
            }

        output = self._command_runner(
            [
                "docker",
                "run",
                "-d",
                "--name",
                container_name,
                "--restart",
                "unless-stopped",
                "-e",
                "TZ={0}".format(timezone),
                "-v",
                "{0}:/config".format(resolved_config_dir),
                "-p",
                "{0}:8123".format(port),
                image,
            ]
        )
        return {
            "name": container_name,
            "image": image,
            "config_dir": str(resolved_config_dir),
            "port": port,
            "status": "created",
            "result": output.strip(),
        }
