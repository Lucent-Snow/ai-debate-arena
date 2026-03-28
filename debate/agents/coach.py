from __future__ import annotations

import json
import logging

from ..prompts.templates import (
    COACH_FOUNDATION,
    build_coach_prompt,
    build_coach_synthesize_prompt,
    build_draft_strategy_prompt,
    build_extract_summary_prompt,
    build_finalize_prep_prompt,
    build_plan_research_prompt,
    build_reflect_prompt,
)
from .base import BaseAgent

logger = logging.getLogger(__name__)

_JSON_RETRY_LIMIT = 3


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

    # ── Deep research prep methods ──────────────────────────────────

    async def draft_strategy(
        self,
        *,
        theme: str,
        stance: str,
        mode: str,
        role_focus_dict: dict[int, str],
        total_rounds: int,
    ) -> str:
        system_prompt = build_draft_strategy_prompt(
            theme=theme,
            stance=stance,
            mode=mode,
            role_focus_dict=role_focus_dict,
            total_rounds=total_rounds,
        )
        resp = await self.generate(
            system_prompt=system_prompt,
            user_prompt="请输出你的初步战略方向。",
        )
        return resp.content

    async def synthesize(
        self,
        *,
        theme: str,
        stance: str,
        coach_direction: str,
        debater_drafts: str,
    ) -> str:
        """综合教练方向 + 四份辩手草稿 → 统一论证框架。"""
        system_prompt = build_coach_synthesize_prompt(
            theme=theme,
            stance=stance,
            coach_direction=coach_direction,
            debater_drafts=debater_drafts,
        )
        resp = await self.generate(
            system_prompt=system_prompt,
            user_prompt="请综合所有草稿，输出统一论证框架。",
        )
        return resp.content

    async def plan_research(
        self,
        *,
        framework: str,
        debater_suggestions: str,
        theme: str,
        stance: str,
        existing_evidence: str,
    ) -> list[dict]:
        system_prompt = build_plan_research_prompt(
            framework=framework,
            debater_suggestions=debater_suggestions,
            theme=theme,
            stance=stance,
            existing_evidence=existing_evidence,
        )
        return await self._json_with_retry(
            system_prompt=system_prompt,
            user_prompt="请输出搜索任务 JSON。",
            extract=lambda d: d.get("tasks", []),
            fallback=[],
            response_format={"type": "json_object"},
        )

    async def extract_summary(
        self,
        *,
        url_content: str,
        query: str,
        theme: str,
        stance: str,
    ) -> str:
        system_prompt = build_extract_summary_prompt(
            url_content=url_content,
            query=query,
            theme=theme,
            stance=stance,
        )
        resp = await self.generate(
            system_prompt=system_prompt,
            user_prompt="请提取相关证据摘要。",
        )
        return resp.content

    async def reflect(
        self,
        *,
        framework: str,
        evidence_so_far: str,
        theme: str,
        stance: str,
        round_num: int,
        max_rounds: int,
    ) -> bool:
        system_prompt = build_reflect_prompt(
            framework=framework,
            evidence_so_far=evidence_so_far,
            theme=theme,
            stance=stance,
            round_num=round_num,
            max_rounds=max_rounds,
        )
        return await self._json_with_retry(
            system_prompt=system_prompt,
            user_prompt="请判断是否继续搜索。",
            extract=lambda d: bool(d.get("continue", False)),
            fallback=False,
            response_format={"type": "json_object"},
        )

    async def finalize_prep(
        self,
        *,
        framework: str,
        evidence: str,
        role_focus_dict: dict[int, str],
    ) -> dict:
        system_prompt = build_finalize_prep_prompt(
            framework=framework,
            evidence=evidence,
            role_focus_dict=role_focus_dict,
        )
        return await self._json_with_retry(
            system_prompt=system_prompt,
            user_prompt="请输出弹药包 JSON。",
            extract=lambda d: d,
            fallback={"overall_strategy": framework, "debaters": []},
            response_format={"type": "json_object"},
        )

    # ── JSON retry helper ───────────────────────────────────────────

    async def _json_with_retry(
        self, *, system_prompt, user_prompt, extract, fallback, response_format
    ):
        for attempt in range(_JSON_RETRY_LIMIT):
            try:
                resp = await self.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    response_format=response_format,
                )
                parsed = json.loads(resp.content)
                return extract(parsed)
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                logger.warning(
                    "Coach %s JSON parse attempt %d failed: %s", self.id, attempt + 1, exc
                )
                # Roll back the last 3 messages (system + user + assistant) for retry
                if len(self.message_history) >= 3:
                    self.message_history = self.message_history[:-3]
                if attempt == _JSON_RETRY_LIMIT - 1:
                    logger.error("Coach %s JSON retry exhausted, using fallback", self.id)
                    return fallback
                # Append stricter instruction for retry
                system_prompt = (
                    system_prompt + "\n\n注意：你必须只输出合法 JSON，不要包含任何其他文字。"
                )
        return fallback
