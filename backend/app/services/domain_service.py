# ── DOMAIN SERVICE ──────────────────────────────────────────
"""
SP3CT3R Domain OSINT Module
DNS, WHOIS, Subdomains, SSL, Headers, Technologies
"""
import asyncio, socket, ssl, json, re
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.core.config import settings
from app.core.utils import sanitize_target, now_iso
from app.websocket.manager import ws_manager

logger = logging.getLogger("sp3ct3r.domain")

DNS_RECORD_TYPES = ["A", "AAAA", "MX", "TXT", "NS", "CNAME", "SOA", "CAA"]

COMMON_SUBDOMAINS = [
    "www", "mail", "ftp", "smtp", "pop", "imap", "admin", "portal", "api",
    "dev", "staging", "test", "beta", "vpn", "remote", "cdn", "static",
    "blog", "shop", "store", "app", "m", "mobile", "secure", "login",
    "webmail", "cpanel", "whm", "ns1", "ns2", "mx", "autodiscover",
    "autoconfig", "git", "gitlab", "jenkins", "jira", "confluence",
    "monitor", "status", "support", "help", "docs", "wiki",
]


async def run_domain_scan(scan_id: str, target: str, db, options: dict = {}) -> Dict[str, Any]:
    """
    Main domain scan orchestrator.
    Runs all sub-modules concurrently and streams results via WebSocket.
    """
    domain = sanitize_target(target)
    results = []

    await ws_manager.send_log(scan_id, "INFO", f"Initializing DOMAIN module for target: {domain}")
    await ws_manager.send_log(scan_id, "INFO", f"Loading {len(COMMON_SUBDOMAINS)} subdomain wordlist...")
    await ws_manager.send_progress(scan_id, 2.0, 0, len(COMMON_SUBDOMAINS))

    # Run all checks
    tasks = [
        _dns_lookup(scan_id, domain),
        _whois_lookup(scan_id, domain),
        _ssl_cert(scan_id, domain),
        _subdomain_enum(scan_id, domain),
        _http_headers(scan_id, domain),
        _ip_reputation(scan_id, domain),
    ]
    gathered = await asyncio.gather(*tasks, return_exceptions=True)

    for chunk in gathered:
        if isinstance(chunk, list):
            results.extend(chunk)
        elif isinstance(chunk, Exception):
            logger.warning(f"Task error: {chunk}")

    await ws_manager.send_progress(scan_id, 100.0, len(results), len(COMMON_SUBDOMAINS))
    await ws_manager.send_log(scan_id, "OK", f"Domain scan complete. {len(results)} findings.")

    summary = {
        "domain": domain,
        "total_findings": len(results),
        "dns_records": sum(1 for r in results if r.get("category") == "dns"),
        "subdomains": sum(1 for r in results if r.get("category") == "subdomain"),
        "completed_at": now_iso(),
    }
    await ws_manager.send_complete(scan_id, summary)
    return {"results": results, "summary": summary}


async def _dns_lookup(scan_id: str, domain: str) -> List[Dict]:
    """Resolve DNS records using Google DoH (DNS over HTTPS)."""
    findings = []
    await ws_manager.send_log(scan_id, "INFO", f"Resolving DNS records for {domain}...")

    async with httpx.AsyncClient(timeout=10) as client:
        for rtype in DNS_RECORD_TYPES:
            try:
                resp = await client.get(
                    "https://dns.google/resolve",
                    params={"name": domain, "type": rtype}
                )
                data = resp.json()
                answers = data.get("Answer", [])
                if answers:
                    for ans in answers:
                        finding = {
                            "category": "dns",
                            "platform": f"{rtype} Record",
                            "data": ans.get("data", ""),
                            "status": "found",
                            "risk_level": "info",
                            "raw": ans,
                        }
                        findings.append(finding)
                        await ws_manager.send_result(scan_id, finding)
                        await ws_manager.send_log(scan_id, "OK", f"DNS {rtype}: {ans.get('data', '')[:80]}")
            except Exception as e:
                logger.debug(f"DNS {rtype} error: {e}")
            await asyncio.sleep(0.1)

    return findings


