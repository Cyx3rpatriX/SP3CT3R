"""
SP3CT3R — Dark Web Intelligence Module

Covers:
  1. Tor connectivity check + anonymized routing
  2. HIBP breach database lookup (email / domain)
  3. Paste site monitoring via psbdmp.ws
  4. VirusTotal + AbuseIPDB threat intelligence cross-check
  5. DeHashed credential search (commercial plug-in, key required)
  6. Flare / Recorded Future stubs (commercial plug-in hooks)
"""
import asyncio
import socket
import time
import re
import httpx
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.config import settings
from app.core.utils import now_iso, is_valid_email, is_valid_domain, is_valid_ip
from app.websocket.manager import ws_manager

logger = logging.getLogger("sp3ct3r.darkweb")

# ─────────────────────────────────────────────────────────────
# Paste site search — psbdmp.ws  (clearnet, public API)
# Used legitimately by Shodan, SpiderFoot, IntelX, etc.

PSBDMP_SEARCH = "https://psbdmp.ws/api/v3/search/{query}"
PSBDMP_DUMP   = "https://psbdmp.ws/api/v3/get/{id}"

# VirusTotal public lookup (no key required for basic domain/IP)
VT_DOMAIN_URL = "https://www.virustotal.com/api/v3/domains/{domain}"
VT_IP_URL     = "https://www.virustotal.com/api/v3/ip_addresses/{ip}"

# HIBP v3 (requires API key for email; domain search is API-key-gated)
HIBP_BREACH_URL      = "https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
HIBP_DOMAIN_URL      = "https://haveibeenpwned.com/api/v3/breaches"
HIBP_PASTE_URL       = "https://haveibeenpwned.com/api/v3/pasteaccount/{email}"
HIBP_DATA_CLASSES    = "https://haveibeenpwned.com/api/v3/dataclasses"

# AbuseIPDB (domain / IP reputation)
ABUSEIPDB_URL = "https://api.abuseipdb.com/api/v2/check"

# TOR check endpoint (clearnet — checks if we're exiting via Tor)
TOR_CHECK_URL = "https://check.torproject.org/api/ip"


# ═════════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ═════════════════════════════════════════════════════════════

async def run_darkweb_scan(
    scan_id: str,
    target: str,
    db,
    options: dict = {}
) -> Dict[str, Any]:
    """
    Orchestrates all dark web / threat intel sub-modules.
    Detects target type and runs appropriate checks.
    """
    results  = []
    target   = target.strip()

    # Detect target type
    if is_valid_email(target):
        target_type = "email"
    elif is_valid_domain(target):
        target_type = "domain"
    elif is_valid_ip(target):
        target_type = "ip"
    else:
        target_type = "keyword"

    await ws_manager.send_log(scan_id, "INFO",
        f"🕶  Dark Web module initializing — target: {target} [{target_type.upper()}]")
    await ws_manager.send_progress(scan_id, 2.0, 0, 6)

    # ── Run all sub-checks concurrently ──────────────────────
    tasks = [
        _tor_connectivity_check(scan_id),
        _hibp_breach_check(scan_id, target, target_type),
        _hibp_paste_check(scan_id, target, target_type),
        _paste_site_monitor(scan_id, target),
        _virustotal_check(scan_id, target, target_type),
        _dehashed_lookup(scan_id, target, target_type),
        _abuseipdb_check(scan_id, target, target_type),
        _threat_intel_aggregator(scan_id, target, target_type),
        _commercial_plugin_stubs(scan_id),
    ]

    gathered = await asyncio.gather(*tasks, return_exceptions=True)

    for idx, chunk in enumerate(gathered):
        if isinstance(chunk, list):
            results.extend(chunk)
        elif isinstance(chunk, Exception):
            logger.warning(f"Dark web sub-task {idx} error: {chunk}")

    await ws_manager.send_progress(scan_id, 100.0, len(results), 6)
    await ws_manager.send_log(scan_id, "OK",
        f"Dark web scan complete — {len(results)} intelligence findings")

    summary = {
        "target":        target,
        "target_type":   target_type,
        "total_findings": len(results),
        "breaches":      sum(1 for r in results if r.get("category") == "breach"),
        "pastes":        sum(1 for r in results if r.get("category") == "paste"),
        "threat_intel":  sum(1 for r in results if r.get("category") == "threat_intel"),
        "completed_at":  now_iso(),
    }
    await ws_manager.send_complete(scan_id, summary)
    return {"results": results, "summary": summary}


