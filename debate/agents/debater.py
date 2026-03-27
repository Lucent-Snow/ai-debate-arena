from __future__ import annotations

from ..prompts.templates import (
    build_debater_prompt,
    build_debater_revise_prompt,
    build_debater_suggest_prompt,
)
from .base import BaseAgent


class Debater(BaseAgent):
    async def plan(self, *, theme: str, stance: str, mode: str) -> str:
        system_prompt = (
            "你是辩手的私有策略助手。请输出 3 条简洁要点，全部使用中文，"
            "不要写开场白，也不要写 Markdown 标题。"
        )
        user_prompt = (
            f"模式：{mode}\n"
            f"辩题：{theme}\n"
            f"你的立场：{stance}\n"
            "请覆盖：核心论点、预判对手、发言重点。"
        )
        return (await self.generate(system_prompt=system_prompt, user_prompt=user_prompt)).content

    async def speak(
        self,
        *,
        mode: str,
        side_label: str,
        theme: str,
        stance: str,
        current_round: int,
        total_rounds: int,
        plan: str,
        public_transcript: str,
        coach_instruction: str | None = None,
        role_focus: str | None = None,
    ) -> str:
        system_prompt = build_debater_prompt(
            mode=mode,
            side_label=side_label,
            theme=theme,
            stance=stance,
            current_round=current_round,
            total_rounds=total_rounds,
            plan=plan,
            public_transcript=public_transcript,
            coach_instruction=coach_instruction,
            role_focus=role_focus,
        )
        user_prompt = "请给出你的本轮正式发言。"
        return (await self.generate(system_prompt=system_prompt, user_prompt=user_prompt)).content

    # ── Deep research prep methods ──────────────────────────────────

    async def suggest(
        self,
        *,
        coach_strategy: str,
        theme: str,
        stance: str,
        position: int,
        role_focus: str,
    ) -> str:
        system_prompt = build_debater_suggest_prompt(
            coach_strategy=coach_strategy,
            theme=theme,
            stance=stance,
            position=position,
            role_focus=role_focus,
        )
        resp = await self.generate(
            system_prompt=system_prompt,
            user_prompt="请给出你的建议。",
        )
        return resp.content

    async def revise(
        self,
        *,
        framework: str,
        evidence: str,
        ammo: str,
        theme: str,
        stance: str,
        position: int,
        role_focus: str,
    ) -> str:
        system_prompt = build_debater_revise_prompt(
            framework=framework,
            evidence=evidence,
            ammo=ammo,
            theme=theme,
            stance=stance,
            position=position,
            role_focus=role_focus,
        )
        resp = await self.generate(
            system_prompt=system_prompt,
            user_prompt="请输出你的修订发言计划。",
        )
        return resp.content
