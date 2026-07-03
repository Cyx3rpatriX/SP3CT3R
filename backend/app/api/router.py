# ── API ROUTES ────────────────────────────────────────────────
"""SP3CT3R API Router — combines all module routes"""
from fastapi import APIRouter
from app.api.routes import domain, email, username, phone, ip, darkweb, scans

api_router = APIRouter()
api_router.include_router(domain.router,   prefix="/domain",   tags=["Domain OSINT"])
api_router.include_router(email.router,    prefix="/email",    tags=["Email OSINT"])
api_router.include_router(username.router, prefix="/username", tags=["Username OSINT"])
api_router.include_router(phone.router,    prefix="/phone",    tags=["Phone OSINT"])
api_router.include_router(ip.router,       prefix="/ip",       tags=["IP Intelligence"])
api_router.include_router(darkweb.router,  prefix="/darkweb",  tags=["Dark Web Intel"])
api_router.include_router(scans.router,    prefix="/scans",    tags=["Scan Sessions"])
