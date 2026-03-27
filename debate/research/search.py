from __future__ import annotations

import asyncio
import logging
from functools import partial

from .types import SearchResult

logger = logging.getLogger(__name__)


async def web_search(query: str, *, max_results: int = 5) -> list[SearchResult]:
    """Search via DuckDuckGo. Returns empty list on failure."""
    try:
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(
            None,
            partial(_sync_search, query=query, max_results=max_results),
        )
        return [
            SearchResult(
                query=query,
                title=r.get("title", ""),
                url=r.get("href", ""),
                snippet=r.get("body", ""),
            )
            for r in results
        ]
    except Exception:
        logger.warning("DuckDuckGo search failed for query: %s", query, exc_info=True)
        return []


def _sync_search(*, query: str, max_results: int) -> list[dict]:
    from duckduckgo_search import DDGS

    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=max_results))
