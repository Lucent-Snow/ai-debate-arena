from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from ..models import DebateResult

router = APIRouter(prefix="/api")

HISTORY_DIR = Path.home() / ".debate-arena" / "history"


def _sanitize(text: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff-]", "_", text)[:40]


def save_result(result: DebateResult, *, mode: str, theme: str) -> Path:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    from ..models import utc_now
    ts = utc_now().strftime("%Y%m%d_%H%M%S")
    filename = f"{ts}_{mode}_{_sanitize(theme)}.json"
    path = HISTORY_DIR / filename
    path.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def list_history() -> list[dict[str, Any]]:
    if not HISTORY_DIR.exists():
        return []
    items: list[dict[str, Any]] = []
    for f in sorted(HISTORY_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            winner = data.get("judging", {}).get("final", {}).get("winner", "")
            items.append({
                "filename": f.name,
                "mode": data.get("mode", ""),
                "theme": data.get("topic", {}).get("theme", ""),
                "date": f.name[:15],  # 20260321_120000
                "winner": winner,
            })
        except Exception:
            continue
    return items


@router.get("/history")
async def get_history() -> list[dict[str, Any]]:
    return list_history()


@router.get("/history/{filename}")
async def get_history_detail(filename: str) -> dict[str, Any]:
    path = HISTORY_DIR / filename
    if not path.exists() or not path.is_file():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found")
    return json.loads(path.read_text(encoding="utf-8"))
