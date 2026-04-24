from enum import Enum


class RiskLevel(str, Enum):
    SAFE_READ = "safe_read"
    SAFE_WRITE = "safe_write"
    HIGH_RISK = "high_risk"
    BLOCKED = "blocked"
