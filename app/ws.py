from __future__ import annotations

import asyncio
import json
from typing import Set

from fastapi import WebSocket

from app.services.db_session import DBSession

# Simple in-memory set of connected driver websockets. This is intentionally
# lightweight: for a production system you'd use a broker (Redis) to fan-out.
_drivers: Set[WebSocket] = set()


async def register_driver(ws: WebSocket) -> None:
    _drivers.add(ws)


def unregister_driver(ws: WebSocket) -> None:
    _drivers.discard(ws)


async def broadcast_open_rides(message: dict) -> None:
    payload = json.dumps(message)
    coros = []
    for ws in list(_drivers):
        coros.append(_safe_send(ws, payload))
    if coros:
        await asyncio.gather(*coros)


async def _safe_send(ws: WebSocket, payload: str) -> None:
    try:
        await ws.send_text(payload)
    except Exception:
        unregister_driver(ws)
