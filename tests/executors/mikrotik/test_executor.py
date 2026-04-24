import pytest

from homelab_agent.executors.mikrotik.executor import MikroTikExecutor


class StubMikroTikAdapter:
    def __init__(self) -> None:
        self.calls = []

    def show_interfaces(self, host: str) -> dict:
        self.calls.append(("show_interfaces", host))
        return {"raw": "ether1"}

    def show_routes(self, host: str) -> dict:
        self.calls.append(("show_routes", host))
        return {"raw": "0.0.0.0/0"}

    def export_firewall(self, host: str) -> dict:
        self.calls.append(("export_firewall", host))
        return {"raw": "/ip firewall filter"}


def test_executor_shows_interfaces():
    adapter = StubMikroTikAdapter()
    executor = MikroTikExecutor(adapter=adapter)

    payload = executor.run("show_interfaces", target_name="router", arguments={})

    assert adapter.calls == [("show_interfaces", "router")]
    assert payload == {
        "target_type": "mikrotik",
        "action": "show_interfaces",
        "interfaces": {"raw": "ether1"},
    }


def test_executor_shows_routes():
    adapter = StubMikroTikAdapter()
    executor = MikroTikExecutor(adapter=adapter)

    payload = executor.run("show_routes", target_name="router", arguments={})

    assert adapter.calls == [("show_routes", "router")]
    assert payload == {
        "target_type": "mikrotik",
        "action": "show_routes",
        "routes": {"raw": "0.0.0.0/0"},
    }


def test_executor_exports_firewall():
    adapter = StubMikroTikAdapter()
    executor = MikroTikExecutor(adapter=adapter)

    payload = executor.run("export_firewall", target_name="router", arguments={})

    assert adapter.calls == [("export_firewall", "router")]
    assert payload == {
        "target_type": "mikrotik",
        "action": "export_firewall",
        "firewall": {"raw": "/ip firewall filter"},
    }


def test_executor_rejects_unknown_action():
    executor = MikroTikExecutor(adapter=StubMikroTikAdapter())

    with pytest.raises(KeyError):
        executor.run("set_dns", target_name="router", arguments={})
