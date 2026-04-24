from typing import Any, Dict

from homelab_agent.executors.mikrotik.adapter import MikroTikSshAdapter


class MikroTikExecutor:
    def __init__(self, adapter: MikroTikSshAdapter) -> None:
        self._adapter = adapter

    def run(self, action: str, target_name: str, arguments: Dict[str, Any]) -> dict:
        del arguments

        if action == "show_interfaces":
            return {
                "target_type": "mikrotik",
                "action": action,
                "interfaces": self._adapter.show_interfaces(target_name),
            }

        if action == "show_routes":
            return {
                "target_type": "mikrotik",
                "action": action,
                "routes": self._adapter.show_routes(target_name),
            }

        if action == "export_firewall":
            return {
                "target_type": "mikrotik",
                "action": action,
                "firewall": self._adapter.export_firewall(target_name),
            }

        raise KeyError("unsupported mikrotik action: {0}".format(action))