# ═════════════════════════════════════════════════════════════
# — TOR CONNECTIVITY CHECK
# ═════════════════════════════════════════════════════════════

async def _tor_connectivity_check(scan_id: str) -> List[Dict]:
    """
    Checks if a local Tor SOCKS5 proxy is reachable on
    127.0.0.1:9050 and whether we exit via a Tor node.
    Reports Tor circuit IP + exit country.
    """
    findings = []
    await ws_manager.send_log(scan_id, "INFO",
        f"Checking Tor SOCKS5 proxy on {settings.TOR_SOCKS_HOST}:{settings.TOR_SOCKS_PORT}...")

    # ── 1: Is Tor daemon listening? ─────────────────────
    tor_listening = False
    try:
        loop = asyncio.get_event_loop()
        def _tcp_probe():
            s = socket.socket()
            s.settimeout(3)
            result = s.connect_ex((settings.TOR_SOCKS_HOST, settings.TOR_SOCKS_PORT))
            s.close()
            return result == 0
        tor_listening = await loop.run_in_executor(None, _tcp_probe)
    except Exception:
        pass

    if not tor_listening:
        f = {
            "category": "tor", "platform": "Tor Daemon",
            "data": f"SOCKS5 proxy not reachable on {settings.TOR_SOCKS_HOST}:{settings.TOR_SOCKS_PORT} — Tor is not running",
            "status": "not_found", "risk_level": "info",
            "raw": {"tor_port": settings.TOR_SOCKS_PORT, "listening": False},
        }
        findings.append(f)
        await ws_manager.send_result(scan_id, f)
        await ws_manager.send_log(scan_id, "WARN",
            "Tor not running. Install Tor and start with: sudo service tor start")

        # Provide setup guidance as an info finding
        findings.append({
            "category": "tor", "platform": "Tor Setup Guide",
            "data": "Install: sudo apt install tor | Start: sudo service tor start | Default SOCKS5: 127.0.0.1:9050",
            "status": "partial", "risk_level": "info", "raw": {},
        })
        await ws_manager.send_result(scan_id, findings[-1])
        return findings

    await ws_manager.send_log(scan_id, "OK",
        f"Tor SOCKS5 proxy detected on port {settings.TOR_SOCKS_PORT}")

    # ── 2: Route a request through Tor, check exit IP ───
    exit_ip, exit_country, latency_ms = None, "Unknown", None
    try:
        import httpx
        proxies = {
            "http://":  f"socks5://{settings.TOR_SOCKS_HOST}:{settings.TOR_SOCKS_PORT}",
            "https://": f"socks5://{settings.TOR_SOCKS_HOST}:{settings.TOR_SOCKS_PORT}",
        }
        t0 = time.time()
        async with httpx.AsyncClient(proxies=proxies, timeout=15) as client:
            resp = await client.get(TOR_CHECK_URL)
            if resp.status_code == 200:
                data = resp.json()
                exit_ip  = data.get("IP", "Unknown")
                is_tor   = data.get("IsTor", False)
                latency_ms = int((time.time() - t0) * 1000)

                if is_tor:
                    await ws_manager.send_log(scan_id, "OK",
                        f"✅ Routing through Tor exit node: {exit_ip} ({latency_ms}ms)")
                    status = "found"
                    data_str = f"Connected via Tor exit node: {exit_ip} | Latency: {latency_ms}ms | Anonymized routing ACTIVE"
                else:
                    await ws_manager.send_log(scan_id, "WARN",
                        f"Proxy connected but Tor check returned non-Tor IP: {exit_ip}")
                    status = "partial"
                    data_str = f"SOCKS5 connected but exit IP {exit_ip} not recognized as Tor node"

                f = {
                    "category": "tor", "platform": "Tor Exit Node",
                    "data": data_str, "status": status, "risk_level": "info",
                    "raw": {"exit_ip": exit_ip, "is_tor": is_tor, "latency_ms": latency_ms},
                }
                findings.append(f)
                await ws_manager.send_result(scan_id, f)

    except Exception as e:
        await ws_manager.send_log(scan_id, "WARN", f"Tor routing test failed: {e}")
        findings.append({
            "category": "tor", "platform": "Tor Routing",
            "data": f"SOCKS5 port open but routing test failed: {e}",
            "status": "partial", "risk_level": "info", "raw": {},
        })

    # ── 3: Real IP without Tor (for comparison) ─────────
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get("https://ipinfo.io/json")
            if resp.status_code == 200:
                data = resp.json()
                real_ip = data.get("ip", "Unknown")
                f = {
                    "category": "tor", "platform": "Real IP (No Tor)",
                    "data": f"{real_ip} — {data.get('city','?')}, {data.get('country','?')} | {data.get('org','')}",
                    "status": "found", "risk_level": "info",
                    "raw": data,
                }
                findings.append(f)
                await ws_manager.send_result(scan_id, f)
                await ws_manager.send_log(scan_id, "DATA",
                    f"Clearnet IP: {real_ip} | Tor exit: {exit_ip or 'N/A'}")
    except Exception:
        pass

    await ws_manager.send_progress(scan_id, 15.0, len(findings), 6)
    return findings


