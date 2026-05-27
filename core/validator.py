"""SP3CT3R Input Validators"""
from app.core.utils import is_valid_domain, is_valid_email, is_valid_ip, is_valid_phone, detect_target_type
# Re-export for use from shared core (no FastAPI dependency)
__all__ = ["is_valid_domain", "is_valid_email", "is_valid_ip", "is_valid_phone", "detect_target_type"]