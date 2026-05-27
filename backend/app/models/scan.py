"""
SP3CT3R Database Models
Scan sessions, results, and findings
"""
from sqlalchemy import Column, String, Text, DateTime, Float, Integer, JSON, Enum as SAEnum
from sqlalchemy.sql import func
from app.db.database import Base
import enum


class ScanStatus(str, enum.Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"
    CANCELLED = "cancelled"


class ScanModule(str, enum.Enum):
    DOMAIN   = "domain"
    EMAIL    = "email"
    USERNAME = "username"
    PHONE    = "phone"
    IP       = "ip"
    PERSON   = "person"


class RiskLevel(str, enum.Enum):
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"
    INFO     = "info"


class ScanSession(Base):
    """A single scan session for a target."""
    __tablename__ = "scan_sessions"

    id          = Column(String(32), primary_key=True)
    target      = Column(String(512), nullable=False, index=True)
    module      = Column(SAEnum(ScanModule), nullable=False)
    status      = Column(SAEnum(ScanStatus), default=ScanStatus.PENDING)
    risk_level  = Column(SAEnum(RiskLevel), default=RiskLevel.INFO)
    progress    = Column(Float, default=0.0)          # 0.0 - 100.0
    total_found = Column(Integer, default=0)
    total_sources = Column(Integer, default=0)
    summary     = Column(JSON, default=dict)          # Module-specific summary
    error_msg   = Column(Text, nullable=True)
    started_at  = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())


class ScanResult(Base):
    """Individual finding from a scan."""
    __tablename__ = "scan_results"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    scan_id    = Column(String(32), nullable=False, index=True)
    module     = Column(SAEnum(ScanModule), nullable=False)
    category   = Column(String(64))    # e.g. "dns", "subdomain", "social", "breach"
    platform   = Column(String(128))   # e.g. "Twitter", "A Record", "HaveIBeenPwned"
    data       = Column(Text)          # The actual finding
    status     = Column(String(32))    # "found", "not_found", "partial", "exposed"
    risk_level = Column(SAEnum(RiskLevel), default=RiskLevel.INFO)
    raw        = Column(JSON, default=dict)   # Full raw response
    created_at = Column(DateTime(timezone=True), server_default=func.now())

