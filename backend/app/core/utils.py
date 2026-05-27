"""
SP3CT3R Core Utilities
Shared helpers used across all modules
"""
import re, socket, ipaddress
from datetime import datetime
from typing import Optional


def is_valid_domain(domain: str) -> bool:
    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain.strip()))


def is_valid_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def is_valid_ip(ip: str) -> bool:
    try:
        ipaddress.ip_address(ip.strip())
        return True
    except ValueError:
        return False


def is_valid_phone(phone: str) -> bool:
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    return cleaned.isdigit() and 7 <= len(cleaned) <= 15


def sanitize_target(target: str) -> str:
    """Strip protocol prefixes and trailing slashes."""
    target = target.strip()
    for prefix in ["https://", "http://", "www."]:
        if target.lower().startswith(prefix):
            target = target[len(prefix):]
    return target.rstrip("/")


def detect_target_type(target: str) -> str:
    """Auto-detect the type of target input."""
    target = sanitize_target(target)
    if is_valid_ip(target):
        return "ip"
    if is_valid_email(target):
        return "email"
    if is_valid_domain(target):
        return "domain"
    if is_valid_phone(target):
        return "phone"
    return "username"


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def resolve_domain(domain: str) -> Optional[str]:
    """Basic DNS resolution."""
    try:
        return socket.gethostbyname(domain)
    except Exception:
        return None


def format_elapsed(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

