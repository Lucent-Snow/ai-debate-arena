from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from ..config import ModelRegistry
from ..engine.arena import DebateArena
from .history import save_result

logger = logging.getLogger(__name__)


def _serialize_value(obj: Any) -> Any:
    """Convert dataclass / to_dict objects to plain dicts for JSON."""
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    return obj


def _serialize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {k: _serialize_value(v) for k, v in payload.items()}


async def websocket_endpoint(ws: WebSocket, config_path: str) -> None:
    await ws.accept()
    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type")

            if msg_type == "start_debate":
                await _run_debate(ws, msg.get("payload", msg), config_path)
            elif msg_type == "get_history":
                from .history import list_history
                await ws.send_json({"type": "history", "items": list_history()})
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.exception("WebSocket error")
        try:
            await ws.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass


async def _run_debate(ws: WebSocket, msg: dict[str, Any], config_path: str) -> None:
    mode = msg.get("mode", "1v1")
    theme = msg["theme"]
    rounds = msg.get("rounds", 3)
    pro_position = msg.get("pro_position")
    con_position = msg.get("con_position")

    registry = ModelRegistry.from_file(config_path)
    arena = DebateArena(registry=registry)

    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    def observer(event_name: str, payload: dict[str, Any]) -> None:
        queue.put_nowait({
            "type": "event",
            "event": event_name,
            "payload": _serialize_payload(payload),
        })

    async def run() -> Any:
        if mode == "4v4":
            return await arena.run_4v4(
                theme=theme,
                pro_position=pro_position,
                con_position=con_position,
                observer=observer,
            )
        return await arena.run_1v1(
            theme=theme,
            rounds=rounds,
            pro_position=pro_position,
            con_position=con_position,
            observer=observer,
        )

    task = asyncio.create_task(run())

    try:
        while not task.done():
            try:
                item = await asyncio.wait_for(queue.get(), timeout=0.5)
                await ws.send_json(item)
            except asyncio.TimeoutError:
                continue

        # Drain remaining events
        while not queue.empty():
            await ws.send_json(queue.get_nowait())

        result = task.result()
        save_result(result, mode=mode, theme=theme)
        await ws.send_json({"type": "debate_complete", "result": result.to_dict()})
    except Exception as exc:
        task.cancel()
        await ws.send_json({"type": "error", "message": str(exc)})
