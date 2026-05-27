# /backend/app/main.py
"""
	███████╗██████╗ ██████╗  ██████╗████████╗██████╗ ██████╗ 
	██╔════╝██╔══██╗╚════██╗██╔════╝╚══██╔══╝╚════██╗██╔══██╗
	███████╗██████╔╝ █████╔╝██║        ██║    █████╔╝██████╔╝
	╚════██║██╔═══╝  ╚═══██╗██║        ██║    ╚═══██╗██╔══██╗
	███████║██║     ██████╔╝╚██████╗   ██║   ██████╔╝██║  ██║
	╚══════╝╚═╝     ╚═════╝  ╚═════╝   ╚═╝   ╚═════╝ ╚═╝  ╚═╝
	                                                         
SP3CT3R — Smart Profiling & Evidence Collection Tool for Enhanced Reconnaissance
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.api.router import api_router
from app.core.config import settings
from app.db.database import init_db
from app.websocket.manager import ws_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s"
)
logger = logging.getLogger("sp3ct3r")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("🚀 SP3CT3R Engine initializing...")
    await init_db()
    logger.info("✅ Database ready")
    logger.info("✅ WebSocket manager ready")
    logger.info("✅ SP3CT3R online — all systems nominal")
    yield
    logger.info("🛑 SP3CT3R shutting down...")


app = FastAPI(
    title="Project SP3CT3R",
    description="Elite OSINT & Intelligence Gathering Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routes
app.include_router(api_router, prefix="/api/v1")

# WebSocket endpoint
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await ws_manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            await ws_manager.handle_message(client_id, data)
    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")


@app.get("/")
async def root():
    return {
        "project": "SP3CT3R",
        "status": "online",
        "version": "1.0.0",
        "modules": ["domain", "email", "username", "phone", "ip", "person"],
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "engine": "operational"}
