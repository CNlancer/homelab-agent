import subprocess
from pathlib import Path

from homelab_agent.executors.local_docker.adapter import DockerCliAdapter


def test_list_containers_parses_json_lines():
    commands = []

    def runner(command: list[str]) -> str:
        commands.append(command)
        return "\n".join(
            [
                '{"ID":"abc123","Names":"jellyfin","Image":"jellyfin:latest","State":"running","Status":"Up 2 hours"}',
                '{"ID":"def456","Names":"postgres","Image":"postgres:16","State":"exited","Status":"Exited (0) 1 hour ago"}',
            ]
        )

    adapter = DockerCliAdapter(command_runner=runner)

    containers = adapter.list_containers(all_containers=True)

    assert commands == [["docker", "ps", "-a", "--format", "{{json .}}"]]
    assert containers == [
        {
            "id": "abc123",
            "name": "jellyfin",
            "image": "jellyfin:latest",
            "state": "running",
            "status": "Up 2 hours",
        },
        {
            "id": "def456",
            "name": "postgres",
            "image": "postgres:16",
            "state": "exited",
            "status": "Exited (0) 1 hour ago",
        },
    ]


def test_restart_container_uses_docker_restart():
    commands = []

    def runner(command: list[str]) -> str:
        commands.append(command)
        return "jellyfin\n"

    adapter = DockerCliAdapter(command_runner=runner)

    result = adapter.restart_container("jellyfin")

    assert commands == [["docker", "restart", "jellyfin"]]
    assert result == {"name": "jellyfin", "result": "jellyfin"}


def test_ensure_runtime_installs_missing_orbstack_and_selects_context():
    commands = []

    def runner(command: list[str]) -> str:
        commands.append(command)
        if command == ["brew", "list", "--versions", "docker"]:
            return "docker 29.2.1\n"
        if command == ["brew", "list", "--cask", "--versions", "orbstack"]:
            raise subprocess.CalledProcessError(returncode=1, cmd=command)
        if command == ["brew", "install", "--cask", "orbstack"]:
            return "installed orbstack\n"
        if command == ["orb", "status"]:
            raise subprocess.CalledProcessError(returncode=1, cmd=command)
        if command == ["orb", "start"]:
            return "orbstack started\n"
        if command == ["docker", "context", "use", "orbstack"]:
            return "orbstack\n"
        if command == ["docker", "info"]:
            return "Server Version: 29.2.1\n"
        raise AssertionError("unexpected command: {0}".format(command))

    adapter = DockerCliAdapter(command_runner=runner)

    result = adapter.ensure_runtime()

    assert commands == [
        ["brew", "list", "--versions", "docker"],
        ["brew", "list", "--cask", "--versions", "orbstack"],
        ["brew", "install", "--cask", "orbstack"],
        ["orb", "status"],
        ["orb", "start"],
        ["docker", "context", "use", "orbstack"],
        ["docker", "info"],
    ]
    assert result == {
        "runtime": "orbstack",
        "installed_packages": ["orbstack"],
        "existing_packages": ["docker"],
        "orbstack_started": True,
        "docker_context": "orbstack",
    }


def test_ensure_home_assistant_creates_config_and_runs_container(tmp_path: Path):
    commands = []
    config_dir = tmp_path / "home-assistant"

    def runner(command: list[str]) -> str:
        commands.append(command)
        if command[:4] == ["docker", "ps", "-a", "--filter"]:
            return ""
        if command[:3] == ["docker", "run", "-d"]:
            return "container-id\n"
        raise AssertionError("unexpected command: {0}".format(command))

    adapter = DockerCliAdapter(command_runner=runner)

    result = adapter.ensure_home_assistant(
        config_dir=config_dir,
        timezone="Asia/Shanghai",
        port=8123,
        container_name="home-assistant",
        image="ghcr.io/home-assistant/home-assistant:stable",
    )

    assert config_dir.is_dir()
    assert commands == [
        [
            "docker",
            "ps",
            "-a",
            "--filter",
            "name=^home-assistant$",
            "--format",
            "{{json .}}",
        ],
        [
            "docker",
            "run",
            "-d",
            "--name",
            "home-assistant",
            "--restart",
            "unless-stopped",
            "-e",
            "TZ=Asia/Shanghai",
            "-v",
            "{0}:/config".format(config_dir.resolve()),
            "-p",
            "8123:8123",
            "ghcr.io/home-assistant/home-assistant:stable",
        ],
    ]
    assert result == {
        "name": "home-assistant",
        "image": "ghcr.io/home-assistant/home-assistant:stable",
        "config_dir": str(config_dir.resolve()),
        "port": 8123,
        "status": "created",
        "result": "container-id",
    }
