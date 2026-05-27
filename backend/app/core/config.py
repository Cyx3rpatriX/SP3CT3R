"""
SP3CT3R Core Configuration
All settings loaded from .env file
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "SP3CT3R"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "sp3ct3r-change-this-in-production"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./sp3ct3r.db"

    # Redis (optional — for caching & job queues)
    REDIS_URL: str = "redis://localhost:6379"
    USE_REDIS: bool = False

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]

    # API Keys (populated via .env)
    SHODAN_API_KEY: str = ""
    HUNTER_API_KEY: str = ""
    VIRUSTOTAL_API_KEY: str = ""
    IPINFO_API_KEY: str = ""
    WHOISXML_API_KEY: str = ""
    NUMVERIFY_API_KEY: str = ""

    # Scan settings
    MAX_CONCURRENT_SCANS: int = 5
    SCAN_TIMEOUT_SECONDS: int = 30
    DEFAULT_THREADS: int = 10

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

