python3 << 'PYEOF'
import os

base = "/home/claude/Project_Sp3ct3r/backend/app/api/routes"
modules = ["domain", "email", "username", "phone", "ip"]
module_enums = {"domain": "DOMAIN", "email": "EMAIL", "username": "USERNAME", "phone": "PHONE", "ip": "IP"}

for m in modules:
    content = f'''"""SP3CT3R {m.title()} OSINT Route"""
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.scan_schema import ScanStartResponse
from app.models.scan import ScanStatus, ScanModule, ScanSession
from app.core.security import generate_scan_id
from app.workers.scan_worker import dispatch_scan

router = APIRouter()

@router.post("/scan", response_model=ScanStartResponse)
async def scan_{m}(target: str, bg: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    scan_id = generate_scan_id()
    module_enum = ScanModule.{module_enums[m]}
    session = ScanSession(id=scan_id, target=target, module=module_enum, status=ScanStatus.PENDING)
    db.add(session)
    await db.flush()
    bg.add_task(dispatch_scan, scan_id, target, module_enum, {{}}, db)
    return ScanStartResponse(
        scan_id=scan_id, target=target, module=module_enum,
        status=ScanStatus.PENDING, message="Scan started",
        websocket_url=f"/ws/{{scan_id}}",
    )
'''
    path = os.path.join(base, f"{m}.py")
    with open(path, "w") as f:
        f.write(content)
    print(f"✅ routes/{m}.py")

# __init__ files
for d in [
    "/home/claude/Project_Sp3ct3r/backend/app",
    "/home/claude/Project_Sp3ct3r/backend/app/api",
    "/home/claude/Project_Sp3ct3r/backend/app/api/routes",
    "/home/claude/Project_Sp3ct3r/backend/app/core",
    "/home/claude/Project_Sp3ct3r/backend/app/services",
    "/home/claude/Project_Sp3ct3r/backend/app/models",
    "/home/claude/Project_Sp3ct3r/backend/app/db",
    "/home/claude/Project_Sp3ct3r/backend/app/schemas",
    "/home/claude/Project_Sp3ct3r/backend/app/websocket",
    "/home/claude/Project_Sp3ct3r/backend/app/workers",
    "/home/claude/Project_Sp3ct3r/backend/app/middleware",
    "/home/claude/Project_Sp3ct3r/backend/app/cache",
]:
    init = os.path.join(d, "__init__.py")
    if not os.path.exists(init):
        open(init, "w").close()

print("✅ All __init__.py files created")
PYEOF