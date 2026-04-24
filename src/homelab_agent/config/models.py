from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TargetConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1)
    base_url: Optional[str] = None
    ssh_host: str = Field(min_length=1)
    ssh_username: str = Field(min_length=1)
    ssh_password: Optional[str] = None
    ssh_identity_file: Optional[Path] = None
