from pydantic import BaseModel, ConfigDict, Field, field_validator

from homelab_agent.models.risk import RiskLevel


class TaskSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_type: str = Field(min_length=1)
    target_name: str = Field(min_length=1)
    action: str = Field(min_length=1)
    arguments: dict
    risk_level: RiskLevel
    confirmation_required: bool

    @field_validator("action")
    @classmethod
    def action_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("action must not be blank")
        return value
