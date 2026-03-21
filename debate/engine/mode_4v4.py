from __future__ import annotations

from ..models import DebateResult
from .arena import DebateArena


async def run_mode_4v4(
    arena: DebateArena,
    *,
    theme: str,
    pro_position: str | None = None,
    con_position: str | None = None,
) -> DebateResult:
    return await arena.run_4v4(
        theme=theme,
        pro_position=pro_position,
        con_position=con_position,
    )
