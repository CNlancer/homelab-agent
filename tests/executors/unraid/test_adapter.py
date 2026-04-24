from homelab_agent.config.models import TargetConfig
from homelab_agent.executors.unraid.adapter import SshCommandAdapter


def test_read_system_info_calls_expected_ssh_commands():
    commands = []

    def runner(command: list[str]) -> str:
        commands.append(command)
        if command[-1] == "hostname":
            return "tower\n"
        if command[-1] == "uname -a":
            return "Linux tower 6.12.0-unraid aarch64 GNU/Linux\n"
        raise AssertionError("unexpected command")

    adapter = SshCommandAdapter(command_runner=runner)
    config = TargetConfig(
        label="unraid-tower",
        ssh_host="10.0.0.11",
        ssh_username="root",
    )

    payload = adapter.read_system_info(config)

    assert commands == [
        ["ssh", "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=10", "root@10.0.0.11", "hostname"],
        ["ssh", "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=10", "root@10.0.0.11", "uname -a"],
    ]
    assert payload == {
        "hostname": "tower",
        "kernel": "Linux tower 6.12.0-unraid aarch64 GNU/Linux",
    }


def test_list_containers_parses_remote_docker_ps_json():
    commands = []

    def runner(command: list[str]) -> str:
        commands.append(command)
        return "\n".join(
            [
                '{"ID":"abc123","Names":"jellyfin","Image":"jellyfin:latest","State":"running","Status":"Up 2 hours"}',
                '{"ID":"def456","Names":"postgres","Image":"postgres:16","State":"running","Status":"Up 1 hour"}',
            ]
        )

    adapter = SshCommandAdapter(command_runner=runner)
    config = TargetConfig(
        label="unraid-tower",
        ssh_host="10.0.0.11",
        ssh_username="root",
    )

    payload = adapter.list_containers(config, all_containers=True)

    assert commands == [
        [
            "ssh",
            "-o",
            "StrictHostKeyChecking=accept-new",
            "-o",
            "ConnectTimeout=10",
            "root@10.0.0.11",
            "docker ps -a --format '{{json .}}'",
        ]
    ]
    assert payload == [
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
            "state": "running",
            "status": "Up 1 hour",
        },
    ]


def test_password_profile_uses_askpass_without_putting_password_in_command():
    calls = []

    def runner(command: list[str], env: dict, stdin: object) -> str:
        calls.append((command, env, stdin))
        return "tower\n"

    adapter = SshCommandAdapter(password_command_runner=runner)
    config = TargetConfig(
        label="unraid-tower",
        ssh_host="10.0.0.11",
        ssh_username="root",
        ssh_password="secret",
    )

    payload = adapter._run_ssh(config, "hostname")

    command, env, _stdin = calls[0]
    assert payload == "tower\n"
    assert command == [
        "ssh",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        "ConnectTimeout=10",
        "root@10.0.0.11",
        "hostname",
    ]
    assert "secret" not in command
    assert env["HOMELAB_AGENT_SSH_PASSWORD"] == "secret"
    assert env["SSH_ASKPASS_REQUIRE"] == "force"


def test_configure_docker_registry_mirror_builds_unraid_config_command():
    commands = []

    def runner(command: list[str]) -> str:
        commands.append(command)
        return "\n".join(
            [
                "config_path=/boot/config/docker.cfg",
                "backup_path=/boot/config/docker.cfg.bak.20260419120000",
                "mirror_url=https://docker.1ms.run",
                "restart_docker=false",
                "docker_restarted=false",
            ]
        )

    adapter = SshCommandAdapter(command_runner=runner)
    config = TargetConfig(
        label="unraid-tower",
        ssh_host="10.0.0.11",
        ssh_username="root",
    )

    payload = adapter.configure_docker_registry_mirror(
        config,
        mirror_url="https://docker.1ms.run",
        restart_docker=False,
    )

    remote_command = commands[0][-1]
    assert "cfg=/boot/config/docker.cfg" in remote_command
    assert "mirror=https://docker.1ms.run" in remote_command
    assert "/etc/rc.d/rc.docker restart" in remote_command
    assert payload["mirror_url"] == "https://docker.1ms.run"
    assert payload["docker_restarted"] == "false"


def test_configure_ca_proxy_writes_proxy_cfg_with_backup_metadata():
    commands = []

    def runner(command: list[str]) -> str:
        commands.append(command)
        return "\n".join(
            [
                "config_path=/boot/config/plugins/community.applications/proxy.cfg",
                "backup_path=/boot/config/plugins/community.applications/proxy.cfg.bak.20260419130000",
                "proxy_url=http://10.0.0.2:6152",
                "tunnel=1",
            ]
        )

    adapter = SshCommandAdapter(command_runner=runner)
    config = TargetConfig(label="unraid", ssh_host="10.0.0.11", ssh_username="root")

    payload = adapter.configure_community_applications_proxy(
        config,
        proxy_host="10.0.0.2",
        proxy_port=6152,
        tunnel=True,
    )

    remote_command = commands[0][-1]
    assert "cfg=/boot/config/plugins/community.applications/proxy.cfg" in remote_command
    assert "proxy=10.0.0.2" in remote_command
    assert "port=6152" in remote_command
    assert 'printf \'proxy="%s"\\nport="%s"\\ntunnel="%s"\\n\'' in remote_command
    assert payload["proxy_url"] == "http://10.0.0.2:6152"
    assert payload["tunnel"] == "1"


