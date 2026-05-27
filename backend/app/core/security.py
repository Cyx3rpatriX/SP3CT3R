"""
SP3CT3R Security Utilities
API key validation, rate limiting helpers
"""
from fastapi import HTTPException, Header
from app.core.config import settings
import hashlib, secrets, time
from typing import Optional


def generate_scan_id() -> str:
    """Generate a unique scan session ID."""
    return secrets.token_hex(16)


def hash_target(target: str) -> str:
    """Hash a target string for safe storage/logging."""
    return hashlib.sha256(target.encode()).hexdigest()[:16]


def validate_api_key(x_api_key: Optional[str] = Header(None)):
    """Optional internal API key check (for future auth)."""
    if settings.DEBUG:
        return True
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    return True


# Simple in-memory rate limiter (use Redis in production)
_rate_store: dict = {}

def check_rate_limit(client_ip: str, limit: int = 60) -> bool:
    """Returns True if within limit, False if exceeded."""
    now = int(time.time())
    window = now // 60  # 1-minute window
    key = f"{client_ip}:{window}"
    _rate_store[key] = _rate_store.get(key, 0) + 1
    # Cleanup old keys
    old = [k for k in _rate_store if k.split(":")[1] != str(window)]
    for k in old:
        del _rate_store[k]
    return _rate_store[key] <= limit

