from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field

from homelab_agent.models.risk import RiskLevel


class ExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_type: str = Field(min_length=1)
    target_name: str = Field(min_length=1)
    action: str = Field(min_length=1)
    risk_level: RiskLevel
    confirmation_required: bool
    success: bool
    summary: str = Field(min_length=1)
    output: Dict[str, Any]