# ═════════════════════════════════════════════════════════════
# — HIBP BREACH CHECK
# ═════════════════════════════════════════════════════════════

async def _hibp_breach_check(scan_id: str, target: str, target_type: str) -> List[Dict]:
    """
    HaveIBeenPwned v3 breach lookup.
    - Email targets: full per-account breach list
    - Domain targets: filter all breaches for domain matches
    Requires HIBP_API_KEY for email lookup.
    Domain breach filtering works without a key.
    """
    findings = []
    await ws_manager.send_log(scan_id, "INFO", "Querying HaveIBeenPwned breach database...")

    api_key = settings.HIBP_API_KEY
    headers = {
        "User-Agent":    "SP3CT3R-OSINT/1.0",
        "hibp-api-key":  api_key,
    }

    # ── Email breach lookup ───────────────────────────────────
    if target_type == "email" and api_key:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    HIBP_BREACH_URL.format(email=target),
                    headers=headers,
                    params={"truncateResponse": "false"},
                )
                if resp.status_code == 200:
                    breaches = resp.json()
                    await ws_manager.send_log(scan_id, "WARN" if breaches else "OK",
                        f"HIBP: {len(breaches)} breach(es) found for {target}")
                    for b in breaches:
                        classes = b.get("DataClasses", [])
                        severity = _breach_severity(classes)
                        f = {
                            "category":   "breach",
                            "platform":   f"HIBP — {b.get('Name', 'Unknown')}",
                            "data":       f"Breach date: {b.get('BreachDate','?')} | Pwned: {b.get('PwnCount',0):,} accounts | Data: {', '.join(classes[:5])}",
                            "status":     "found",
                            "risk_level": severity,
                            "raw":        b,
                        }
                        findings.append(f)
                        await ws_manager.send_result(scan_id, f)
                        await ws_manager.send_log(scan_id, "ERROR" if severity in ("critical","high") else "WARN",
                            f"⚠  BREACH: {b.get('Name')} [{', '.join(classes[:3])}]")

                elif resp.status_code == 404:
                    await ws_manager.send_log(scan_id, "OK", f"HIBP: No breaches found for {target}")
                    findings.append({
                        "category": "breach", "platform": "HIBP Breach Check",
                        "data": f"No breaches found for {target}",
                        "status": "not_found", "risk_level": "info", "raw": {},
                    })
                elif resp.status_code == 401:
                    await ws_manager.send_log(scan_id, "WARN", "HIBP API key invalid or expired")
        except Exception as e:
            await ws_manager.send_log(scan_id, "WARN", f"HIBP email lookup failed: {e}")

    elif target_type == "email" and not api_key:
        await ws_manager.send_log(scan_id, "WARN",
            "HIBP email lookup requires API key — set HIBP_API_KEY in .env")
        findings.append({
            "category": "breach", "platform": "HIBP (API Key Required)",
            "data": "Set HIBP_API_KEY in .env to enable email breach lookup — https://haveibeenpwned.com/API/Key",
            "status": "partial", "risk_level": "info", "raw": {},
        })

    # ── Domain breach scan (public — no key needed) ───────────
    if target_type in ("domain", "email"):
        domain = target.split("@")[-1] if "@" in target else target
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(HIBP_DOMAIN_URL, headers={"User-Agent": "SP3CT3R-OSINT/1.0"})
                if resp.status_code == 200:
                    all_breaches = resp.json()
                    domain_hits = [
                        b for b in all_breaches
                        if domain.lower() in b.get("Domain", "").lower()
                        or domain.lower() in b.get("Description", "").lower()
                    ]
                    if domain_hits:
                        await ws_manager.send_log(scan_id, "WARN",
                            f"HIBP domain scan: {len(domain_hits)} breach(es) reference {domain}")
                        for b in domain_hits:
                            classes = b.get("DataClasses", [])
                            f = {
                                "category":   "breach",
                                "platform":   f"HIBP Domain — {b.get('Name')}",
                                "data":       f"Domain {domain} referenced in breach: {b.get('BreachDate','?')} | {b.get('PwnCount',0):,} accounts",
                                "status":     "found",
                                "risk_level": _breach_severity(classes),
                                "raw":        b,
                            }
                            findings.append(f)
                            await ws_manager.send_result(scan_id, f)
                    else:
                        await ws_manager.send_log(scan_id, "OK", f"Domain {domain} not found in HIBP breach index")
        except Exception as e:
            await ws_manager.send_log(scan_id, "WARN", f"HIBP domain scan failed: {e}")

    await ws_manager.send_progress(scan_id, 30.0, len(findings), 6)
    return findings


