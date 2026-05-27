"""
SP3CT3R Pydantic Schemas — Request & Response shapes
"""
from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.scan import ScanStatus, ScanModule, RiskLevel


# ── Requests ──────────────────────────────────────────────

class ScanRequest(BaseModel):
    target: str
    module: ScanModule
    options: Optional[Dict[str, Any]] = {}

    @field_validator("target")
    @classmethod
    def target_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Target cannot be empty")
        return v


# ── Responses ─────────────────────────────────────────────

class ScanResultOut(BaseModel):
    id: int
    scan_id: str
    module: ScanModule
    category: str
    platform: str
    data: str
    status: str
    risk_level: RiskLevel
    raw: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class ScanSessionOut(BaseModel):
    id: str
    target: str
    module: ScanModule
    status: ScanStatus
    risk_level: RiskLevel
    progress: float
    total_found: int
    total_sources: int
    summary: Dict[str, Any]
    error_msg: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ScanStartResponse(BaseModel):
    scan_id: str
    target: str
    module: ScanModule
    status: ScanStatus
    message: str
    websocket_url: str


class ScanListResponse(BaseModel):
    total: int
    scans: List[ScanSessionOut]


# ── WebSocket message shapes ───────────────────────────────

class WSMessage(BaseModel):
    type: str           # "progress" | "result" | "log" | "complete" | "error"
    scan_id: str
    data: Dict[str, Any]
    timestamp: str


class LogLevel(str):
    INFO  = "INFO"
    OK    = "OK"
    WARN  = "WARN"
    ERROR = "ERROR"
    DATA  = "DATA"

