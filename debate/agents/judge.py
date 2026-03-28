from __future__ import annotations

import json

from ..llm import LLMClient
from ..models import JudgeScore
from ..prompts.templates import build_judge_prompt, build_judge_round_prompt
from .base import BaseAgent


class Judge(BaseAgent):
    async def score_round(
        self,
        *,
        angle_name: str,
        angle_description: str,
        theme: str,
        pro_position: str,
        con_position: str,
        round_num: int,
        total_rounds: int,
        pro_speech: str,
        con_speech: str,
        transcript_so_far: str,
    ) -> JudgeScore:
        """逐轮评分：分析本轮攻防，给出本轮得分。"""
        system_prompt = build_judge_round_prompt(
            angle_name=angle_name,
            angle_description=angle_description,
            theme=theme,
            pro_position=pro_position,
            con_position=con_position,
            round_num=round_num,
            total_rounds=total_rounds,
            pro_speech=pro_speech,
            con_speech=con_speech,
            transcript_so_far=transcript_so_far,
        )
        response = await self.generate(
            system_prompt=system_prompt,
            user_prompt="请完成本轮评分。",
            response_format={"type": "json_object"},
        )
        return self._parse_score(response, angle_name)

    async def score_final(
        self,
        *,
        angle_name: str,
        angle_description: str,
        theme: str,
        pro_position: str,
        con_position: str,
        transcript: str,
        round_scores: list[dict],
    ) -> JudgeScore:
        """最终评分：综合所有轮次得分，给出最终裁决和深度分析。"""
        round_summary = "\n".join(
            f"第{s.get('round', '?')}轮: 正方 {s.get('pro_score', 0):.1f} / 反方 {s.get('con_score', 0):.1f} — {s.get('reasoning', '')}"
            for s in round_scores
        )
        pro_total = sum(s.get("pro_score", 0) for s in round_scores)
        con_total = sum(s.get("con_score", 0) for s in round_scores)

        system_prompt = (
            f"{build_judge_prompt.__module__}"  # placeholder, use actual prompt below
        )
        system_prompt = build_judge_prompt(
            angle_name=angle_name,
            angle_description=angle_description,
            theme=theme,
            pro_position=pro_position,
            con_position=con_position,
            transcript=transcript,
        )
        # Inject round accumulation info
        system_prompt += (
            f"\n\n以下是各轮逐轮评分记录（供参考）：\n{round_summary}\n"
            f"各轮累计：正方 {pro_total:.1f} / 反方 {con_total:.1f}\n\n"
            "你的最终评分应基于全程表现，可以对累计分做修正（如有某轮的战术价值在全局视角下需要重新评估）。\n"
            "但修正应有明确理由。"
        )
        response = await self.generate(
            system_prompt=system_prompt,
            user_prompt="请完成最终评分。",
            response_format={"type": "json_object"},
        )
        return self._parse_score(response, angle_name)

    def _parse_score(self, response, angle_name: str) -> JudgeScore:
        try:
            payload = LLMClient.parse_json_content(response)
        except json.JSONDecodeError:
            # Minimal fallback
            payload = {
                "pro_score": 5.0,
                "con_score": 5.0,
                "pro_analysis": "解析失败",
                "con_analysis": "解析失败",
                "key_moments": [],
                "reasoning": "JSON 解析失败，使用默认评分",
            }
        return JudgeScore(
            judge=self.id,
            angle=angle_name,
            pro_score=float(payload.get("pro_score", 5)),
            con_score=float(payload.get("con_score", 5)),
            pro_analysis=payload.get("pro_analysis", ""),
            con_analysis=payload.get("con_analysis", ""),
            key_moments=list(payload.get("key_moments", [])),
            reasoning=payload.get("reasoning", ""),
        )
