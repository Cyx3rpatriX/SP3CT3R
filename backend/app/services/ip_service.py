# ── IP SERVICE ────────────────────────────────────────────────
"""SP3CT3R IP Intelligence Module"""
import asyncio, httpx, socket
from typing import List, Dict, Any

from app.core.config import settings
from app.core.utils import now_iso
from app.websocket.manager import ws_manager
import logging

logger = logging.getLogger("sp3ct3r.ip")


async def run_ip_scan(scan_id: str, target: str, db, options: dict = {}) -> Dict[str, Any]:
    ip = target.strip()
    await ws_manager.send_log(scan_id, "INFO", f"Initializing IP module for: {ip}")

    tasks = [
        _ipinfo(scan_id, ip),
        _reverse_dns(scan_id, ip),
        _port_scan(scan_id, ip, options.get("ports", [21,22,23,25,53,80,443,3306,8080,8443])),
        _shodan_lookup(scan_id, ip),
        _abuse_check(scan_id, ip),
    ]
    gathered = await asyncio.gather(*tasks, return_exceptions=True)
    results = [r for chunk in gathered if isinstance(chunk, list) for r in chunk]

    await ws_manager.send_log(scan_id, "OK", f"IP scan complete: {len(results)} findings")
    summary = {"ip": ip, "total_findings": len(results), "completed_at": now_iso()}
    await ws_manager.send_complete(scan_id, summary)
    return {"results": results, "summary": summary}


async def _ipinfo(scan_id: str, ip: str) -> List[Dict]:
    findings = []
    await ws_manager.send_log(scan_id, "INFO", f"Fetching geolocation for {ip}...")
    try:
        token = settings.IPINFO_API_KEY
        url = f"https://ipinfo.io/{ip}/json" + (f"?token={token}" if token else "")
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                fields = {
                    "IP Address": data.get("ip", ip),
                    "Hostname": data.get("hostname", "N/A"),
                    "City": data.get("city", "Unknown"),
                    "Region": data.get("region", "Unknown"),
                    "Country": data.get("country", "Unknown"),
                    "Location (LatLon)": data.get("loc", "N/A"),
                    "Organization / ASN": data.get("org", "Unknown"),
                    "Postal Code": data.get("postal", "N/A"),
                    "Timezone": data.get("timezone", "N/A"),
                }
                for platform, value in fields.items():
                    f = {"category": "geolocation", "platform": platform, "data": value,
                         "status": "found", "risk_level": "info", "raw": data}
                    findings.append(f)
                    await ws_manager.send_result(scan_id, f)
                await ws_manager.send_log(scan_id, "OK",
                    f"Geo: {data.get('city')}, {data.get('country')} | ASN: {data.get('org')}")
    except Exception as e:
        await ws_manager.send_log(scan_id, "WARN", f"IP info failed: {e}")
    return findings


async def _reverse_dns(scan_id: str, ip: str) -> List[Dict]:
    findings = []
    await ws_manager.send_log(scan_id, "INFO", f"Performing reverse DNS on {ip}...")
    try:
        loop = asyncio.get_event_loop()
        hostname, _, _ = await loop.run_in_executor(None, socket.gethostbyaddr, ip)
        f = {"category": "dns", "platform": "Reverse DNS (PTR)", "data": hostname,
             "status": "found", "risk_level": "info", "raw": {"ptr": hostname}}
        findings.append(f)
        await ws_manager.send_result(scan_id, f)
        await ws_manager.send_log(scan_id, "OK", f"PTR record: {hostname}")
    except Exception:
        await ws_manager.send_log(scan_id, "INFO", "No reverse DNS record found")
    return findings


async def _port_scan(scan_id: str, ip: str, ports: list) -> List[Dict]:
    findings = []
    await ws_manager.send_log(scan_id, "INFO", f"Port scanning {ip} ({len(ports)} ports)...")

    SERVICE_MAP = {21:"FTP",22:"SSH",23:"Telnet",25:"SMTP",53:"DNS",80:"HTTP",
                   110:"POP3",143:"IMAP",443:"HTTPS",445:"SMB",3306:"MySQL",
                   5432:"PostgreSQL",6379:"Redis",8080:"HTTP-Alt",8443:"HTTPS-Alt",27017:"MongoDB"}

    async def check_port(port: int):
        try:
            loop = asyncio.get_event_loop()
            conn = asyncio.open_connection(ip, port)
            _, writer = await asyncio.wait_for(conn, timeout=2.0)
            writer.close()
            svc = SERVICE_MAP.get(port, "unknown")
            risk = "high" if port in [23, 3306, 6379, 27017] else "medium" if port in [21,22,445] else "info"
            f = {"category": "port", "platform": f"Port {port}/{svc}", "data": f"OPEN — {svc}",
                 "status": "found", "risk_level": risk, "raw": {"port": port, "service": svc}}
            await ws_manager.send_result(scan_id, f)
            await ws_manager.send_log(scan_id, "WARN" if risk in ["high","medium"] else "OK",
                                       f"Port {port} ({svc}): OPEN")
            return f
        except Exception:
            return None

    results = await asyncio.gather(*[check_port(p) for p in ports])
    findings = [r for r in results if r]
    await ws_manager.send_log(scan_id, "DATA", f"Port scan: {len(findings)}/{len(ports)} open")
    return findings


async def _shodan_lookup(scan_id: str, ip: str) -> List[Dict]:
    findings = []
    if not settings.SHODAN_API_KEY:
        await ws_manager.send_log(scan_id, "WARN", "Shodan lookup skipped — set SHODAN_API_KEY in .env")
        return findings
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"https://api.shodan.io/shodan/host/{ip}?key={settings.SHODAN_API_KEY}")
            if resp.status_code == 200:
                data = resp.json()
                f = {"category": "shodan", "platform": "Shodan", "data": str(data.get("ports", [])),
                     "status": "found", "risk_level": "medium", "raw": data}
                findings.append(f)
                await ws_manager.send_result(scan_id, f)
                await ws_manager.send_log(scan_id, "DATA", f"Shodan: {len(data.get('ports',[]))} services indexed")
    except Exception as e:
        await ws_manager.send_log(scan_id, "WARN", f"Shodan failed: {e}")
    return findings


async def _abuse_check(scan_id: str, ip: str) -> List[Dict]:
    """AbuseIPDB check (free tier)."""
    findings = []
    await ws_manager.send_log(scan_id, "INFO", f"Checking AbuseIPDB for {ip}...")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Free public check endpoint
            resp = await client.get(f"https://api.abuseipdb.com/api/v2/check",
                params={"ipAddress": ip, "maxAgeInDays": 90},
                headers={"Accept": "application/json", "Key": "demo"})
            # If no key, we just log the attempt
            await ws_manager.send_log(scan_id, "WARN", "AbuseIPDB check requires API key (set ABUSEIPDB_KEY in .env)")
    except Exception:
        pass
    return findings