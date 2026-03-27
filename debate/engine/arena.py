from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from statistics import mean
from typing import Any

from ..agents import Coach, Debater, Judge, Summarizer
from ..config import ModelRegistry
from ..llm import LLMClient
from ..models import (
    DebateEvent,
    DebateResult,
    EventType,
    Phase,
    Role,
    Side,
    SummaryResult,
    Topic,
    Verdict,
    Visibility,
    utc_now,
)
from ..prompts.templates import JUDGE_ANGLES, topic_splitter_prompt
from ..research import Evidence, SearchTask, fetch_page, web_search
from .event_log import EventLog

logger = logging.getLogger(__name__)

ROLE_FOCUS = {
    1: "开篇立论，建立判断框架与核心论点。",
    2: "补充事实、例子和具体影响。",
    3: "集中攻击对方薄弱环节并完成反驳。",
    4: "总结收束，比较双方得失并强化胜负手。",
}


class DebateArena:
    def __init__(self, *, registry: ModelRegistry) -> None:
        self.registry = registry
        self.client = LLMClient()

    async def run_1v1(
        self,
        *,
        theme: str,
        rounds: int,
        pro_position: str | None = None,
        con_position: str | None = None,
        replan_after: int | None = None,
        observer: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> DebateResult:
        topic = await self._ensure_topic(theme, pro_position, con_position)
        log = EventLog()
        self._record_topic(log, topic)
        self._notify(observer, "topic_ready", {"topic": topic})

        pro_agent = Debater(
            id="pro_debater_1",
            role=Role.DEBATER,
            side=Side.PRO,
            position=1,
            model_config=self.registry.resolve(
                side=Side.PRO, role=self._role("debater"), agent_id="pro_debater_1"
            ),
            llm_client=self.client,
        )
        con_agent = Debater(
            id="con_debater_1",
            role=self._role("debater"),
            side=Side.CON,
            position=1,
            model_config=self.registry.resolve(
                side=Side.CON, role=self._role("debater"), agent_id="con_debater_1"
            ),
            llm_client=self.client,
        )

        pro_plan, con_plan = await asyncio.gather(
            pro_agent.plan(theme=topic.theme, stance=topic.pro_position, mode="1v1"),
            con_agent.plan(theme=topic.theme, stance=topic.con_position, mode="1v1"),
        )
        self._record(
            log,
            Phase.PREP,
            EventType.PLAN,
            pro_agent.id,
            Side.PRO,
            Visibility.PRIVATE,
            None,
            pro_plan,
            pro_agent,
        )
        self._notify(
            observer,
            "plan_ready",
            {"agent_id": pro_agent.id, "side": "pro", "content": pro_plan},
        )
        self._record(
            log,
            Phase.PREP,
            EventType.PLAN,
            con_agent.id,
            Side.CON,
            Visibility.PRIVATE,
            None,
            con_plan,
            con_agent,
        )
        self._notify(
            observer,
            "plan_ready",
            {"agent_id": con_agent.id, "side": "con", "content": con_plan},
        )

        for round_num in range(1, rounds + 1):
            self._notify(observer, "round_start", {"round_num": round_num, "total_rounds": rounds})
            transcript = log.transcript(public_only=True)
            pro_speech = await pro_agent.speak(
                mode="1v1",
                side_label="正方",
                theme=topic.theme,
                stance=topic.pro_position,
                current_round=round_num,
                total_rounds=rounds,
                plan=pro_plan,
                public_transcript=transcript,
            )
            self._record(
                log,
                Phase.DEBATE,
                EventType.SPEECH,
                pro_agent.id,
                Side.PRO,
                Visibility.PUBLIC,
                round_num,
                pro_speech,
                pro_agent,
            )
            self._notify(
                observer,
                "speech_ready",
                {
                    "round_num": round_num,
                    "agent_id": pro_agent.id,
                    "model": pro_agent.model_config.model,
                    "content": pro_speech,
                },
            )

            transcript = log.transcript(public_only=True)
            con_speech = await con_agent.speak(
                mode="1v1",
                side_label="反方",
                theme=topic.theme,
                stance=topic.con_position,
                current_round=round_num,
                total_rounds=rounds,
                plan=con_plan,
                public_transcript=transcript,
            )
            self._record(
                log,
                Phase.DEBATE,
                EventType.SPEECH,
                con_agent.id,
                Side.CON,
                Visibility.PUBLIC,
                round_num,
                con_speech,
                con_agent,
            )
            self._notify(
                observer,
                "speech_ready",
                {
                    "round_num": round_num,
                    "agent_id": con_agent.id,
                    "model": con_agent.model_config.model,
                    "content": con_speech,
                },
            )

            if replan_after and round_num == replan_after and round_num != rounds:
                transcript = log.transcript(public_only=True)
                pro_plan = await pro_agent.plan(
                    theme=topic.theme,
                    stance=topic.pro_position,
                    mode=f"1v1 replan after transcript:\n{transcript}",
                )
                con_plan = await con_agent.plan(
                    theme=topic.theme,
                    stance=topic.con_position,
                    mode=f"1v1 replan after transcript:\n{transcript}",
                )
                self._record(
                    log,
                    Phase.PREP,
                    EventType.PLAN,
                    pro_agent.id,
                    Side.PRO,
                    Visibility.PRIVATE,
                    round_num,
                    pro_plan,
                    pro_agent,
                )
                self._notify(
                    observer,
                    "replan_ready",
                    {
                        "agent_id": pro_agent.id,
                        "side": "pro",
                        "round_num": round_num,
                        "content": pro_plan,
                    },
                )
                self._record(
                    log,
                    Phase.PREP,
                    EventType.PLAN,
                    con_agent.id,
                    Side.CON,
                    Visibility.PRIVATE,
                    round_num,
                    con_plan,
                    con_agent,
                )
                self._notify(
                    observer,
                    "replan_ready",
                    {
                        "agent_id": con_agent.id,
                        "side": "con",
                        "round_num": round_num,
                        "content": con_plan,
                    },
                )

        judges, verdict = await self._judge(topic=topic, log=log)
        self._notify(observer, "judging_ready", {"judging": verdict})
        summary_agent = Summarizer(
            id="summarizer",
            role=self._role("summarizer"),
            side=Side.NEUTRAL,
            position=0,
            model_config=self.registry.resolve(
                role=self._role("summarizer"), agent_id="summarizer"
            ),
            llm_client=self.client,
        )
        summary = await summary_agent.summarize(
            theme=topic.theme,
            pro_position=topic.pro_position,
            con_position=topic.con_position,
            transcript=log.transcript(public_only=True),
        )
        self._record(
            log,
            Phase.SUMMARY,
            EventType.SUMMARY,
            "summarizer",
            Side.NEUTRAL,
            Visibility.PUBLIC,
            None,
            summary.content,
            summary_agent,
        )
        self._notify(observer, "summary_ready", {"summary": summary.content})
        return self._assemble_result(
            mode="1v1",
            topic=topic,
            log=log,
            agents=[pro_agent, con_agent, *judges, summary_agent],
            verdict=verdict,
            summary=summary,
        )

    async def run_4v4(
        self,
        *,
        theme: str,
        pro_position: str | None = None,
        con_position: str | None = None,
        observer: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> DebateResult:
        topic = await self._ensure_topic(theme, pro_position, con_position)
        log = EventLog()
        self._record_topic(log, topic)
        self._notify(observer, "topic_ready", {"topic": topic})

        pro_coach = Coach(
            id="pro_coach",
            role=self._role("coach"),
            side=Side.PRO,
            position=0,
            model_config=self.registry.resolve(
                side=Side.PRO, role=self._role("coach"), agent_id="pro_coach"
            ),
            llm_client=self.client,
        )
        con_coach = Coach(
            id="con_coach",
            role=self._role("coach"),
            side=Side.CON,
            position=0,
            model_config=self.registry.resolve(
                side=Side.CON, role=self._role("coach"), agent_id="con_coach"
            ),
            llm_client=self.client,
        )
        pro_debaters = [
            Debater(
                id=f"pro_debater_{idx}",
                role=self._role("debater"),
                side=Side.PRO,
                position=idx,
                model_config=self.registry.resolve(
                    side=Side.PRO, role=self._role("debater"), agent_id=f"pro_debater_{idx}"
                ),
                llm_client=self.client,
            )
            for idx in range(1, 5)
        ]
        con_debaters = [
            Debater(
                id=f"con_debater_{idx}",
                role=self._role("debater"),
                side=Side.CON,
                position=idx,
                model_config=self.registry.resolve(
                    side=Side.CON, role=self._role("debater"), agent_id=f"con_debater_{idx}"
                ),
                llm_client=self.client,
            )
            for idx in range(1, 5)
        ]

        # ── Deep research PREP phase ────────────────────────────────
        research_cfg = self.registry.research_config
        pro_research_coach = Coach(
            id="pro_research_coach",
            role=self._role("coach"),
            side=Side.PRO,
            position=0,
            model_config=self.registry.resolve(
                side=Side.PRO, role=self._role("coach"), agent_id="research"
            ),
            llm_client=self.client,
        )
        con_research_coach = Coach(
            id="con_research_coach",
            role=self._role("coach"),
            side=Side.CON,
            position=0,
            model_config=self.registry.resolve(
                side=Side.CON, role=self._role("coach"), agent_id="research"
            ),
            llm_client=self.client,
        )

        (pro_strategy, pro_plans), (con_strategy, con_plans) = await asyncio.gather(
            self._deep_research_prep(
                coach=pro_coach,
                research_coach=pro_research_coach,
                debaters=pro_debaters,
                side=Side.PRO,
                side_label="正方",
                topic=topic,
                stance=topic.pro_position,
                log=log,
                observer=observer,
                research_cfg=research_cfg,
            ),
            self._deep_research_prep(
                coach=con_coach,
                research_coach=con_research_coach,
                debaters=con_debaters,
                side=Side.CON,
                side_label="反方",
                topic=topic,
                stance=topic.con_position,
                log=log,
                observer=observer,
                research_cfg=research_cfg,
            ),
        )

        for round_num in range(1, 5):
            self._notify(observer, "round_start", {"round_num": round_num, "total_rounds": 4})
            pro_agent = pro_debaters[round_num - 1]
            con_agent = con_debaters[round_num - 1]
            public_transcript = log.transcript(public_only=True)

            pro_instruction, con_instruction = await asyncio.gather(
                pro_coach.instruct(
                    side_label="正方",
                    theme=topic.theme,
                    stance=topic.pro_position,
                    context_instruction=f"给第 {round_num} 位辩手制定本轮战术指令。",
                    public_transcript=public_transcript,
                    team_context=pro_strategy,
                ),
                con_coach.instruct(
                    side_label="反方",
                    theme=topic.theme,
                    stance=topic.con_position,
                    context_instruction=f"给第 {round_num} 位辩手制定本轮战术指令。",
                    public_transcript=public_transcript,
                    team_context=con_strategy,
                ),
            )
            self._record(
                log,
                Phase.PREP,
                EventType.COACH_INSTRUCTION,
                pro_coach.id,
                Side.PRO,
                Visibility.TEAM,
                round_num,
                pro_instruction,
                pro_coach,
            )
            self._notify(
                observer,
                "coach_instruction_ready",
                {
                    "round_num": round_num,
                    "agent_id": pro_coach.id,
                    "side": "pro",
                    "content": pro_instruction,
                },
            )
            self._record(
                log,
                Phase.PREP,
                EventType.COACH_INSTRUCTION,
                con_coach.id,
                Side.CON,
                Visibility.TEAM,
                round_num,
                con_instruction,
                con_coach,
            )
            self._notify(
                observer,
                "coach_instruction_ready",
                {
                    "round_num": round_num,
                    "agent_id": con_coach.id,
                    "side": "con",
                    "content": con_instruction,
                },
            )

            pro_speech = await pro_agent.speak(
                mode="4v4",
                side_label="正方",
                theme=topic.theme,
                stance=topic.pro_position,
                current_round=round_num,
                total_rounds=4,
                plan=pro_plans[round_num - 1],
                public_transcript=log.transcript(public_only=True),
                coach_instruction=pro_instruction,
                role_focus=ROLE_FOCUS[round_num],
            )
            self._record(
                log,
                Phase.DEBATE,
                EventType.SPEECH,
                pro_agent.id,
                Side.PRO,
                Visibility.PUBLIC,
                round_num,
                pro_speech,
                pro_agent,
            )
            self._notify(
                observer,
                "speech_ready",
                {
                    "round_num": round_num,
                    "agent_id": pro_agent.id,
                    "model": pro_agent.model_config.model,
                    "content": pro_speech,
                },
            )

            con_speech = await con_agent.speak(
                mode="4v4",
                side_label="反方",
                theme=topic.theme,
                stance=topic.con_position,
                current_round=round_num,
                total_rounds=4,
                plan=con_plans[round_num - 1],
                public_transcript=log.transcript(public_only=True),
                coach_instruction=con_instruction,
                role_focus=ROLE_FOCUS[round_num],
            )
            self._record(
                log,
                Phase.DEBATE,
                EventType.SPEECH,
                con_agent.id,
                Side.CON,
                Visibility.PUBLIC,
                round_num,
                con_speech,
                con_agent,
            )
            self._notify(
                observer,
                "speech_ready",
                {
                    "round_num": round_num,
                    "agent_id": con_agent.id,
                    "model": con_agent.model_config.model,
                    "content": con_speech,
                },
            )

        judges, verdict = await self._judge(topic=topic, log=log)
        self._notify(observer, "judging_ready", {"judging": verdict})
        summary_agent = Summarizer(
            id="summarizer",
            role=self._role("summarizer"),
            side=Side.NEUTRAL,
            position=0,
            model_config=self.registry.resolve(
                role=self._role("summarizer"), agent_id="summarizer"
            ),
            llm_client=self.client,
        )
        summary = await summary_agent.summarize(
            theme=topic.theme,
            pro_position=topic.pro_position,
            con_position=topic.con_position,
            transcript=log.transcript(public_only=True),
        )
        self._record(
            log,
            Phase.SUMMARY,
            EventType.SUMMARY,
            "summarizer",
            Side.NEUTRAL,
            Visibility.PUBLIC,
            None,
            summary.content,
            summary_agent,
        )
        self._notify(observer, "summary_ready", {"summary": summary.content})
        return self._assemble_result(
            mode="4v4",
            topic=topic,
            log=log,
            agents=[
                pro_coach, con_coach,
                pro_research_coach, con_research_coach,
                *pro_debaters, *con_debaters,
                *judges, summary_agent,
            ],
            verdict=verdict,
            summary=summary,
        )

    async def _deep_research_prep(
        self,
        *,
        coach: Coach,
        research_coach: Coach,
        debaters: list[Debater],
        side: Side,
        side_label: str,
        topic: Topic,
        stance: str,
        log: EventLog,
        observer: Callable[[str, dict[str, Any]], None] | None,
        research_cfg: Any,
    ) -> tuple[str, list[str]]:
        """Deep research prep: framework → suggestions → research → finalize → revise."""
        side_val = side.value
        prep_start = time.monotonic()

        # Step 1: Coach drafts framework
        framework = await coach.draft_strategy(
            theme=topic.theme,
            stance=stance,
            mode="4v4",
            role_focus_dict=ROLE_FOCUS,
            total_rounds=4,
        )
        self._record(
            log, Phase.PREP, EventType.FRAMEWORK, coach.id, side,
            Visibility.TEAM, None, framework, coach,
        )
        self._notify(observer, "framework_ready", {
            "agent_id": coach.id, "side": side_val, "content": framework,
        })

        # Step 1b: Debaters suggest
        suggestions = await asyncio.gather(*[
            d.suggest(
                coach_strategy=framework,
                theme=topic.theme,
                stance=stance,
                position=d.position,
                role_focus=ROLE_FOCUS[d.position],
            )
            for d in debaters
        ])
        for d, sug in zip(debaters, suggestions, strict=True):
            self._record(
                log, Phase.PREP, EventType.DEBATER_SUGGESTION, d.id, side,
                Visibility.TEAM, None, sug, d,
            )
            self._notify(observer, "debater_suggestion_ready", {
                "agent_id": d.id, "side": side_val, "content": sug,
            })

        debater_suggestions_text = "\n".join(
            f"{d.position}号辩手：{sug}" for d, sug in zip(debaters, suggestions, strict=True)
        )

        # Step 2: Iterative research loop
        evidence_list: list[Evidence] = []
        seen_queries: set[str] = set()

        for rnd in range(1, research_cfg.max_research_rounds + 1):
            if time.monotonic() - prep_start >= research_cfg.total_prep_timeout:
                logger.info("Side %s: total prep timeout reached", side_val)
                break

            evidence_text = self._format_evidence(evidence_list)

            # Plan research tasks
            try:
                tasks_raw = await asyncio.wait_for(
                    research_coach.plan_research(
                        framework=framework,
                        debater_suggestions=debater_suggestions_text,
                        theme=topic.theme,
                        stance=stance,
                        existing_evidence=evidence_text,
                    ),
                    timeout=research_cfg.per_round_timeout,
                )
            except asyncio.TimeoutError:
                logger.warning("Side %s: plan_research timeout at round %d", side_val, rnd)
                break

            new_tasks = [
                SearchTask(query=t["query"], purpose=t.get("purpose", ""))
                for t in tasks_raw
                if isinstance(t, dict) and t.get("query") and t["query"] not in seen_queries
            ]
            if not new_tasks:
                break
            for t in new_tasks:
                seen_queries.add(t.query)

            # Execute searches
            for task in new_tasks:
                if len(evidence_list) >= research_cfg.max_total_evidence:
                    break
                if time.monotonic() - prep_start >= research_cfg.total_prep_timeout:
                    break

                results = await web_search(task.query, max_results=5)
                for sr in results[:3]:
                    if len(evidence_list) >= research_cfg.max_total_evidence:
                        break

                    page_content = await fetch_page(
                        sr.url,
                        jina_api_key=research_cfg.jina_api_key,
                        max_length=research_cfg.webcontent_max_length,
                    )

                    if page_content:
                        summary = await research_coach.extract_summary(
                            url_content=page_content,
                            query=task.query,
                            theme=topic.theme,
                            stance=stance,
                        )
                        # Retry with shorter content if summary too short
                        if len(summary) < 20 and page_content:
                            truncated = page_content[:int(len(page_content) * 0.7)]
                            summary = await research_coach.extract_summary(
                                url_content=truncated,
                                query=task.query,
                                theme=topic.theme,
                                stance=stance,
                            )
                    else:
                        summary = ""

                    # Fallback to snippet
                    if not summary or len(summary) < 10:
                        summary = sr.snippet

                    if summary and summary != "无相关内容":
                        ev = Evidence(
                            query=task.query,
                            url=sr.url,
                            title=sr.title,
                            summary=summary,
                            snippet=sr.snippet,
                        )
                        evidence_list.append(ev)
                        self._record(
                            log, Phase.PREP, EventType.RESEARCH, research_coach.id, side,
                            Visibility.TEAM, None, summary, research_coach,
                            extra_metadata={"url": sr.url, "title": sr.title, "query": task.query},
                        )
                        self._notify(observer, "research_ready", {
                            "agent_id": research_coach.id, "side": side_val,
                            "content": summary,
                            "url": sr.url, "title": sr.title, "query": task.query,
                        })

            # Reflect: continue?
            if rnd < research_cfg.max_research_rounds:
                try:
                    should_continue = await asyncio.wait_for(
                        research_coach.reflect(
                            framework=framework,
                            evidence_so_far=self._format_evidence(evidence_list),
                            theme=topic.theme,
                            stance=stance,
                            round_num=rnd,
                            max_rounds=research_cfg.max_research_rounds,
                        ),
                        timeout=research_cfg.per_round_timeout,
                    )
                except asyncio.TimeoutError:
                    break
                if not should_continue:
                    break

        # Step 3: Finalize + revise
        evidence_text = self._format_evidence(evidence_list)
        prep_result = await coach.finalize_prep(
            framework=framework,
            evidence=evidence_text,
            role_focus_dict=ROLE_FOCUS,
        )
        overall_strategy = prep_result.get("overall_strategy", framework)
        debater_ammos = prep_result.get("debaters", [])

        # Record finalized framework
        self._record(
            log, Phase.PREP, EventType.FRAMEWORK, coach.id, side,
            Visibility.TEAM, None, overall_strategy, coach,
        )
        self._notify(observer, "prep_finalized", {
            "agent_id": coach.id, "side": side_val, "content": overall_strategy,
        })

        # Build ammo lookup
        ammo_by_pos: dict[int, str] = {}
        for item in debater_ammos:
            if isinstance(item, dict):
                ammo_by_pos[item.get("position", 0)] = item.get("ammo", "")

        # Debaters revise plans
        plans = await asyncio.gather(*[
            d.revise(
                framework=overall_strategy,
                evidence=evidence_text,
                ammo=ammo_by_pos.get(d.position, overall_strategy),
                theme=topic.theme,
                stance=stance,
                position=d.position,
                role_focus=ROLE_FOCUS[d.position],
            )
            for d in debaters
        ])
        for d, plan in zip(debaters, plans, strict=True):
            self._record(
                log, Phase.PREP, EventType.PLAN, d.id, side,
                Visibility.PRIVATE, None, plan, d,
            )
            self._notify(observer, "plan_ready", {
                "agent_id": d.id, "side": side_val, "content": plan,
            })

        return overall_strategy, list(plans)

    @staticmethod
    def _format_evidence(evidence_list: list[Evidence]) -> str:
        if not evidence_list:
            return ""
        parts = []
        for i, ev in enumerate(evidence_list, 1):
            parts.append(f"[{i}] {ev.title} ({ev.url})\n{ev.summary}")
        return "\n\n".join(parts)

    async def _ensure_topic(
        self,
        theme: str,
        pro_position: str | None,
        con_position: str | None,
    ) -> Topic:
        if pro_position and con_position:
            return Topic(theme=theme, pro_position=pro_position, con_position=con_position)
        generator = Debater(
            id="topic_splitter",
            role=self._role("debater"),
            side=Side.NEUTRAL,
            position=0,
            model_config=self.registry.resolve(agent_id="topic_splitter"),
            llm_client=self.client,
        )
        response = await generator.generate(
            system_prompt="你只允许输出合法 JSON，且所有文本必须是中文。",
            user_prompt=topic_splitter_prompt(theme),
            response_format={"type": "json_object"},
        )
        payload = self.client.parse_json_content(response)
        return Topic(
            theme=theme, pro_position=payload["pro_position"], con_position=payload["con_position"]
        )

    async def _judge(self, *, topic: Topic, log: EventLog) -> tuple[list[Judge], dict[str, Any]]:
        transcript = log.transcript(public_only=True)
        judges: list[Judge] = []
        for agent_id in JUDGE_ANGLES:
            judge = Judge(
                id=agent_id,
                role=self._role("judge"),
                side=Side.NEUTRAL,
                position=0,
                model_config=self.registry.resolve(role=self._role("judge"), agent_id=agent_id),
                llm_client=self.client,
            )
            judges.append(judge)
        scores = await asyncio.gather(
            *[
                judge.score(
                    angle_name=JUDGE_ANGLES[judge.id][0],
                    angle_description=JUDGE_ANGLES[judge.id][1],
                    theme=topic.theme,
                    pro_position=topic.pro_position,
                    con_position=topic.con_position,
                    transcript=transcript,
                )
                for judge in judges
            ]
        )
        for judge, score in zip(judges, scores, strict=True):
            self._record(
                log,
                Phase.JUDGE,
                EventType.JUDGE_SCORE,
                judge.id,
                Side.NEUTRAL,
                Visibility.PUBLIC,
                None,
                score.reasoning,
                judge,
                extra_metadata=score.to_dict(),
            )
        pro_total = mean(score.pro_score for score in scores)
        con_total = mean(score.con_score for score in scores)
        winner = "pro" if pro_total >= con_total else "con"
        verdict_document = "\n\n".join(
            [
                (
                    f"{score.angle}: Pro {score.pro_score:.1f} / "
                    f"Con {score.con_score:.1f}\n{score.reasoning}"
                )
                for score in scores
            ]
        )
        verdict = Verdict(
            pro_total=pro_total,
            con_total=con_total,
            winner=winner,
            verdict_document=verdict_document,
        )
        return judges, {"scores": [score.to_dict() for score in scores], "final": verdict.to_dict()}

    def _assemble_result(
        self,
        *,
        mode: str,
        topic: Topic,
        log: EventLog,
        agents: list[Any],
        verdict: dict[str, Any],
        summary: SummaryResult,
    ) -> DebateResult:
        agent_descriptors = [agent.descriptor for agent in agents]
        per_agent_stats = {agent.id: agent.stats.to_dict() for agent in agents}
        total_tokens = sum(
            stat["tokens_in"] + stat["tokens_out"] for stat in per_agent_stats.values()
        )
        total_duration = sum(stat["duration_seconds"] for stat in per_agent_stats.values())
        return DebateResult(
            version="1.0",
            mode=mode,
            topic=topic,
            config={"models": self.registry.export()},
            agents=agent_descriptors,
            events=log.events,
            judging=verdict,
            summary=summary,
            stats={
                "total_tokens": total_tokens,
                "total_cost_usd": 0.0,
                "total_duration_seconds": round(total_duration, 3),
                "per_agent_stats": per_agent_stats,
            },
        )

    def _record_topic(self, log: EventLog, topic: Topic) -> None:
        log.add(
            DebateEvent(
                timestamp=utc_now(),
                phase=Phase.SETUP,
                event_type=EventType.TOPIC,
                agent_id="system",
                side=Side.NEUTRAL,
                visibility=Visibility.PUBLIC,
                round_num=None,
                content=(
                    f"辩题：{topic.theme}\n正方：{topic.pro_position}\n反方：{topic.con_position}"
                ),
                metadata={},
            )
        )

    @staticmethod
    def _notify(
        observer: Callable[[str, dict[str, Any]], None] | None,
        event: str,
        payload: dict[str, Any],
    ) -> None:
        if observer:
            observer(event, payload)

    def _record(
        self,
        log: EventLog,
        phase: Phase,
        event_type: EventType,
        agent_id: str,
        side: Side,
        visibility: Visibility,
        round_num: int | None,
        content: str,
        agent: Any,
        extra_metadata: dict[str, Any] | None = None,
    ) -> None:
        metadata = {
            "model": agent.model_config.model,
            "calls": agent.stats.calls,
            "tokens_in": agent.stats.tokens_in,
            "tokens_out": agent.stats.tokens_out,
            "duration_seconds": round(agent.stats.duration_seconds, 3),
        }
        if extra_metadata:
            metadata.update(extra_metadata)
        log.add(
            DebateEvent(
                timestamp=utc_now(),
                phase=phase,
                event_type=event_type,
                agent_id=agent_id,
                side=side,
                visibility=visibility,
                round_num=round_num,
                content=content,
                metadata=metadata,
            )
        )

    @staticmethod
    def _role(name: str):
        mapping = {
            "debater": Role.DEBATER,
            "coach": Role.COACH,
            "judge": Role.JUDGE,
            "summarizer": Role.SUMMARIZER,
        }
        return mapping[name]