async def _whois_lookup(scan_id: str, domain: str) -> List[Dict]:
    """WHOIS data via RDAP (modern WHOIS replacement)."""
    findings = []
    await ws_manager.send_log(scan_id, "INFO", f"Querying WHOIS/RDAP for {domain}...")

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"https://rdap.org/domain/{domain}")
            if resp.status_code == 200:
                data = resp.json()
                # Registrar
                entities = data.get("entities", [])
                for e in entities:
                    roles = e.get("roles", [])
                    vcard = e.get("vcardArray", [None, []])
                    name = next((v[3] for v in vcard[1] if v[0] == "fn"), "Unknown") if len(vcard) > 1 else "Unknown"
                    if "registrar" in roles:
                        f = {"category": "whois", "platform": "Registrar", "data": name,
                             "status": "found", "risk_level": "info", "raw": e}
                        findings.append(f)
                        await ws_manager.send_result(scan_id, f)
                # Dates
                for event in data.get("events", []):
                    action = event.get("eventAction", "")
                    date = event.get("eventDate", "")
                    if action in ["registration", "expiration", "last changed"]:
                        f = {"category": "whois", "platform": action.title(), "data": date,
                             "status": "found", "risk_level": "info", "raw": event}
                        findings.append(f)
                        await ws_manager.send_result(scan_id, f)
                # Name servers
                for ns in data.get("nameservers", []):
                    ldhName = ns.get("ldhName", "")
                    f = {"category": "whois", "platform": "Nameserver",
                         "data": ldhName, "status": "found", "risk_level": "info", "raw": ns}
                    findings.append(f)
                    await ws_manager.send_result(scan_id, f)
                await ws_manager.send_log(scan_id, "OK", f"WHOIS data retrieved via RDAP")
    except Exception as e:
        await ws_manager.send_log(scan_id, "WARN", f"WHOIS lookup failed: {e}")

    return findings


async def _ssl_cert(scan_id: str, domain: str) -> List[Dict]:
    """Fetch SSL certificate details."""
    findings = []
    await ws_manager.send_log(scan_id, "INFO", f"Fetching SSL certificate for {domain}...")

    try:
        ctx = ssl.create_default_context()
        loop = asyncio.get_event_loop()

        def _get_cert():
            conn = ctx.wrap_socket(socket.socket(), server_hostname=domain)
            conn.settimeout(10)
            conn.connect((domain, 443))
            cert = conn.getpeercert()
            conn.close()
            return cert

        cert = await loop.run_in_executor(None, _get_cert)
        issuer = dict(x[0] for x in cert.get("issuer", []))
        subject = dict(x[0] for x in cert.get("subject", []))
        not_after = cert.get("notAfter", "")
        sans = [v for k, v in cert.get("subjectAltName", [])]

        fields = [
            ("SSL Issuer", issuer.get("organizationName", "Unknown")),
            ("SSL Subject", subject.get("commonName", domain)),
            ("SSL Valid Until", not_after),
            ("SSL SANs", ", ".join(sans[:10])),
        ]
        for platform, data in fields:
            f = {"category": "ssl", "platform": platform, "data": data,
                 "status": "found", "risk_level": "info", "raw": {"issuer": issuer}}
            findings.append(f)
            await ws_manager.send_result(scan_id, f)

        await ws_manager.send_log(scan_id, "OK", f"SSL cert: valid until {not_after}")
    except Exception as e:
        await ws_manager.send_log(scan_id, "WARN", f"SSL check failed: {e}")

    return findings


