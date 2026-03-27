from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)


async def fetch_page(
    url: str,
    *,
    jina_api_key: str = "",
    max_length: int = 15000,
    timeout: float = 30.0,
    retries: int = 3,
) -> str:
    """Fetch page content via Jina Reader. Returns empty string on failure."""
    headers: dict[str, str] = {"Accept": "text/markdown"}
    if jina_api_key:
        headers["Authorization"] = f"Bearer {jina_api_key}"

    jina_url = f"https://r.jina.ai/{url}"

    for attempt in range(1, retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(jina_url, headers=headers)
                resp.raise_for_status()
                text = resp.text
                if len(text) > max_length:
                    text = text[:max_length]
                return text
        except Exception:
            if attempt == retries:
                logger.warning("Jina Reader failed for %s after %d attempts", url, retries)
                return ""
            logger.debug("Jina Reader attempt %d failed for %s, retrying", attempt, url)
    return ""
