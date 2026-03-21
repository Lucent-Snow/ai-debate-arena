from __future__ import annotations

from ..models import SummaryResult
from ..prompts.templates import build_summarizer_prompt
from .base import BaseAgent


class Summarizer(BaseAgent):
    async def summarize(
        self,
        *,
        theme: str,
        pro_position: str,
        con_position: str,
        transcript: str,
    ) -> SummaryResult:
        system_prompt = build_summarizer_prompt(
            theme=theme,
            pro_position=pro_position,
            con_position=con_position,
            transcript=transcript,
        )
        response = await self.generate(system_prompt=system_prompt, user_prompt="请输出最终总结。")
        return SummaryResult(content=response.content, agent_id=self.id, model=response.model)
