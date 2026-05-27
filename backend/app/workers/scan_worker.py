"""
SP3CT3R Scan Worker
Dispatches scans to the correct service module and updates DB status
"""
import asyncio, logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.scan import ScanSession, ScanResult, ScanStatus, ScanModule, RiskLevel
from app.websocket.manager import ws_manager
from app.db.database import AsyncSessionLocal

logger = logging.getLogger("sp3ct3r.worker")


async def dispatch_scan(scan_id: str, target: str, module: ScanModule, options: dict, _db=None):
    """
    Background task: runs the appropriate OSINT service,
    persists results to DB, and updates scan status.
    """
    # Use a fresh DB session — background tasks can't share the request session
    async with AsyncSessionLocal() as db:
        try:
            # Mark as running
            result = await db.execute(select(ScanSession).where(ScanSession.id == scan_id))
            session = result.scalar_one_or_none()
            if not session:
                logger.error(f"Scan session {scan_id} not found")
                return

            session.status = ScanStatus.RUNNING
            await db.commit()

            await ws_manager.send_log(scan_id, "INFO", f"Scan {scan_id} dispatched → module: {module.value.upper()}")

            # Dispatch to correct service
            scan_result = await _run_module(scan_id, target, module, options, db)

            # Persist findings to DB
            findings = scan_result.get("results", [])
            for finding in findings:
                risk_str = finding.get("risk_level", "info")
                try:
                    risk_enum = RiskLevel(risk_str)
                except ValueError:
                    risk_enum = RiskLevel.INFO

                db_result = ScanResult(
                    scan_id=scan_id,
                    module=module,
                    category=finding.get("category", "general"),
                    platform=finding.get("platform", ""),
                    data=finding.get("data", ""),
                    status=finding.get("status", "found"),
                    risk_level=risk_enum,
                    raw=finding.get("raw", {}),
                )
                db.add(db_result)

            # Determine overall risk level
            risk_levels = [f.get("risk_level", "info") for f in findings]
            if "critical" in risk_levels: overall_risk = RiskLevel.CRITICAL
            elif "high" in risk_levels: overall_risk = RiskLevel.HIGH
            elif "medium" in risk_levels: overall_risk = RiskLevel.MEDIUM
            elif "low" in risk_levels: overall_risk = RiskLevel.LOW
            else: overall_risk = RiskLevel.INFO

            # Update session
            session.status = ScanStatus.COMPLETED
            session.progress = 100.0
            session.total_found = len([f for f in findings if f.get("status") == "found"])
            session.risk_level = overall_risk
            session.summary = scan_result.get("summary", {})
            session.completed_at = datetime.now(timezone.utc)
            await db.commit()

            logger.info(f"✅ Scan {scan_id} completed — {len(findings)} findings, risk: {overall_risk.value}")

        except Exception as e:
            logger.error(f"❌ Scan {scan_id} failed: {e}")
            try:
                result = await db.execute(select(ScanSession).where(ScanSession.id == scan_id))
                session = result.scalar_one_or_none()
                if session:
                    session.status = ScanStatus.FAILED
                    session.error_msg = str(e)
                    await db.commit()
            except Exception:
                pass
            await ws_manager.send_log(scan_id, "ERROR", f"Scan failed: {e}")


async def _run_module(scan_id: str, target: str, module: ScanModule, options: dict, db) -> dict:
    """Route to the correct service module."""
    from app.services.domain_service   import run_domain_scan
    from app.services.email_service    import run_email_scan
    from app.services.username_service import run_username_scan
    from app.services.phone_service    import run_phone_scan
    from app.services.ip_service       import run_ip_scan

    dispatch = {
        ScanModule.DOMAIN:   run_domain_scan,
        ScanModule.EMAIL:    run_email_scan,
        ScanModule.USERNAME: run_username_scan,
        ScanModule.PHONE:    run_phone_scan,
        ScanModule.IP:       run_ip_scan,
    }

    handler = dispatch.get(module)
    if not handler:
        raise ValueError(f"No handler for module: {module}")

    return await handler(scan_id, target, db, options)

