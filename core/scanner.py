"""
SP3CT3R Shared Scanner Core
Used by both CLI and API layers — no FastAPI dependencies here
"""
import asyncio
from typing import Callable, List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ScanConfig:
    target: str
    module: str
    options: Dict[str, Any] = field(default_factory=dict)
    threads: int = 10
    timeout: int = 30
    output_format: str = "terminal"  # terminal | json | csv | pdf


@dataclass
class Finding:
    category: str
    platform: str
    data: str
    status: str = "found"
    risk_level: str = "info"
    raw: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict:
        return {
            "category": self.category, "platform": self.platform,
            "data": self.data, "status": self.status,
            "risk_level": self.risk_level, "raw": self.raw, "timestamp": self.timestamp,
        }


class Scanner:
    """Base scanner class shared across CLI and API."""

    def __init__(self, config: ScanConfig, on_finding: Optional[Callable] = None, on_log: Optional[Callable] = None):
        self.config = config
        self.findings: List[Finding] = []
        self._on_finding = on_finding
        self._on_log = on_log

    async def emit_finding(self, finding: Finding):
        self.findings.append(finding)
        if self._on_finding:
            await self._on_finding(finding)

    async def emit_log(self, level: str, message: str):
        if self._on_log:
            await self._on_log(level, message)

    def get_results(self) -> List[Dict]:
        return [f.to_dict() for f in self.findings]

    def risk_summary(self) -> str:
        levels = [f.risk_level for f in self.findings]
        for lvl in ["critical", "high", "medium", "low"]:
            if lvl in levels:
                return lvl
        return "info"