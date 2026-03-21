from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..llm import LLMClient, LLMResponse
from ..models import AgentDescriptor, AgentStats, Message, ModelConfig, Role, Side


@dataclass(slots=True)
class BaseAgent:
    id: str
    role: Role
    side: Side
    position: int
    model_config: ModelConfig
    llm_client: LLMClient
    message_history: list[Message] = field(default_factory=list)
    stats: AgentStats = field(default_factory=AgentStats)

    @property
    def descriptor(self) -> AgentDescriptor:
        return AgentDescriptor(
            id=self.id,
            role=self.role,
            side=self.side,
            position=self.position,
            model=self.model_config.model,
        )

    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_format: dict[str, Any] | None = None,
    ) -> LLMResponse:
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_prompt),
        ]
        last_error: Exception | None = None
        for _ in range(max(1, self.model_config.retry_count)):
            try:
                response = await self.llm_client.chat(
                    config=self.model_config,
                    messages=messages,
                    response_format=response_format,
                )
                break
            except Exception as exc:  # noqa: BLE001
                last_error = exc
        else:
            raise RuntimeError(f"{self.id} failed to generate a response") from last_error
        self.stats.calls += 1
        self.stats.tokens_in += response.tokens_in
        self.stats.tokens_out += response.tokens_out
        self.stats.duration_seconds += response.latency_ms / 1000
        self.message_history.extend(messages)
        self.message_history.append(Message(role="assistant", content=response.content))
        return response
