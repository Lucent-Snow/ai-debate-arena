from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from .history import router as history_router
from .ws import websocket_endpoint


def create_app(*, config_path: str) -> FastAPI:
    app = FastAPI(title="AI Debate Arena")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.config_path = config_path

    app.include_router(history_router)

    @app.websocket("/ws")
    async def ws_endpoint(ws: WebSocket) -> None:
        await websocket_endpoint(ws, app.state.config_path)

    # Mount static files if web/dist exists
    dist_dir = Path(__file__).resolve().parent.parent.parent / "web" / "dist"
    if dist_dir.is_dir():
        from fastapi.staticfiles import StaticFiles

        app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="static")

    return app