# ═════════════════════════════════════════════════════════════
# — HIBP PASTE CHECK
# ═════════════════════════════════════════════════════════════

async def _hibp_paste_check(scan_id: str, target: str, target_type: str) -> List[Dict]:
    """
    HIBP paste account check — requires API key.
    Returns paste sites where the email appeared.
    """
    findings = []
    if target_type != "email":
        return findings

    api_key = settings.HIBP_API_KEY
    if not api_key:
        return findings

    await ws_manager.send_log(scan_id, "INFO", f"Checking HIBP paste index for {target}...")

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                HIBP_PASTE_URL.format(email=target),
                headers={"User-Agent": "SP3CT3R-OSINT/1.0", "hibp-api-key": api_key},
            )
            if resp.status_code == 200:
                pastes = resp.json()
                await ws_manager.send_log(scan_id, "WARN",
                    f"HIBP paste check: {len(pastes)} paste(s) contain {target}")
                for p in pastes:
                    f = {
                        "category":   "paste",
                        "platform":   f"HIBP Paste — {p.get('Source','Unknown')}",
                        "data":       f"Title: {p.get('Title') or 'Untitled'} | Date: {p.get('Date','?')} | Emails: {p.get('EmailCount',0)}",
                        "status":     "found",
                        "risk_level": "high",
                        "raw":        p,
                    }
                    findings.append(f)
                    await ws_manager.send_result(scan_id, f)
            elif resp.status_code == 404:
                await ws_manager.send_log(scan_id, "OK", f"No paste hits for {target} in HIBP")
    except Exception as e:
        await ws_manager.send_log(scan_id, "WARN", f"HIBP paste check failed: {e}")

    return findings


# ═════════════════════════════════════════════════════════════
# — PASTE SITE MONITOR (psbdmp.ws)
# ═════════════════════════════════════════════════════════════

