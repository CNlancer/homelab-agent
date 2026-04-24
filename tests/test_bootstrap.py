from pathlib import Path

from homelab_agent.bootstrap import build_router
from homelab_agent.models.risk import RiskLevel
from homelab_agent.models.task import TaskSpec


def test_build_router_registers_unraid_profile_from_local_secrets(tmp_path: Path):
    secrets_dir = tmp_path / "secrets"
    secrets_dir.mkdir(parents=True)
    (secrets_dir / "unraid.json").write_text(
        """
        {
          "label": "unraid",
          "base_url": "http://10.0.0.11/",
          "ssh_host": "10.0.0.11",
          "ssh_username": "root",
          "ssh_password": "secret"
        }
        """.strip(),
        encoding="utf-8",
    )

    router = build_router(config_root=secrets_dir)
    task = TaskSpec(
        target_type="unraid",
        target_name="unraid",
        action="read_system_info",
        arguments={},
        risk_level=RiskLevel.SAFE_READ,
        confirmation_required=False,
    )

    registered = router.resolve(task)

    assert registered.executor_name == "unraid"
    assert registered.action_name == "read_system_info"


def test_build_router_registers_unraid_docker_registry_mirror_action(tmp_path: Path):
    secrets_dir = tmp_path / "secrets"
    secrets_dir.mkdir(parents=True)
    (secrets_dir / "unraid.json").write_text(
        """
        {
          "label": "unraid",
          "base_url": "http://10.0.0.11/",
          "ssh_host": "10.0.0.11",
          "ssh_username": "root",
          "ssh_password": "secret"
        }
        """.strip(),
        encoding="utf-8",
    )

    router = build_router(config_root=secrets_dir)
    task = TaskSpec(
        target_type="unraid",
        target_name="unraid",
        action="configure_docker_registry_mirror",
        arguments={"mirror_url": "https://docker.1ms.run"},
        risk_level=RiskLevel.SAFE_WRITE,
        confirmation_required=True,
    )

    registered = router.resolve(task)

    assert registered.executor_name == "unraid"
    assert registered.action_name == "configure_docker_registry_mirror"


def test_build_router_registers_unraid_community_applications_proxy_action(tmp_path: Path):
    secrets_dir = tmp_path / "secrets"
    secrets_dir.mkdir(parents=True)
    (secrets_dir / "unraid.json").write_text(
        """
        {
          "label": "unraid",
          "base_url": "http://10.0.0.11/",
          "ssh_host": "10.0.0.11",
          "ssh_username": "root",
          "ssh_password": "secret"
        }
        """.strip(),
        encoding="utf-8",
    )

    router = build_router(config_root=secrets_dir)
    task = TaskSpec(
        target_type="unraid",
        target_name="unraid",
        action="configure_community_applications_proxy",
        arguments={"proxy_host": "10.0.0.2", "proxy_port": 6152},
        risk_level=RiskLevel.SAFE_WRITE,
        confirmation_required=True,
    )

    registered = router.resolve(task)

    assert registered.executor_name == "unraid"
    assert registered.action_name == "configure_community_applications_proxy"


def test_build_router_registers_unraid_docker_daemon_proxy_action(tmp_path: Path):
    secrets_dir = tmp_path / "secrets"
    secrets_dir.mkdir(parents=True)
    (secrets_dir / "unraid.json").write_text(
        """
        {
          "label": "unraid",
          "base_url": "http://10.0.0.11/",
          "ssh_host": "10.0.0.11",
          "ssh_username": "root",
          "ssh_password": "secret"
        }
        """.strip(),
        encoding="utf-8",
    )

    router = build_router(config_root=secrets_dir)
    task = TaskSpec(
        target_type="unraid",
        target_name="unraid",
        action="configure_docker_daemon_proxy",
        arguments={"proxy_url": "http://10.0.0.2:6152"},
        risk_level=RiskLevel.SAFE_WRITE,
        confirmation_required=True,
    )

    registered = router.resolve(task)

    assert registered.executor_name == "unraid"
    assert registered.action_name == "configure_docker_daemon_proxy"


