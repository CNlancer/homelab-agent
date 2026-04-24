import json
from pathlib import Path

from homelab_agent.core.audit import AuditLogger
from homelab_agent.models.result import ExecutionResult
from homelab_agent.models.risk import RiskLevel


def test_audit_logger_writes_jsonl_record(tmp_path: Path):
    audit_path = tmp_path / "audit.jsonl"
    logger = AuditLogger(audit_path)
    result = ExecutionResult(
        target_type="unraid",
        target_name="tower",
        action="read_system_info",
        risk_level=RiskLevel.SAFE_READ,
        confirmation_required=False,
        success=True,
        summary="system info collected",
        output={"hostname": "tower"},
    )

    logger.record(result)

    lines = audit_path.read_text().strip().splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["target_type"] == "unraid"
    assert payload["action"] == "read_system_info"
    assert payload["success"] is True
    assert payload["output"] == {"hostname": "tower"}
