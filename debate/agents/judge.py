from __future__ import annotations

import json

from ..llm import LLMClient
from ..models import JudgeScore
from ..prompts.templates import build_judge_prompt
from .base import BaseAgent


class Judge(BaseAgent):
    async def score(
        self,
        *,
        angle_name: str,
        angle_description: str,
        theme: str,
        pro_position: str,
        con_position: str,
        transcript: str,
    ) -> JudgeScore:
        system_prompt = build_judge_prompt(
            angle_name=angle_name,
            angle_description=angle_description,
            theme=theme,
            pro_position=pro_position,
            con_position=con_position,
            transcript=transcript,
        )
        response = await self.generate(
            system_prompt=system_prompt,
            user_prompt="请完成评分。",
            response_format={"type": "json_object"},
        )
        try:
            payload = LLMClient.parse_json_content(response)
        except json.JSONDecodeError:
            fallback_prompt = (
                f"你是 {angle_name}。请重新评分，并且只输出合法 JSON。\n"
                f"维度说明：{angle_description}\n"
                f"辩题：{theme}\n"
                f"正方立场：{pro_position}\n"
                f"反方立场：{con_position}\n"
                f"辩论记录：\n{transcript}\n"
                "字段只允许有 pro_score、con_score、pro_analysis、con_analysis、"
                "key_moments、reasoning。所有内容必须使用中文。"
                "两边分析各不超过 50 字，reasoning 不超过 40 字，key_moments 仅保留 2 条短句。"
            )
            repaired = await self.generate(
                system_prompt="你只允许输出合法 JSON。",
                user_prompt=fallback_prompt,
                response_format={"type": "json_object"},
            )
            payload = LLMClient.parse_json_content(repaired)
        return JudgeScore(
            judge=self.id,
            angle=angle_name,
            pro_score=float(payload["pro_score"]),
            con_score=float(payload["con_score"]),
            pro_analysis=payload["pro_analysis"],
            con_analysis=payload["con_analysis"],
            key_moments=list(payload["key_moments"]),
            reasoning=payload["reasoning"],
        )