def test_build_router_registers_unraid_boot_hook_action(tmp_path: Path):
    secrets_dir = tmp_path / "secrets"
    secrets_dir.mkdir(parents=True)
    (secrets_dir / "unraid.json").write_text(
        """
        {
          "label": "unraid",
          "base_url": "http://10.0.0.11/",
          "ssh_host": "10.0.0.11",
          "ssh_username": "root",
          "ssh_password": "secret"
        }
        """.strip(),
        encoding="utf-8",
    )

    router = build_router(config_root=secrets_dir)
    task = TaskSpec(
        target_type="unraid",
        target_name="unraid",
        action="install_boot_network_acceleration_hook",
        arguments={
            "mirror_url": "https://docker.1ms.run",
            "proxy_host": "10.0.0.2",
            "proxy_port": 6152,
        },
        risk_level=RiskLevel.SAFE_WRITE,
        confirmation_required=True,
    )

    registered = router.resolve(task)

    assert registered.executor_name == "unraid"
    assert registered.action_name == "install_boot_network_acceleration_hook"


def test_build_router_registers_unraid_webui_proxy_action(tmp_path: Path):
    secrets_dir = tmp_path / "secrets"
    secrets_dir.mkdir(parents=True)
    (secrets_dir / "unraid.json").write_text(
        """
        {
          "label": "unraid",
          "base_url": "http://10.0.0.11/",
          "ssh_host": "10.0.0.11",
          "ssh_username": "root",
          "ssh_password": "secret"
        }
        """.strip(),
        encoding="utf-8",
    )

    router = build_router(config_root=secrets_dir)
    task = TaskSpec(
        target_type="unraid",
        target_name="unraid",
        action="configure_webui_proxy",
        arguments={"proxy_url": "http://10.0.0.2:6152"},
        risk_level=RiskLevel.SAFE_WRITE,
        confirmation_required=True,
    )

    registered = router.resolve(task)

    assert registered.executor_name == "unraid"
    assert registered.action_name == "configure_webui_proxy"


def test_build_router_registers_unraid_backup_action(tmp_path: Path):
    secrets_dir = tmp_path / "secrets"
    secrets_dir.mkdir(parents=True)
    (secrets_dir / "unraid.json").write_text(
        """
        {
          "label": "unraid",
          "base_url": "http://10.0.0.11/",
          "ssh_host": "10.0.0.11",
          "ssh_username": "root",
          "ssh_password": "secret"
        }
        """.strip(),
        encoding="utf-8",
    )

    router = build_router(config_root=secrets_dir)
    task = TaskSpec(
        target_type="unraid",
        target_name="unraid",
        action="backup_boot_config_to_local",
        arguments={"local_backup_root": "/tmp/backups/unraid"},
        risk_level=RiskLevel.SAFE_READ,
        confirmation_required=False,
    )

    registered = router.resolve(task)

    assert registered.executor_name == "unraid"
    assert registered.action_name == "backup_boot_config_to_local"


def test_build_router_registers_local_docker_bootstrap_runtime(tmp_path: Path):
    secrets_dir = tmp_path / "secrets"
    secrets_dir.mkdir(parents=True)
    (secrets_dir / "unraid.json").write_text(
        """
        {
          "label": "unraid",
          "base_url": "http://10.0.0.11/",
          "ssh_host": "10.0.0.11",
          "ssh_username": "root",
          "ssh_password": "secret"
        }
        """.strip(),
        encoding="utf-8",
    )

    router = build_router(config_root=secrets_dir)
    task = TaskSpec(
        target_type="local_docker",
        target_name="local",
        action="bootstrap_runtime",
        arguments={},
        risk_level=RiskLevel.HIGH_RISK,
        confirmation_required=True,
    )

    registered = router.resolve(task)

    assert registered.executor_name == "local_docker"
    assert registered.action_name == "bootstrap_runtime"


def test_build_router_supports_local_actions_without_unraid_profile(tmp_path: Path):
    router = build_router(config_root=tmp_path / "missing-secrets")
    task = TaskSpec(
        target_type="local_docker",
        target_name="local",
        action="deploy_home_assistant",
        arguments={},
        risk_level=RiskLevel.HIGH_RISK,
        confirmation_required=True,
    )

    registered = router.resolve(task)

    assert registered.executor_name == "local_docker"
    assert registered.action_name == "deploy_home_assistant"
