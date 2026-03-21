from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Side(str, Enum):
    PRO = "pro"
    CON = "con"
    NEUTRAL = "neutral"


class Role(str, Enum):
    DEBATER = "debater"
    COACH = "coach"
    JUDGE = "judge"
    SUMMARIZER = "summarizer"


class Phase(str, Enum):
    SETUP = "SETUP"
    PREP = "PREP"
    DEBATE = "DEBATE"
    JUDGE = "JUDGE"
    SUMMARY = "SUMMARY"


class EventType(str, Enum):
    TOPIC = "TOPIC"
    PLAN = "PLAN"
    SPEECH = "SPEECH"
    COACH_INSTRUCTION = "COACH_INSTRUCTION"
    TEAM_DISCUSSION = "TEAM_DISCUSSION"
    JUDGE_SCORE = "JUDGE_SCORE"
    SUMMARY = "SUMMARY"


class Visibility(str, Enum):
    PUBLIC = "PUBLIC"
    TEAM = "TEAM"
    PRIVATE = "PRIVATE"


@dataclass(slots=True)
class Message:
    role: str
    content: str


@dataclass(slots=True)
class Topic:
    theme: str
    pro_position: str
    con_position: str


@dataclass(slots=True)
class ModelConfig:
    provider: str
    model: str
    base_url: str
    api_key: str
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout_seconds: float = 120.0
    retry_count: int = 2


@dataclass(slots=True)
class AgentDescriptor:
    id: str
    role: Role
    side: Side
    position: int
    model: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role.value,
            "side": self.side.value,
            "position": self.position,
            "model": self.model,
        }


@dataclass(slots=True)
class DebateEvent:
    timestamp: datetime
    phase: Phase
    event_type: EventType
    agent_id: str
    side: Side
    visibility: Visibility
    round_num: int | None
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "phase": self.phase.value,
            "event_type": self.event_type.value,
            "agent_id": self.agent_id,
            "side": self.side.value,
            "visibility": self.visibility.value,
            "round_num": self.round_num,
            "content": self.content,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class JudgeScore:
    judge: str
    angle: str
    pro_score: float
    con_score: float
    pro_analysis: str
    con_analysis: str
    key_moments: list[str]
    reasoning: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Verdict:
    pro_total: float
    con_total: float
    winner: str
    verdict_document: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SummaryResult:
    content: str
    agent_id: str
    model: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AgentStats:
    calls: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    duration_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DebateResult:
    version: str
    mode: str
    topic: Topic
    config: dict[str, Any]
    agents: list[AgentDescriptor]
    events: list[DebateEvent]
    judging: dict[str, Any]
    summary: SummaryResult
    stats: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "mode": self.mode,
            "topic": asdict(self.topic),
            "config": self.config,
            "agents": [agent.to_dict() for agent in self.agents],
            "events": [event.to_dict() for event in self.events],
            "judging": self.judging,
            "summary": self.summary.to_dict(),
            "stats": self.stats,
        }