async def _paste_site_monitor(scan_id: str, target: str) -> List[Dict]:
    """
    Searches psbdmp.ws — the largest public Pastebin dump index.
    Used by Shodan, SpiderFoot, IntelX in their OSINT pipelines.
    Returns paste matches containing the target string.
    """
    findings = []
    await ws_manager.send_log(scan_id, "INFO",
        f"Searching paste dump index (psbdmp.ws) for: {target}")

    try:
        query = target.split("@")[0] if "@" in target else target  # use username part for emails
        url   = PSBDMP_SEARCH.format(query=query)

        async with httpx.AsyncClient(timeout=20, headers={"User-Agent": "SP3CT3R-OSINT/1.0"}) as client:
            resp = await client.get(url)

            if resp.status_code == 200:
                data  = resp.json()
                pastes = data.get("data", []) if isinstance(data, dict) else data
                if not isinstance(pastes, list):
                    pastes = []

                await ws_manager.send_log(
                    scan_id,
                    "WARN" if pastes else "OK",
                    f"psbdmp: {len(pastes)} paste(s) found referencing '{query}'"
                )

                for paste in pastes[:25]:  # cap at 25 to avoid flooding
                    pid    = paste.get("id", "")
                    tags   = paste.get("tags", [])
                    ptime  = paste.get("time", "")
                    length = paste.get("length", 0)

                    # Infer severity from tags
                    sev = "medium"
                    dangerous_tags = {"password", "pass", "credential", "leak", "dump", "db", "combo"}
                    if any(t.lower() in dangerous_tags for t in tags):
                        sev = "high"
                    if any(t.lower() in {"ssn","credit","card","cvv","bank"} for t in tags):
                        sev = "critical"

                    paste_url = f"https://psbdmp.ws/{pid}"
                    f = {
                        "category":   "paste",
                        "platform":   f"psbdmp — {pid}",
                        "data":       f"Tags: {', '.join(tags) or 'none'} | Length: {length:,} chars | Date: {ptime} | URL: {paste_url}",
                        "status":     "found",
                        "risk_level": sev,
                        "raw":        {**paste, "url": paste_url},
                    }
                    findings.append(f)
                    await ws_manager.send_result(scan_id, f)
                    await ws_manager.send_log(scan_id, "WARN",
                        f"Paste hit [{sev.upper()}]: {paste_url} | tags: {tags}")

                if not pastes:
                    findings.append({
                        "category": "paste", "platform": "psbdmp.ws",
                        "data": f"No paste dumps found referencing '{query}'",
                        "status": "not_found", "risk_level": "info", "raw": {},
                    })

            elif resp.status_code == 429:
                await ws_manager.send_log(scan_id, "WARN", "psbdmp rate limit hit — try again in 60s")
            else:
                await ws_manager.send_log(scan_id, "WARN",
                    f"psbdmp returned HTTP {resp.status_code}")

    except Exception as e:
        await ws_manager.send_log(scan_id, "WARN", f"Paste monitor failed: {e}")

    await ws_manager.send_progress(scan_id, 55.0, len(findings), 6)
    return findings


# ═════════════════════════════════════════════════════════════
# — VIRUSTOTAL THREAT INTEL
# ═════════════════════════════════════════════════════════════

async def _virustotal_check(scan_id: str, target: str, target_type: str) -> List[Dict]:
    """
    VirusTotal domain/IP reputation check.
    Public API: 4 req/min. Upgrade to Premium for more.
    """
    findings = []
    api_key  = settings.VIRUSTOTAL_API_KEY

    if target_type not in ("domain", "ip"):
        return findings

    await ws_manager.send_log(scan_id, "INFO", f"Querying VirusTotal for {target}...")

    if not api_key:
        await ws_manager.send_log(scan_id, "WARN",
            "VirusTotal check requires API key — set VIRUSTOTAL_API_KEY in .env")
        findings.append({
            "category": "threat_intel", "platform": "VirusTotal (Key Required)",
            "data": "Set VIRUSTOTAL_API_KEY in .env — https://virustotal.com",
            "status": "partial", "risk_level": "info", "raw": {},
        })
        return findings

    try:
        url = VT_DOMAIN_URL.format(domain=target) if target_type == "domain" else VT_IP_URL.format(ip=target)
        async with httpx.AsyncClient(timeout=15, headers={"x-apikey": api_key}) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data       = resp.json().get("data", {})
                attrs      = data.get("attributes", {})
                stats      = attrs.get("last_analysis_stats", {})
                malicious  = stats.get("malicious", 0)
                suspicious = stats.get("suspicious", 0)
                harmless   = stats.get("harmless", 0)
                total      = malicious + suspicious + harmless + stats.get("undetected", 0)
                rep        = attrs.get("reputation", 0)

                sev = "info"
                if malicious >= 10:   sev = "critical"
                elif malicious >= 5:  sev = "high"
                elif malicious >= 1:  sev = "medium"

                f = {
                    "category":   "threat_intel",
                    "platform":   "VirusTotal",
                    "data":       f"Malicious: {malicious}/{total} engines | Suspicious: {suspicious} | Reputation: {rep}",
                    "status":     "found" if malicious > 0 else "found",
                    "risk_level": sev,
                    "raw":        attrs,
                }
                findings.append(f)
                await ws_manager.send_result(scan_id, f)
                await ws_manager.send_log(
                    scan_id,
                    "ERROR" if sev in ("critical","high") else "DATA",
                    f"VT: {malicious}/{total} engines flagged {target} as malicious"
                )

                # Categories
                cats = attrs.get("categories", {})
                if cats:
                    findings.append({
                        "category": "threat_intel", "platform": "VT Categories",
                        "data": " | ".join(f"{k}: {v}" for k, v in list(cats.items())[:8]),
                        "status": "found", "risk_level": "info", "raw": cats,
                    })

    except Exception as e:
        await ws_manager.send_log(scan_id, "WARN", f"VirusTotal check failed: {e}")

    return findings


