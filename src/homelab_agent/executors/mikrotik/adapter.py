import subprocess
from typing import Callable


CommandRunner = Callable[[list[str]], str]


def run_command(command: list[str]) -> str:
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


class MikroTikSshAdapter:
    def __init__(self, command_runner: CommandRunner = run_command) -> None:
        self._command_runner = command_runner

    def _run_ssh(self, host: str, remote_command: str) -> str:
        return self._command_runner(["ssh", host, remote_command]).strip()

    def show_interfaces(self, host: str) -> dict:
        return {"raw": self._run_ssh(host, "/interface/print terse")}

    def show_routes(self, host: str) -> dict:
        return {"raw": self._run_ssh(host, "/ip/route/print terse")}

    def export_firewall(self, host: str) -> dict:
        return {"raw": self._run_ssh(host, "/ip/firewall/filter/export terse")}
