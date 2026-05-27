# ── MODULE-SPECIFIC ROUTES ─────────────────
"""SP3CT3R domain OSINT Route"""
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.scan_schema import ScanRequest, ScanStartResponse
from app.models.scan import ScanStatus, ScanModule
from app.core.security import generate_scan_id
from app.models.scan import ScanSession
from app.workers.scan_worker import dispatch_scan

router = APIRouter()

@router.post("/scan", response_model=ScanStartResponse)
async def scan_username(target: str, bg: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    scan_id = generate_scan_id()
    module_enum = ScanModule.USERNAME
    session = ScanSession(id=scan_id, target=target, module=module_enum, status=ScanStatus.PENDING)
    db.add(session)
    await db.flush()
    bg.add_task(dispatch_scan, scan_id, target, module_enum, {}, db)
    return ScanStartResponse(
        scan_id=scan_id, target=target, module=module_enum,
        status=ScanStatus.PENDING, message="Scan started",
        websocket_url=f"/ws/{scan_id}",
    )