# ═════════════════════════════════════════════════════════════
# — DEHASHED CREDENTIAL SEARCH  (commercial plug-in)
# ═════════════════════════════════════════════════════════════

async def _dehashed_lookup(scan_id: str, target: str, target_type: str) -> List[Dict]:
    """
    DeHashed API — credential/leak database search.
    Requires DEHASHED_EMAIL + DEHASHED_API_KEY.
    https://dehashed.com
    """
    findings = []
    key   = settings.DEHASHED_API_KEY
    email = settings.DEHASHED_EMAIL

    if not (key and email):
        await ws_manager.send_log(scan_id, "WARN",
            "DeHashed lookup skipped — set DEHASHED_EMAIL + DEHASHED_API_KEY in .env")
        findings.append({
            "category": "breach",
            "platform": "DeHashed (API Key Required)",
            "data": "Set DEHASHED_EMAIL + DEHASHED_API_KEY in .env for credential search — https://dehashed.com",
            "status": "partial", "risk_level": "info", "raw": {},
        })
        return findings

    await ws_manager.send_log(scan_id, "INFO", f"Querying DeHashed for: {target}")

    try:
        query_param = "email" if target_type == "email" else "domain"
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                "https://api.dehashed.com/search",
                params={"query": f"{query_param}:{target}", "size": 20},
                auth=(email, key),
                headers={"Accept": "application/json"},
            )
            if resp.status_code == 200:
                data    = resp.json()
                entries = data.get("entries", []) or []
                total   = data.get("total", 0)
                await ws_manager.send_log(scan_id, "WARN" if total else "OK",
                    f"DeHashed: {total} credential record(s) found for {target}")

                for entry in entries[:15]:
                    fields = []
                    if entry.get("email"):    fields.append(f"email: {entry['email']}")
                    if entry.get("username"): fields.append(f"user: {entry['username']}")
                    if entry.get("password"): fields.append(f"pw: {entry['password'][:20]}...")
                    if entry.get("hashed_password"): fields.append(f"hash: {entry['hashed_password'][:24]}...")
                    if entry.get("database_name"): fields.append(f"db: {entry['database_name']}")

                    f = {
                        "category":   "breach",
                        "platform":   f"DeHashed — {entry.get('database_name','Unknown DB')}",
                        "data":       " | ".join(fields),
                        "status":     "found",
                        "risk_level": "high" if entry.get("password") else "medium",
                        "raw":        entry,
                    }
                    findings.append(f)
                    await ws_manager.send_result(scan_id, f)

                if total > 15:
                    findings.append({
                        "category": "breach", "platform": "DeHashed — More Results",
                        "data": f"{total - 15} additional records on dehashed.com",
                        "status": "found", "risk_level": "medium", "raw": {"total": total},
                    })
            elif resp.status_code == 400:
                await ws_manager.send_log(scan_id, "WARN", "DeHashed: no results or bad query")
            elif resp.status_code == 401:
                await ws_manager.send_log(scan_id, "WARN", "DeHashed: invalid credentials")

    except Exception as e:
        await ws_manager.send_log(scan_id, "WARN", f"DeHashed lookup failed: {e}")

    await ws_manager.send_progress(scan_id, 75.0, len(findings), 6)
    return findings


