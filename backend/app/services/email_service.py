# ── EMAIL SERVICE ────────────────────────────────────────────
"""SP3CT3R Email OSINT Module"""
import asyncio, re, httpx
from typing import List, Dict, Any
from app.core.utils import sanitize_target, now_iso
from app.websocket.manager import ws_manager
import logging

logger = logging.getLogger("sp3ct3r.email")

BREACH_CHECK_APIS = ["haveibeenpwned.com", "dehashed.com", "leakcheck.io"]


async def run_email_scan(scan_id: str, target: str, db, options: dict = {}) -> Dict[str, Any]:
    email = target.strip().lower()
    await ws_manager.send_log(scan_id, "INFO", f"Initializing EMAIL module for: {email}")

    tasks = [
        _validate_email(scan_id, email),
        _mx_check(scan_id, email),
        _gravatar_check(scan_id, email),
        _breach_check(scan_id, email),
        _social_search(scan_id, email),
    ]
    gathered = await asyncio.gather(*tasks, return_exceptions=True)
    results = [r for chunk in gathered if isinstance(chunk, list) for r in chunk]

    await ws_manager.send_log(scan_id, "OK", f"Email scan complete: {len(results)} findings")
    summary = {"email": email, "total_findings": len(results), "completed_at": now_iso()}
    await ws_manager.send_complete(scan_id, summary)
    return {"results": results, "summary": summary}


async def _validate_email(scan_id: str, email: str) -> List[Dict]:
    findings = []
    parts = email.split("@")
    if len(parts) != 2:
        return findings
    user, domain = parts
    f = {"category": "validation", "platform": "Email Format", "data": email,
         "status": "found", "risk_level": "info", "raw": {"user": user, "domain": domain}}
    findings.append(f)
    await ws_manager.send_result(scan_id, f)
    await ws_manager.send_log(scan_id, "OK", f"Email format valid: {email}")
    return findings


async def _mx_check(scan_id: str, email: str) -> List[Dict]:
    findings = []
    domain = email.split("@")[1]
    await ws_manager.send_log(scan_id, "INFO", f"Checking MX records for {domain}...")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://dns.google/resolve", params={"name": domain, "type": "MX"})
            data = resp.json()
            for ans in data.get("Answer", []):
                f = {"category": "mx", "platform": "MX Record", "data": ans.get("data", ""),
                     "status": "found", "risk_level": "info", "raw": ans}
                findings.append(f)
                await ws_manager.send_result(scan_id, f)
        await ws_manager.send_log(scan_id, "OK", f"MX records found for {domain}")
    except Exception as e:
        await ws_manager.send_log(scan_id, "WARN", f"MX check failed: {e}")
    return findings


async def _gravatar_check(scan_id: str, email: str) -> List[Dict]:
    findings = []
    import hashlib
    gh = hashlib.md5(email.strip().lower().encode()).hexdigest()
    url = f"https://www.gravatar.com/avatar/{gh}?d=404"
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(url)
            status = "found" if resp.status_code == 200 else "not_found"
            f = {"category": "social", "platform": "Gravatar", "data": url if status == "found" else "No profile",
                 "status": status, "risk_level": "info", "raw": {"hash": gh}}
            findings.append(f)
            await ws_manager.send_result(scan_id, f)
            await ws_manager.send_log(scan_id, "OK" if status == "found" else "INFO",
                                       f"Gravatar: {'profile found' if status == 'found' else 'no profile'}")
    except Exception as e:
        await ws_manager.send_log(scan_id, "WARN", f"Gravatar check failed: {e}")
    return findings


async def _breach_check(scan_id: str, email: str) -> List[Dict]:
    """Stub — requires HIBP API key in production."""
    findings = []
    await ws_manager.send_log(scan_id, "INFO", "Checking breach databases...")
    await ws_manager.send_log(scan_id, "WARN", "HIBP check requires API key (set HIBP_API_KEY in .env)")
    f = {"category": "breach", "platform": "HaveIBeenPwned", "data": "API key required for breach lookup",
         "status": "partial", "risk_level": "info", "raw": {}}
    findings.append(f)
    await ws_manager.send_result(scan_id, f)
    return findings


async def _social_search(scan_id: str, email: str) -> List[Dict]:
    """Check common services for email registration hints."""
    findings = []
    domain = email.split("@")[1]
    providers = {
        "Gmail": "gmail.com", "Outlook": "outlook.com",
        "Yahoo": "yahoo.com", "ProtonMail": "proton.me"
    }
    for name, provider_domain in providers.items():
        if provider_domain in domain:
            f = {"category": "provider", "platform": f"Email Provider: {name}",
                 "data": f"Target uses {name} ({provider_domain})",
                 "status": "found", "risk_level": "info", "raw": {}}
            findings.append(f)
            await ws_manager.send_result(scan_id, f)
            await ws_manager.send_log(scan_id, "DATA", f"Email provider identified: {name}")
    return findings