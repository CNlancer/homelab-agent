import json
from pathlib import Path

from homelab_agent.config.models import TargetConfig


def load_target_config(target_name: str, config_root: Path = Path("local/secrets")) -> TargetConfig:
    profile_path = config_root / "{0}.json".format(target_name)
    payload = json.loads(profile_path.read_text(encoding="utf-8"))
    return TargetConfig.model_validate(payload)
