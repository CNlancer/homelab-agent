from homelab_agent.executors.mikrotik.adapter import MikroTikSshAdapter


def test_show_interfaces_runs_interface_print():
    commands = []

    def runner(command: list[str]) -> str:
        commands.append(command)
        return "0 R name=ether1 mtu=1500\n1   name=bridge mtu=1500\n"

    adapter = MikroTikSshAdapter(command_runner=runner)

    payload = adapter.show_interfaces("router")

    assert commands == [["ssh", "router", "/interface/print terse"]]
    assert payload == {
        "raw": "0 R name=ether1 mtu=1500\n1   name=bridge mtu=1500"
    }


def test_show_routes_runs_route_print():
    commands = []

    def runner(command: list[str]) -> str:
        commands.append(command)
        return "0 As dst-address=0.0.0.0/0 gateway=10.0.0.1\n"

    adapter = MikroTikSshAdapter(command_runner=runner)

    payload = adapter.show_routes("router")

    assert commands == [["ssh", "router", "/ip/route/print terse"]]
    assert payload == {
        "raw": "0 As dst-address=0.0.0.0/0 gateway=10.0.0.1"
    }


def test_export_firewall_runs_firewall_export():
    commands = []

    def runner(command: list[str]) -> str:
        commands.append(command)
        return "/ip firewall filter\nadd action=accept chain=input\n"

    adapter = MikroTikSshAdapter(command_runner=runner)

    payload = adapter.export_firewall("router")

    assert commands == [["ssh", "router", "/ip/firewall/filter/export terse"]]
    assert payload == {
        "raw": "/ip firewall filter\nadd action=accept chain=input"
    }
