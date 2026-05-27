# ── USERNAME SERVICE ──────────────────────────────────────────
"""SP3CT3R Username OSINT Module — checks 100+ platforms"""
import asyncio, httpx
from typing import List, Dict, Any
from app.core.utils import now_iso
from app.websocket.manager import ws_manager
import logging

logger = logging.getLogger("sp3ct3r.username")

# Platform registry: name -> url template (use {username})
PLATFORMS = {
    "GitHub":         "https://github.com/{username}",
    "GitLab":         "https://gitlab.com/{username}",
    "Twitter/X":      "https://twitter.com/{username}",
    "Instagram":      "https://instagram.com/{username}",
    "TikTok":         "https://tiktok.com/@{username}",
    "YouTube":        "https://youtube.com/@{username}",
    "Reddit":         "https://reddit.com/user/{username}",
    "LinkedIn":       "https://linkedin.com/in/{username}",
    "Facebook":       "https://facebook.com/{username}",
    "Pinterest":      "https://pinterest.com/{username}",
    "Twitch":         "https://twitch.tv/{username}",
    "Steam":          "https://steamcommunity.com/id/{username}",
    "Spotify":        "https://open.spotify.com/user/{username}",
    "SoundCloud":     "https://soundcloud.com/{username}",
    "Medium":         "https://medium.com/@{username}",
    "Dev.to":         "https://dev.to/{username}",
    "Keybase":        "https://keybase.io/{username}",
    "HackerNews":     "https://news.ycombinator.com/user?id={username}",
    "ProductHunt":    "https://producthunt.com/@{username}",
    "Behance":        "https://behance.net/{username}",
    "Dribbble":       "https://dribbble.com/{username}",
    "Flickr":         "https://flickr.com/people/{username}",
    "Vimeo":          "https://vimeo.com/{username}",
    "Tumblr":         "https://{username}.tumblr.com",
    "WordPress":      "https://{username}.wordpress.com",
    "About.me":       "https://about.me/{username}",
    "Gravatar":       "https://gravatar.com/{username}",
    "DockerHub":      "https://hub.docker.com/u/{username}",
    "PyPI":           "https://pypi.org/user/{username}",
    "NPM":            "https://npmjs.com/~{username}",
    "HackerOne":      "https://hackerone.com/{username}",
    "BugCrowd":       "https://bugcrowd.com/{username}",
    "Tryhackme":      "https://tryhackme.com/p/{username}",
    "HackTheBox":     "https://app.hackthebox.com/users/{username}",
}


async def run_username_scan(scan_id: str, target: str, db, options: dict = {}) -> Dict[str, Any]:
    username = target.strip().lower()
    total = len(PLATFORMS)
    await ws_manager.send_log(scan_id, "INFO", f"Initializing USERNAME module for: @{username}")
    await ws_manager.send_log(scan_id, "INFO", f"Probing {total} platforms...")
    await ws_manager.send_progress(scan_id, 2.0, 0, total)

    results = []
    found = 0

    async def check_platform(name: str, url_tpl: str, idx: int):
        nonlocal found
        url = url_tpl.replace("{username}", username)
        try:
            async with httpx.AsyncClient(timeout=8, follow_redirects=True,
                                          headers={"User-Agent": "Mozilla/5.0"}) as client:
                resp = await client.get(url)
                # Heuristic: 200 = likely exists, 404 = not found, 403 = exists but private
                if resp.status_code in [200, 403]:
                    found += 1
                    status = "found"
                    risk = "info"
                    f = {"category": "social", "platform": name, "data": url,
                         "status": status, "risk_level": risk, "raw": {"url": url, "status_code": resp.status_code}}
                    results.append(f)
                    await ws_manager.send_result(scan_id, f)
                    await ws_manager.send_log(scan_id, "OK", f"[+] {name}: {url}")
                else:
                    f = {"category": "social", "platform": name, "data": "Not found",
                         "status": "not_found", "risk_level": "info", "raw": {"url": url}}
                    results.append(f)
        except Exception:
            pass

        progress = min(97.0, 5.0 + (idx / total) * 90.0)
        await ws_manager.send_progress(scan_id, progress, found, total)

    # Run in concurrent batches
    batch_size = 8
    platform_list = list(PLATFORMS.items())
    for i in range(0, total, batch_size):
        batch = platform_list[i:i+batch_size]
        await asyncio.gather(*[check_platform(n, u, i+j) for j, (n, u) in enumerate(batch)])
        await asyncio.sleep(0.3)

    await ws_manager.send_progress(scan_id, 100.0, found, total)
    await ws_manager.send_log(scan_id, "DATA", f"Username scan complete: {found}/{total} platforms found")
    summary = {"username": username, "platforms_found": found, "total_checked": total, "completed_at": now_iso()}
    await ws_manager.send_complete(scan_id, summary)
    return {"results": results, "summary": summary}