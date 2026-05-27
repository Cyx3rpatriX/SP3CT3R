"""
SP3CT3R WebSocket Manager
Handles live scan streaming to frontend clients
"""
from fastapi import WebSocket
from typing import Dict, Set
import json, logging
from datetime import datetime, timezone

logger = logging.getLogger("sp3ct3r.ws")


class WebSocketManager:
    def __init__(self):
        # client_id -> WebSocket
        self.active: Dict[str, WebSocket] = {}
        # scan_id -> set of client_ids watching it
        self.scan_subscribers: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active[client_id] = websocket
        logger.info(f"[WS] Client connected: {client_id}")
        await self.send_to(client_id, {
            "type": "connected",
            "data": {"client_id": client_id, "message": "SP3CT3R WebSocket ready"}
        })

    def disconnect(self, client_id: str):
        self.active.pop(client_id, None)
        for subscribers in self.scan_subscribers.values():
            subscribers.discard(client_id)
        logger.info(f"[WS] Client disconnected: {client_id}")

    async def handle_message(self, client_id: str, raw: str):
        """Handle incoming WS messages (e.g. subscribe to a scan)."""
        try:
            msg = json.loads(raw)
            if msg.get("type") == "subscribe" and "scan_id" in msg:
                scan_id = msg["scan_id"]
                if scan_id not in self.scan_subscribers:
                    self.scan_subscribers[scan_id] = set()
                self.scan_subscribers[scan_id].add(client_id)
                logger.info(f"[WS] {client_id} subscribed to scan {scan_id}")
        except json.JSONDecodeError:
            pass

    async def send_to(self, client_id: str, payload: dict):
        """Send a message to a specific client."""
        ws = self.active.get(client_id)
        if ws:
            try:
                await ws.send_text(json.dumps(payload))
            except Exception as e:
                logger.warning(f"[WS] Failed to send to {client_id}: {e}")
                self.disconnect(client_id)

    async def broadcast_scan(self, scan_id: str, payload: dict):
        """Broadcast a scan update to all subscribers of that scan."""
        payload["timestamp"] = datetime.now(timezone.utc).isoformat()
        payload["scan_id"] = scan_id
        subscribers = self.scan_subscribers.get(scan_id, set())
        dead = set()
        for client_id in subscribers:
            ws = self.active.get(client_id)
            if ws:
                try:
                    await ws.send_text(json.dumps(payload))
                except Exception:
                    dead.add(client_id)
        for d in dead:
            self.disconnect(d)

    async def send_log(self, scan_id: str, level: str, message: str):
        """Convenience: push a terminal log line."""
        await self.broadcast_scan(scan_id, {
            "type": "log",
            "data": {"level": level, "message": message}
        })

    async def send_result(self, scan_id: str, result: dict):
        """Convenience: push a new finding."""
        await self.broadcast_scan(scan_id, {
            "type": "result",
            "data": result
        })

    async def send_progress(self, scan_id: str, progress: float, found: int, total: int):
        """Convenience: update progress bar."""
        await self.broadcast_scan(scan_id, {
            "type": "progress",
            "data": {"progress": progress, "found": found, "total": total}
        })

    async def send_complete(self, scan_id: str, summary: dict):
        """Convenience: mark scan as complete."""
        await self.broadcast_scan(scan_id, {
            "type": "complete",
            "data": summary
        })


# Global singleton
ws_manager = WebSocketManager()

