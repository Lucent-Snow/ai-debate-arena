from __future__ import annotations

from pathlib import Path

from debate.config import ModelRegistry
from debate.models import Role, Side


def test_model_registry_resolves_override_layers(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AI_DEBATE_API_KEY", "secret-key")
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "default:",
                "  provider: openai",
                "  model: qwen-plus",
                "  base_url: https://dashscope.aliyuncs.com/compatible-mode/v1",
                "  api_key: ${AI_DEBATE_API_KEY}",
                "  temperature: 0.4",
                "  max_tokens: 500",
                "overrides:",
                "  pro:",
                "    model: qwen3.5-plus",
                "  judge:",
                "    temperature: 0",
                "  pro_debater_1:",
                "    max_tokens: 700",
            ]
        ),
        encoding="utf-8",
    )

    registry = ModelRegistry.from_file(config_path)
    resolved = registry.resolve(side=Side.PRO, role=Role.JUDGE, agent_id="pro_debater_1")

    assert resolved.api_key == "secret-key"
    assert resolved.model == "qwen3.5-plus"
    assert resolved.temperature == 0
    assert resolved.max_tokens == 700
