from __future__ import annotations

from ..prompts.templates import build_coach_prompt
from .base import BaseAgent


class Coach(BaseAgent):
    async def instruct(
        self,
        *,
        side_label: str,
        theme: str,
        stance: str,
        context_instruction: str,
        public_transcript: str,
        team_context: str,
    ) -> str:
        system_prompt = build_coach_prompt(
            side_label=side_label,
            theme=theme,
            stance=stance,
            context_instruction=context_instruction,
            public_transcript=public_transcript,
            team_context=team_context,
        )
        response = await self.generate(
            system_prompt=system_prompt,
            user_prompt="请给出你的战术指令。",
        )
        return response.content