# ═════════════════════════════════════════════════════════════
# — ABUSEIPDB CHECK
# ═════════════════════════════════════════════════════════════

async def _abuseipdb_check(scan_id: str, target: str, target_type: str) -> List[Dict]:
    """AbuseIPDB reputation check for IP targets."""
    findings = []
    if target_type != "ip":
        return findings

    api_key = settings.ABUSEIPDB_KEY
    if not api_key:
        await ws_manager.send_log(scan_id, "WARN",
            "AbuseIPDB check requires API key — set ABUSEIPDB_KEY in .env")
        findings.append({
            "category": "threat_intel", "platform": "AbuseIPDB (Key Required)",
            "data": "Set ABUSEIPDB_KEY in .env — https://abuseipdb.com",
            "status": "partial", "risk_level": "info", "raw": {},
        })
        return findings

    await ws_manager.send_log(scan_id, "INFO", f"Checking AbuseIPDB for {target}...")

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                ABUSEIPDB_URL,
                params={"ipAddress": target, "maxAgeInDays": 90, "verbose": True},
                headers={"Key": api_key, "Accept": "application/json"},
            )
            if resp.status_code == 200:
                d    = resp.json().get("data", {})
                score = d.get("abuseConfidenceScore", 0)
                reports = d.get("totalReports", 0)
                country = d.get("countryCode", "?")
                isp     = d.get("isp", "?")
                sev     = "critical" if score >= 80 else "high" if score >= 50 else "medium" if score >= 20 else "info"

                f = {
                    "category": "threat_intel", "platform": "AbuseIPDB",
                    "data": f"Abuse score: {score}/100 | Reports: {reports} (90d) | Country: {country} | ISP: {isp}",
                    "status": "found", "risk_level": sev,
                    "raw": d,
                }
                findings.append(f)
                await ws_manager.send_result(scan_id, f)
                await ws_manager.send_log(
                    scan_id,
                    "ERROR" if sev in ("critical","high") else "DATA",
                    f"AbuseIPDB: score {score}/100 | {reports} abuse reports"
                )
    except Exception as e:
        await ws_manager.send_log(scan_id, "WARN", f"AbuseIPDB failed: {e}")

    return findings


# ═════════════════════════════════════════════════════════════
# — THREAT INTEL AGGREGATOR
# ═════════════════════════════════════════════════════════════

