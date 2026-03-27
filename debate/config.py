from __future__ import annotations

import os
import re
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from .models import ModelConfig, Role, Side
from .research.types import ResearchConfig

ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


def expand_env(value: Any) -> Any:
    if isinstance(value, str):

        def replace(match: re.Match[str]) -> str:
            key = match.group(1)
            return os.environ.get(key, "")

        return ENV_PATTERN.sub(replace, value)
    if isinstance(value, list):
        return [expand_env(item) for item in value]
    if isinstance(value, dict):
        return {key: expand_env(item) for key, item in value.items()}
    return value


def load_yaml_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    return expand_env(raw)


class ModelRegistry:
    def __init__(self, payload: dict[str, Any]) -> None:
        if "default" not in payload:
            raise ValueError("Config file must define a default model.")
        self.payload = payload
        self.default = ModelConfig(**payload["default"])
        self.overrides = payload.get("overrides", {})

    @classmethod
    def from_file(cls, path: str | Path) -> ModelRegistry:
        return cls(load_yaml_config(path))

    def resolve(
        self,
        *,
        side: Side | None = None,
        role: Role | None = None,
        agent_id: str | None = None,
    ) -> ModelConfig:
        merged = asdict(self.default)
        if side and side.value in self.overrides:
            merged.update(self.overrides[side.value])
        if role and role.value in self.overrides:
            merged.update(self.overrides[role.value])
        if agent_id and agent_id in self.overrides:
            merged.update(self.overrides[agent_id])
        return ModelConfig(**merged)

    def export(self) -> dict[str, Any]:
        payload = deepcopy(self.payload)
        self._redact_secrets(payload)
        return payload

    @classmethod
    def _redact_secrets(cls, value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"api_key", "jina_api_key"} and item:
                    value[key] = "***"
                    continue
                cls._redact_secrets(item)
        elif isinstance(value, list):
            for item in value:
                cls._redact_secrets(item)

    @property
    def research_config(self) -> ResearchConfig:
        raw = self.payload.get("research", {})
        if not raw:
            return ResearchConfig()
        fields = {f.name for f in ResearchConfig.__dataclass_fields__.values()}
        filtered = {k: v for k, v in raw.items() if k in fields}
        return ResearchConfig(**filtered)