def test_configure_docker_daemon_proxy_writes_docker_cfg_exports_with_no_proxy():
    commands = []

    def runner(command: list[str]) -> str:
        commands.append(command)
        return "\n".join(
            [
                "config_path=/boot/config/docker-proxy.env",
                "backup_path=/boot/config/docker.cfg.bak.20260419130000",
                "proxy_url=http://10.0.0.2:6152",
                "restart_docker=false",
                "docker_restarted=false",
            ]
        )

    adapter = SshCommandAdapter(command_runner=runner)
    config = TargetConfig(label="unraid", ssh_host="10.0.0.11", ssh_username="root")

    payload = adapter.configure_docker_daemon_proxy(
        config,
        proxy_url="http://10.0.0.2:6152",
        no_proxy="localhost,127.0.0.1,10.0.0.0/8",
        restart_docker=False,
    )

    remote_command = commands[0][-1]
    assert "cfg=/boot/config/docker.cfg" in remote_command
    assert 'HTTP_PROXY="http://10.0.0.2:6152"' in remote_command
    assert 'NO_PROXY="localhost,127.0.0.1,10.0.0.0/8"' in remote_command
    assert "export HTTP_PROXY HTTPS_PROXY NO_PROXY http_proxy https_proxy no_proxy" in remote_command
    assert payload["proxy_url"] == "http://10.0.0.2:6152"
    assert payload["docker_restarted"] == "false"


def test_install_boot_network_acceleration_hook_writes_safe_go_wrapper():
    commands = []

    def runner(command: list[str]) -> str:
        commands.append(command)
        return "\n".join(
            [
                "go_path=/boot/config/go",
                "go_backup_path=/boot/config/go.bak.20260419140000",
                "script_path=/boot/config/plugins/homelab-agent/apply-network-acceleration.sh",
                "hook_installed=true",
            ]
        )

    adapter = SshCommandAdapter(command_runner=runner)
    config = TargetConfig(label="unraid", ssh_host="10.0.0.11", ssh_username="root")

    payload = adapter.install_boot_network_acceleration_hook(
        config,
        mirror_url="https://docker.1ms.run",
        proxy_host="10.0.0.2",
        proxy_port=6152,
        no_proxy="localhost,127.0.0.1,::1,10.0.0.0/8",
    )

    remote_command = commands[0][-1]
    assert 'go=/boot/config/go' in remote_command
    assert 'script=/boot/config/plugins/homelab-agent/apply-network-acceleration.sh' in remote_command
    assert "homelab-agent boot hook begin" in remote_command
    assert "|| true" in remote_command
    assert payload["go_path"] == "/boot/config/go"
    assert payload["hook_installed"] == "true"


def test_configure_webui_proxy_writes_env_script_and_go_hook():
    commands = []

    def runner(command: list[str]) -> str:
        commands.append(command)
        return "\n".join(
            [
                "go_path=/boot/config/go",
                "go_backup_path=/boot/config/go.bak.20260423220000",
                "env_path=/boot/config/plugins/homelab-agent/unraid-webui-proxy.env",
                "script_path=/boot/config/plugins/homelab-agent/apply-webui-proxy.sh",
                "proxy_url=http://10.0.0.2:6152",
                "restart_webui=true",
                "webui_restarted=true",
            ]
        )

    adapter = SshCommandAdapter(command_runner=runner)
    config = TargetConfig(label="unraid", ssh_host="10.0.0.11", ssh_username="root")

    payload = adapter.configure_webui_proxy(
        config,
        proxy_url="http://10.0.0.2:6152",
        no_proxy="localhost,127.0.0.1,10.0.0.0/8",
        restart_webui=True,
    )

    remote_command = commands[0][-1]
    assert 'env_file=/boot/config/plugins/homelab-agent/unraid-webui-proxy.env' in remote_command
    assert 'script=/boot/config/plugins/homelab-agent/apply-webui-proxy.sh' in remote_command
    assert 'HTTP_PROXY="http://10.0.0.2:6152"' in remote_command
    assert 'NO_PROXY="localhost,127.0.0.1,10.0.0.0/8"' in remote_command
    assert "homelab-agent webui proxy begin" in remote_command
    assert "clear_env = no" in remote_command
    assert "env[HTTP_PROXY] = $HTTP_PROXY" in remote_command
    assert "docker_update_php=/usr/local/emhttp/plugins/dynamix.docker.manager/include/DockerUpdate.php" in remote_command
    assert "php <<'PHP'" in remote_command
    assert "putenv($parts[0] . '=' . $value);" in remote_command
    assert "/etc/rc.d/rc.php-fpm restart" in remote_command
    assert "/etc/rc.d/rc.nginx restart" in remote_command
    assert '/bin/bash "$script"' in remote_command
    assert payload["proxy_url"] == "http://10.0.0.2:6152"
    assert payload["webui_restarted"] == "true"


def test_backup_boot_config_to_local_builds_scp_to_timestamped_dir(tmp_path):
    commands = []

    def runner(command: list[str]) -> str:
        commands.append(command)
        return ""

    adapter = SshCommandAdapter(command_runner=runner)
    config = TargetConfig(label="unraid", ssh_host="10.0.0.11", ssh_username="root")

    payload = adapter.backup_boot_config_to_local(
        config,
        local_backup_root=tmp_path,
        timestamp="20260419_140500",
    )

    command = commands[0]
    assert command[0] == "scp"
    assert command[-2] == "root@10.0.0.11:/boot/config"
    assert command[-1].endswith("/unraid-20260419_140500/config")
    assert payload["remote_path"] == "/boot/config"
    assert payload["backup_timestamp"] == "20260419_140500"
