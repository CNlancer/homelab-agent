import json
from datetime import datetime, timezone
from pathlib import Path

from homelab_agent.models.result import ExecutionResult


class AuditLogger:
    def __init__(self, path: Path) -> None:
        self._path = path

    def record(self, result: ExecutionResult) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = result.model_dump()
        payload["recorded_at"] = datetime.now(timezone.utc).isoformat()
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True))
            handle.write("\n")
