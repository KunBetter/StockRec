import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()


class WSManager:
    def __init__(self):
        self.active: list[WebSocket] = []
        self._subscribed_symbols: dict[WebSocket, set] = {}

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        self._subscribed_symbols[ws] = set()

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)
        self._subscribed_symbols.pop(ws, None)

    async def broadcast(self, data: dict):
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                self.disconnect(ws)


ws_manager = WSManager()


@router.websocket("/ws/prices")
async def websocket_prices(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            # Client can send subscribe/unsubscribe messages
            try:
                msg = json.loads(data)
                action = msg.get("action")
                symbols = msg.get("symbols", [])
                if action == "subscribe":
                    ws_manager._subscribed_symbols[ws].update(symbols)
                elif action == "unsubscribe":
                    ws_manager._subscribed_symbols[ws].difference_update(symbols)
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
