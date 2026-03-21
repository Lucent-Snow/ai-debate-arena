from __future__ import annotations

from dataclasses import dataclass, field

from ..models import DebateEvent, Side, Visibility


@dataclass(slots=True)
class EventLog:
    events: list[DebateEvent] = field(default_factory=list)

    def add(self, event: DebateEvent) -> None:
        self.events.append(event)

    def public_events(self) -> list[DebateEvent]:
        return [event for event in self.events if event.visibility == Visibility.PUBLIC]

    def visible_to(self, *, agent_id: str, side: Side) -> list[DebateEvent]:
        visible: list[DebateEvent] = []
        for event in self.events:
            if event.visibility == Visibility.PUBLIC:
                visible.append(event)
            elif event.visibility == Visibility.TEAM and event.side == side:
                visible.append(event)
            elif event.visibility == Visibility.PRIVATE and event.agent_id == agent_id:
                visible.append(event)
        return visible

    def transcript(self, *, public_only: bool = True) -> str:
        source = self.public_events() if public_only else self.events
        lines = []
        for event in source:
            round_tag = f"Round {event.round_num}" if event.round_num else event.phase.value
            lines.append(f"[{round_tag}] {event.agent_id}: {event.content}")
        return "\n".join(lines) if lines else "No prior debate content."
