from __future__ import annotations

from ..models import DebateResult
from .arena import DebateArena


async def run_mode_1v1(
    arena: DebateArena,
    *,
    theme: str,
    rounds: int,
    pro_position: str | None = None,
    con_position: str | None = None,
    replan_after: int | None = None,
) -> DebateResult:
    return await arena.run_1v1(
        theme=theme,
        rounds=rounds,
        pro_position=pro_position,
        con_position=con_position,
        replan_after=replan_after,
    )
