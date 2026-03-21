from __future__ import annotations

import os

import pytest

from debate.llm import LLMClient
from debate.models import Message, ModelConfig


def build_live_config() -> ModelConfig:
    base_url = os.environ.get("AI_DEBATE_BASE_URL")
    api_key = os.environ.get("AI_DEBATE_API_KEY")
    model = os.environ.get("AI_DEBATE_MODEL")
    if not (base_url and api_key and model):
        pytest.skip("Live API environment variables are not configured.")
    return ModelConfig(
        provider="openai",
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=0,
        max_tokens=80,
        timeout_seconds=60,
        retry_count=2,
    )


@pytest.mark.live
@pytest.mark.asyncio
async def test_llm_client_returns_json_content() -> None:
    client = LLMClient()
    response = await client.chat(
        config=build_live_config(),
        messages=[
            Message(role="system", content="Return valid JSON only."),
            Message(
                role="user",
                content='Output {"status":"ok","kind":"json"} exactly as valid JSON.',
            ),
        ],
        response_format={"type": "json_object"},
    )

    payload = LLMClient.parse_json_content(response)
    assert payload["status"] == "ok"
    assert payload["kind"] == "json"
    assert response.model
