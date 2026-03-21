from __future__ import annotations

import json
from dataclasses import dataclass
from time import perf_counter
from typing import Any

import httpx

from .models import Message, ModelConfig


@dataclass(slots=True)
class LLMResponse:
    content: str
    model: str
    tokens_in: int
    tokens_out: int
    latency_ms: int
    raw: dict[str, Any]


class LLMClient:
    async def chat(
        self,
        *,
        config: ModelConfig,
        messages: list[Message],
        response_format: dict[str, Any] | None = None,
    ) -> LLMResponse:
        start = perf_counter()
        if config.provider == "anthropic":
            payload = await self._call_anthropic(config, messages)
        else:
            payload = await self._call_openai_compatible(config, messages, response_format)
        latency_ms = int((perf_counter() - start) * 1000)
        usage = payload.get("usage", {})
        message = payload["choices"][0]["message"]
        return LLMResponse(
            content=message.get("content", "").strip(),
            model=payload.get("model", config.model),
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
            latency_ms=latency_ms,
            raw=payload,
        )

    async def _call_openai_compatible(
        self,
        config: ModelConfig,
        messages: list[Message],
        response_format: dict[str, Any] | None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": config.model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(
            base_url=config.base_url.rstrip("/"),
            timeout=config.timeout_seconds,
        ) as client:
            response = await client.post("/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def _call_anthropic(self, config: ModelConfig, messages: list[Message]) -> dict[str, Any]:
        system_messages = [msg.content for msg in messages if msg.role == "system"]
        body = {
            "model": config.model,
            "system": "\n\n".join(system_messages),
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in messages
                if msg.role != "system"
            ],
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }
        headers = {
            "x-api-key": config.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        async with httpx.AsyncClient(
            base_url=config.base_url.rstrip("/"),
            timeout=config.timeout_seconds,
        ) as client:
            response = await client.post("/v1/messages", headers=headers, json=body)
            response.raise_for_status()
            payload = response.json()
        text = "".join(block.get("text", "") for block in payload.get("content", []))
        usage = payload.get("usage", {})
        return {
            "model": payload.get("model", config.model),
            "choices": [{"message": {"content": text}}],
            "usage": {
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
            },
            "raw_anthropic": payload,
        }

    @staticmethod
    def parse_json_content(response: LLMResponse) -> dict[str, Any]:
        return json.loads(response.content)