async def _subdomain_enum(scan_id: str, domain: str) -> List[Dict]:
    """Enumerate subdomains using DNS brute-force."""
    findings = []
    await ws_manager.send_log(scan_id, "INFO", f"Starting subdomain enumeration ({len(COMMON_SUBDOMAINS)} probes)...")

    found_count = 0
    total = len(COMMON_SUBDOMAINS)

    async def probe(sub: str, idx: int):
        nonlocal found_count
        fqdn = f"{sub}.{domain}"
        try:
            loop = asyncio.get_event_loop()
            ip = await loop.run_in_executor(None, socket.gethostbyname, fqdn)
            found_count += 1
            risk = "high" if sub in ["admin", "dev", "staging", "test", "internal", "vpn"] else "info"
            status = "exposed" if sub in ["dev", "staging", "test"] else "found"
            f = {
                "category": "subdomain",
                "platform": f"{sub}.{domain}",
                "data": f"Resolves to: {ip}",
                "status": status,
                "risk_level": risk,
                "raw": {"subdomain": fqdn, "ip": ip},
            }
            await ws_manager.send_result(scan_id, f)
            await ws_manager.send_log(scan_id, "OK" if status == "found" else "WARN",
                                       f"{'[EXPOSED] ' if status=='exposed' else ''}{fqdn} → {ip}")
            progress = min(95.0, 10.0 + (idx / total) * 80.0)
            await ws_manager.send_progress(scan_id, progress, found_count, total)
            return f
        except socket.gaierror:
            return None
        except Exception:
            return None

    # Run in batches of 10 to avoid overwhelming DNS
    batch_size = 10
    for i in range(0, total, batch_size):
        batch = COMMON_SUBDOMAINS[i:i+batch_size]
        tasks = [probe(sub, i+j) for j, sub in enumerate(batch)]
        results = await asyncio.gather(*tasks)
        findings.extend(r for r in results if r)
        await asyncio.sleep(0.2)

    await ws_manager.send_log(scan_id, "DATA", f"Subdomain enum complete: {found_count}/{total} found")
    return findings


async def _http_headers(scan_id: str, domain: str) -> List[Dict]:
    """Grab HTTP response headers for tech fingerprinting."""
    findings = []
    await ws_manager.send_log(scan_id, "INFO", f"Fetching HTTP headers for {domain}...")

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.head(f"https://{domain}")
            interesting = ["server", "x-powered-by", "x-generator", "cf-ray",
                           "x-frame-options", "strict-transport-security", "content-security-policy"]
            for header in interesting:
                val = resp.headers.get(header)
                if val:
                    risk = "low" if header in ["x-frame-options", "strict-transport-security"] else "info"
                    f = {"category": "headers", "platform": f"Header: {header.title()}",
                         "data": val[:200], "status": "found", "risk_level": risk, "raw": {}}
                    findings.append(f)
                    await ws_manager.send_result(scan_id, f)
            await ws_manager.send_log(scan_id, "DATA", f"HTTP {resp.status_code} · {len(resp.headers)} headers")
    except Exception as e:
        await ws_manager.send_log(scan_id, "WARN", f"HTTP headers fetch failed: {e}")

    return findings


async def _ip_reputation(scan_id: str, domain: str) -> List[Dict]:
    """Check IP reputation via ipinfo.io (free tier)."""
    findings = []
    try:
        loop = asyncio.get_event_loop()
        ip = await loop.run_in_executor(None, socket.gethostbyname, domain)
        async with httpx.AsyncClient(timeout=10) as client:
            token = settings.IPINFO_API_KEY
            url = f"https://ipinfo.io/{ip}/json"
            if token:
                url += f"?token={token}"
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                fields = {
                    "IP Address": data.get("ip", ip),
                    "Geolocation": f"{data.get('city','?')}, {data.get('region','?')}, {data.get('country','?')}",
                    "ISP / ASN": data.get("org", "Unknown"),
                    "Hostname": data.get("hostname", "N/A"),
                    "Timezone": data.get("timezone", "N/A"),
                }
                for platform, value in fields.items():
                    f = {"category": "geolocation", "platform": platform,
                         "data": value, "status": "found", "risk_level": "info", "raw": data}
                    findings.append(f)
                    await ws_manager.send_result(scan_id, f)
                await ws_manager.send_log(scan_id, "OK", f"IP geo: {fields['Geolocation']} · {fields['ISP / ASN']}")
    except Exception as e:
        await ws_manager.send_log(scan_id, "WARN", f"IP reputation check failed: {e}")

    return findings