from __future__ import annotations

import os
from pathlib import Path

import pytest

from debate.config import ModelRegistry
from debate.engine.arena import DebateArena


def build_registry(tmp_path: Path) -> ModelRegistry:
    base_url = os.environ.get("AI_DEBATE_BASE_URL")
    api_key = os.environ.get("AI_DEBATE_API_KEY")
    model = os.environ.get("AI_DEBATE_MODEL")
    if not (base_url and api_key and model):
        pytest.skip("Live API environment variables are not configured.")
    config_path = tmp_path / "live-config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "default:",
                "  provider: openai",
                f"  model: {model}",
                f"  base_url: {base_url}",
                f"  api_key: {api_key}",
                "  temperature: 0.3",
                "  max_tokens: 220",
                "  timeout_seconds: 90",
                "  retry_count: 2",
                "overrides:",
                "  judge:",
                "    temperature: 0",
                "    max_tokens: 800",
                "  summarizer:",
                "    temperature: 0.2",
                "    max_tokens: 500",
                "  coach:",
                "    max_tokens: 180",
            ]
        ),
        encoding="utf-8",
    )
    return ModelRegistry.from_file(config_path)


@pytest.mark.live
@pytest.mark.asyncio
async def test_run_1v1_end_to_end(tmp_path: Path) -> None:
    arena = DebateArena(registry=build_registry(tmp_path))
    result = await arena.run_1v1(
        theme="AI should replace most customer service jobs",
        rounds=1,
        pro_position="AI should replace most customer service jobs",
        con_position="AI should not replace most customer service jobs",
    )

    assert result.mode == "1v1"
    assert len([event for event in result.events if event.event_type.value == "SPEECH"]) == 2
    assert len(result.judging["scores"]) == 3
    assert result.summary.content


@pytest.mark.live
@pytest.mark.slow
@pytest.mark.asyncio
async def test_run_4v4_end_to_end(tmp_path: Path) -> None:
    arena = DebateArena(registry=build_registry(tmp_path))
    result = await arena.run_4v4(
        theme="Open source software is better than commercial software",
        pro_position="Open source software is better than commercial software",
        con_position="Commercial software is better than open source software",
    )

    assert result.mode == "4v4"
    assert len([event for event in result.events if event.event_type.value == "SPEECH"]) == 8
    assert any(event.event_type.value == "COACH_INSTRUCTION" for event in result.events)
    assert result.summary.content
