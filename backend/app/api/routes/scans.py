# ── SCAN SESSION ROUTE (generic launcher) ─────────────────────
"""SP3CT3R Generic Scan Launcher + History API"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.database import get_db
from app.schemas.scan_schema import ScanRequest, ScanStartResponse, ScanSessionOut, ScanListResponse
from app.models.scan import ScanSession, ScanStatus, ScanModule
from app.core.security import generate_scan_id
from app.workers.scan_worker import dispatch_scan
from app.core.utils import now_iso
from datetime import datetime, timezone

router = APIRouter()


@router.post("/start", response_model=ScanStartResponse)
async def start_scan(req: ScanRequest, bg: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    scan_id = generate_scan_id()
    session = ScanSession(
        id=scan_id, target=req.target, module=req.module,
        status=ScanStatus.PENDING, total_sources=0,
    )
    db.add(session)
    await db.flush()

    bg.add_task(dispatch_scan, scan_id, req.target, req.module, req.options, db)

    return ScanStartResponse(
        scan_id=scan_id, target=req.target, module=req.module,
        status=ScanStatus.PENDING, message="Scan queued — connect WebSocket to stream results",
        websocket_url=f"/ws/{scan_id}",
    )


@router.get("/{scan_id}", response_model=ScanSessionOut)
async def get_scan(scan_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScanSession).where(ScanSession.id == scan_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Scan not found")
    return session


@router.get("/", response_model=ScanListResponse)
async def list_scans(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScanSession).order_by(desc(ScanSession.created_at)).limit(limit))
    scans = result.scalars().all()
    return ScanListResponse(total=len(scans), scans=scans)


@router.delete("/{scan_id}")
async def cancel_scan(scan_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScanSession).where(ScanSession.id == scan_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Scan not found")
    session.status = ScanStatus.CANCELLED
    return {"message": f"Scan {scan_id} cancelled"}