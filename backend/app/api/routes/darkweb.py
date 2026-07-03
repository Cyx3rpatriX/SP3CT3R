"""SP3CT3R — Dark Web OSINT API Routes"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.schemas.scan_schema import ScanStartResponse
from app.models.scan import ScanSession, ScanStatus, ScanModule
from app.core.security import generate_scan_id
from app.workers.scan_worker import dispatch_scan

router = APIRouter()


@router.post("/scan", response_model=ScanStartResponse)
async def scan_darkweb(
    target: str,
    bg: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Launch a Dark Web intelligence scan.
    Accepts: email, domain, IP address, or keyword.
    """
    scan_id = generate_scan_id()
    session = ScanSession(
        id=scan_id,
        target=target,
        module=ScanModule.DARKWEB,
        status=ScanStatus.PENDING,
        total_sources=0,
    )
    db.add(session)
    await db.flush()
    await db.commit()

    bg.add_task(dispatch_scan, scan_id, target, "darkweb", {})

    return ScanStartResponse(
        scan_id=scan_id,
        target=target,
        module=ScanModule.DARKWEB,
        status=ScanStatus.PENDING,
        message="Dark web scan queued — connect WebSocket for live results",
        websocket_url=f"/ws/{scan_id}",
    )


@router.get("/tor-status")
async def tor_status():
    """Quick check: is local Tor daemon running?"""
    import socket
    from app.core.config import settings
    try:
        s = socket.socket()
        s.settimeout(2)
        result = s.connect_ex((settings.TOR_SOCKS_HOST, settings.TOR_SOCKS_PORT))
        s.close()
        return {
            "tor_available": result == 0,
            "host": settings.TOR_SOCKS_HOST,
            "port": settings.TOR_SOCKS_PORT,
        }
    except Exception as e:
        return {"tor_available": False, "error": str(e)}