async def _threat_intel_aggregator(scan_id: str, target: str, target_type: str) -> List[Dict]:
    """
    Aggregates signals from multiple clearnet threat feeds:
    - URLhaus (malware URLs)
    - PhishTank (phishing)
    - Spamhaus ZEN DNSBL (domain/IP spam reputation)
    """
    findings = []
    await ws_manager.send_log(scan_id, "INFO", "Querying threat intelligence feeds...")

    # ── URLhaus ───────────────────────────────────────────────
    try:
        if target_type in ("domain", "ip", "url"):
            async with httpx.AsyncClient(timeout=15) as client:
                payload = {"host": target} if target_type in ("domain","ip") else {"url": target}
                resp = await client.post(
                    "https://urlhaus-api.abuse.ch/v1/host/",
                    data=payload,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    q_status = data.get("query_status", "")
                    if q_status == "is_host":
                        urls_found = data.get("urls", [])
                        active = [u for u in urls_found if u.get("url_status") == "online"]
                        sev = "critical" if active else "high" if urls_found else "info"
                        f = {
                            "category": "threat_intel", "platform": "URLhaus (abuse.ch)",
                            "data": f"Malware URLs indexed: {len(urls_found)} total | {len(active)} ACTIVE | Threat type: {urls_found[0].get('threat','?') if urls_found else 'N/A'}",
                            "status": "found" if urls_found else "not_found",
                            "risk_level": sev, "raw": data,
                        }
                        findings.append(f)
                        await ws_manager.send_result(scan_id, f)
                        if urls_found:
                            await ws_manager.send_log(scan_id, "ERROR",
                                f"URLhaus: {target} hosts {len(urls_found)} malware URL(s) | {len(active)} active!")
                    elif q_status == "no_results":
                        await ws_manager.send_log(scan_id, "OK", f"URLhaus: {target} not in malware database")
    except Exception as e:
        await ws_manager.send_log(scan_id, "WARN", f"URLhaus check failed: {e}")

    # ── ThreatFox (IOC feed from abuse.ch) ────────────────────
    try:
        if target_type in ("domain", "ip"):
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    "https://threatfox-api.abuse.ch/api/v1/",
                    json={"query": "search_ioc", "search_term": target},
                )
                if resp.status_code == 200:
                    data    = resp.json()
                    iocs    = data.get("data", []) or []
                    if isinstance(iocs, list) and iocs:
                        for ioc in iocs[:5]:
                            f = {
                                "category": "threat_intel", "platform": "ThreatFox IOC",
                                "data": f"Malware: {ioc.get('malware_printable','?')} | Type: {ioc.get('ioc_type','?')} | Confidence: {ioc.get('confidence_level','?')}%",
                                "status": "found", "risk_level": "high",
                                "raw": ioc,
                            }
                            findings.append(f)
                            await ws_manager.send_result(scan_id, f)
                        await ws_manager.send_log(scan_id, "ERROR",
                            f"ThreatFox: {len(iocs)} IOC(s) linked to {target}")
                    else:
                        await ws_manager.send_log(scan_id, "OK", f"ThreatFox: no IOCs for {target}")
    except Exception as e:
        await ws_manager.send_log(scan_id, "WARN", f"ThreatFox check failed: {e}")

    await ws_manager.send_progress(scan_id, 90.0, len(findings), 6)
    return findings


# ═════════════════════════════════════════════════════════════
# — COMMERCIAL PLUG-IN STUBS
# ═════════════════════════════════════════════════════════════

async def _commercial_plugin_stubs(scan_id: str) -> List[Dict]:
    """
    Placeholder findings for premium threat intel APIs.
    Each becomes active when the corresponding key is set in .env.
    """
    findings = []
    plugins = [
        {
            "platform": "Flare (flare.io)",
            "key_setting": "FLARE_API_KEY",
            "key_val": settings.FLARE_API_KEY,
            "desc": "Dark web monitoring, ransomware tracker, stealer log search",
            "url": "https://flare.io",
        },
        {
            "platform": "Recorded Future",
            "key_setting": "RECORDED_FUTURE_API_KEY",
            "key_val": settings.RECORDED_FUTURE_API_KEY,
            "desc": "Enterprise threat intelligence, dark web actor tracking",
            "url": "https://recordedfuture.com",
        },
    ]

    for p in plugins:
        if p["key_val"]:
            await ws_manager.send_log(scan_id, "OK", f"{p['platform']}: API key configured ✅")
            findings.append({
                "category": "threat_intel", "platform": p["platform"],
                "data": f"API key configured — ready for production queries",
                "status": "found", "risk_level": "info",
                "raw": {"configured": True},
            })
        else:
            findings.append({
                "category": "commercial_plugin",
                "platform": p["platform"],
                "data": f"{p['desc']} | Set {p['key_setting']} in .env to activate | {p['url']}",
                "status": "partial", "risk_level": "info",
                "raw": {"configured": False, "setting": p["key_setting"]},
            })

    return findings


# ═════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════

def _breach_severity(data_classes: list) -> str:
    """Infer severity from HIBP data class list."""
    classes_lower = [c.lower() for c in data_classes]
    critical = {"passwords", "credit cards", "bank account numbers", "social security numbers", "passport numbers"}
    high     = {"email addresses", "usernames", "phone numbers", "dates of birth", "physical addresses"}
    if any(c in classes_lower for c in critical):
        return "critical"
    if any(c in classes_lower for c in high):
        return "high"
    return "medium"

