from pathlib import Path

from homelab_agent.config.loader import load_target_config
from homelab_agent.core.router import ActionRouter
from homelab_agent.executors.local_docker.adapter import DockerCliAdapter
from homelab_agent.executors.local_docker.executor import LocalDockerExecutor
from homelab_agent.executors.mikrotik.adapter import MikroTikSshAdapter
from homelab_agent.executors.mikrotik.executor import MikroTikExecutor
from homelab_agent.executors.unraid.adapter import SshCommandAdapter
from homelab_agent.executors.unraid.executor import UnraidExecutor


def build_router(config_root: Path = Path("local/secrets")) -> ActionRouter:
    router = ActionRouter()
    local_docker_executor = LocalDockerExecutor(adapter=DockerCliAdapter())
    mikrotik_executor = MikroTikExecutor(adapter=MikroTikSshAdapter())
    router.register(
        "local_docker",
        "list_containers",
        lambda task: local_docker_executor.run("list_containers", task.arguments),
    )
    router.register(
        "local_docker",
        "restart_container",
        lambda task: local_docker_executor.run("restart_container", task.arguments),
    )
    router.register(
        "local_docker",
        "bootstrap_runtime",
        lambda task: local_docker_executor.run("bootstrap_runtime", task.arguments),
    )
    router.register(
        "local_docker",
        "deploy_home_assistant",
        lambda task: local_docker_executor.run("deploy_home_assistant", task.arguments),
    )
    unraid_profile_path = config_root / "unraid.json"
    if unraid_profile_path.exists():
        unraid_config = load_target_config("unraid", config_root=config_root)
        unraid_executor = UnraidExecutor(
            adapter=SshCommandAdapter(),
            target_configs={
                "unraid": unraid_config,
                unraid_config.label: unraid_config,
            },
        )
        router.register(
            "unraid",
            "read_system_info",
            lambda task: unraid_executor.run("read_system_info", task.target_name, task.arguments),
        )
        router.register(
            "unraid",
            "list_containers",
            lambda task: unraid_executor.run("list_containers", task.target_name, task.arguments),
        )
        router.register(
            "unraid",
            "configure_docker_registry_mirror",
            lambda task: unraid_executor.run("configure_docker_registry_mirror", task.target_name, task.arguments),
        )
        router.register(
            "unraid",
            "configure_community_applications_proxy",
            lambda task: unraid_executor.run(
                "configure_community_applications_proxy",
                task.target_name,
                task.arguments,
            ),
        )
        router.register(
            "unraid",
            "configure_docker_daemon_proxy",
            lambda task: unraid_executor.run("configure_docker_daemon_proxy", task.target_name, task.arguments),
        )
        router.register(
            "unraid",
            "install_boot_network_acceleration_hook",
            lambda task: unraid_executor.run(
                "install_boot_network_acceleration_hook",
                task.target_name,
                task.arguments,
            ),
        )
        router.register(
            "unraid",
            "configure_webui_proxy",
            lambda task: unraid_executor.run("configure_webui_proxy", task.target_name, task.arguments),
        )
        router.register(
            "unraid",
            "backup_boot_config_to_local",
            lambda task: unraid_executor.run("backup_boot_config_to_local", task.target_name, task.arguments),
        )
    router.register(
        "mikrotik",
        "show_interfaces",
        lambda task: mikrotik_executor.run("show_interfaces", task.target_name, task.arguments),
    )
    router.register(
        "mikrotik",
        "show_routes",
        lambda task: mikrotik_executor.run("show_routes", task.target_name, task.arguments),
    )
    router.register(
        "mikrotik",
        "export_firewall",
        lambda task: mikrotik_executor.run("export_firewall", task.target_name, task.arguments),
    )
    return router
