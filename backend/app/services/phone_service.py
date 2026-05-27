# ── PHONE SERVICE ─────────────────────────────────────────────
"""SP3CT3R Phone OSINT Module"""
import asyncio, httpx, re
from typing import List, Dict, Any
from app.core.utils import now_iso
from app.websocket.manager import ws_manager

COUNTRY_CODES = {
    "1":"US/CA","7":"RU","20":"EG","27":"ZA","30":"GR","31":"NL","32":"BE","33":"FR",
    "34":"ES","36":"HU","39":"IT","40":"RO","41":"CH","43":"AT","44":"UK","45":"DK",
    "46":"SE","47":"NO","48":"PL","49":"DE","51":"PE","52":"MX","53":"CU","54":"AR",
    "55":"BR","56":"CL","57":"CO","58":"VE","60":"MY","61":"AU","62":"ID","63":"PH",
    "64":"NZ","65":"SG","66":"TH","81":"JP","82":"KR","84":"VN","86":"CN","90":"TR",
    "91":"IN","92":"PK","93":"AF","94":"LK","95":"MM","98":"IR","212":"MA","213":"DZ",
    "216":"TN","218":"LY","220":"GM","221":"SN","234":"NG","254":"KE","255":"TZ",
    "256":"UG","260":"ZM","263":"ZW","351":"PT","352":"LU","353":"IE","354":"IS",
    "358":"FI","359":"BG","370":"LT","371":"LV","372":"EE","380":"UA","381":"RS",
    "385":"HR","386":"SI","420":"CZ","421":"SK","966":"SA","971":"AE","972":"IL",
    "974":"QA","992":"TJ","994":"AZ","995":"GE","998":"UZ",
}


async def run_phone_scan(scan_id: str, target: str, db, options: dict = {}) -> Dict[str, Any]:
    phone = re.sub(r'[\s\-\(\)]', '', target.strip())
    await ws_manager.send_log(scan_id, "INFO", f"Initializing PHONE module for: {phone}")

    tasks = [
        _parse_phone(scan_id, phone),
        _carrier_lookup(scan_id, phone),
        _social_search(scan_id, phone),
    ]
    gathered = await asyncio.gather(*tasks, return_exceptions=True)
    results = [r for chunk in gathered if isinstance(chunk, list) for r in chunk]

    await ws_manager.send_log(scan_id, "OK", f"Phone scan complete: {len(results)} findings")
    summary = {"phone": phone, "total_findings": len(results), "completed_at": now_iso()}
    await ws_manager.send_complete(scan_id, summary)
    return {"results": results, "summary": summary}


async def _parse_phone(scan_id: str, phone: str) -> List[Dict]:
    findings = []
    await ws_manager.send_log(scan_id, "INFO", "Parsing phone number format...")
    clean = phone.lstrip("+")
    country = "Unknown"
    for code in sorted(COUNTRY_CODES.keys(), key=len, reverse=True):
        if clean.startswith(code):
            country = COUNTRY_CODES[code]
            break
    fields = [
        ("Phone Number", phone),
        ("Country Code", f"+{clean[:3]} → {country}"),
        ("Number Type", "Mobile / Landline (requires carrier DB)"),
        ("Formatted (E.164)", f"+{clean}"),
    ]
    for platform, data in fields:
        f = {"category": "phone_info", "platform": platform, "data": data,
             "status": "found", "risk_level": "info", "raw": {"phone": phone}}
        findings.append(f)
        await ws_manager.send_result(scan_id, f)
    await ws_manager.send_log(scan_id, "OK", f"Number parsed: {phone} → {country}")
    return findings


async def _carrier_lookup(scan_id: str, phone: str) -> List[Dict]:
    findings = []
    await ws_manager.send_log(scan_id, "WARN", "Carrier lookup requires NumVerify/Twilio API key")
    f = {"category": "carrier", "platform": "Carrier Lookup",
         "data": "Set NUMVERIFY_API_KEY or TWILIO credentials in .env for carrier data",
         "status": "partial", "risk_level": "info", "raw": {}}
    findings.append(f)
    await ws_manager.send_result(scan_id, f)
    return findings


async def _social_search(scan_id: str, phone: str) -> List[Dict]:
    findings = []
    await ws_manager.send_log(scan_id, "INFO", "Checking phone across social platforms...")
    platforms = ["WhatsApp", "Telegram", "Viber", "Signal"]
    for p in platforms:
        f = {"category": "social", "platform": p,
             "data": "Manual verification required (no public API)",
             "status": "partial", "risk_level": "info", "raw": {}}
        findings.append(f)
        await ws_manager.send_result(scan_id, f)
    return findings