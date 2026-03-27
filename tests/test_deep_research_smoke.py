"""Smoke test: verify deep research prep orchestration logic."""
from __future__ import annotations

import json
from unittest.mock import patch

from debate.config import ModelRegistry
from debate.engine.arena import DebateArena
from debate.llm import LLMResponse
from debate.models import EventType


def make_response(content: str, *, tokens_in: int = 10, tokens_out: int = 20) -> LLMResponse:
    return LLMResponse(
        content=content,
        model="mock",
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        latency_ms=100,
        raw={},
    )


call_counter = 0


async def fake_chat(*, config, messages, response_format=None):
    global call_counter
    call_counter += 1
    user_msg = messages[-1].content if messages else ""
    sys_msg = messages[0].content if messages else ""

    # Route by prompt content
    if "论证框架草案" in user_msg:
        return make_response("核心论点：1.效率 2.成本 3.规模\n预判对手：情感牌\n证据方向：行业数据")
    if "建议" in user_msg:
        return make_response("建议补充医疗行业案例")
    if "搜索任务" in user_msg:
        return make_response(json.dumps({
            "tasks": [{"query": "AI customer service statistics", "purpose": "数据支撑"}]
        }))
    if "证据摘要" in user_msg:
        return make_response("研究表明AI客服解决率达92%，来源：Gartner 2024报告")
    if "是否继续搜索" in user_msg:
        return make_response(json.dumps({"continue": False}))
    if "弹药包" in user_msg:
        return make_response(json.dumps({
            "overall_strategy": "效率+成本双线论证",
            "debaters": [
                {"position": 1, "ammo": "开篇立论：效率数据"},
                {"position": 2, "ammo": "补充：成本分析"},
                {"position": 3, "ammo": "反驳：情感论证的局限"},
                {"position": 4, "ammo": "总结：综合优势"},
            ]
        }))
    if "修订发言计划" in user_msg:
        return make_response("1.引用效率数据 2.回应情感质疑 3.强调人机协同")
    if "战术指令" in user_msg:
        return make_response("集中攻击对方数据薄弱环节")
    if "正式发言" in user_msg:
        return make_response("AI客服在标准化场景中已展现出显著优势...")
    if "JSON" in sys_msg and "裁判" in sys_msg:
        return make_response(json.dumps({
            "pro_score": 7.5, "con_score": 7.0,
            "pro_analysis": "论证有力", "con_analysis": "反驳不足",
            "key_moments": ["效率数据"], "reasoning": "正方数据更充分"
        }))
    if "总结" in sys_msg:
        return make_response("双方围绕AI客服展开了激烈辩论...")

    return make_response("默认回复")


# Patch web_search and fetch_page
async def fake_search(query, *, max_results=5):
    del max_results
    from debate.research.types import SearchResult

    return [
        SearchResult(
            query=query,
            title="AI Customer Service Report",
            url="https://example.com/report",
            snippet="AI handles 92% of queries",
        )
    ]


async def fake_fetch(url, **kwargs):
    del url, kwargs
    return "According to Gartner, AI customer service solutions resolve 92% of standard queries."


async def run_smoke() -> None:
    global call_counter
    call_counter = 0
    registry = ModelRegistry({
        "default": {
            "provider": "openai",
            "model": "mock-model",
            "base_url": "http://localhost:9999",
            "api_key": "fake",
            "temperature": 0.4,
            "max_tokens": 800,
            "timeout_seconds": 10,
            "retry_count": 1,
        },
        "overrides": {
            "research": {"temperature": 0.3, "max_tokens": 1000},
        },
        "research": {
            "max_research_rounds": 2,
            "max_total_evidence": 5,
            "webcontent_max_length": 5000,
            "per_round_timeout": 30,
            "total_prep_timeout": 120,
        },
    })

    arena = DebateArena(registry=registry)
    events_log: list[tuple[str, dict]] = []

    def observer(event_name, payload):
        events_log.append((event_name, payload))
        print(
            f"  [{event_name}]"
            f" agent={payload.get('agent_id', '?')}"
            f" side={payload.get('side', '?')}"
        )

    with (
        patch.object(arena.client, "chat", side_effect=fake_chat),
        patch("debate.engine.arena.web_search", side_effect=fake_search),
        patch("debate.engine.arena.fetch_page", side_effect=fake_fetch),
    ):
        result = await arena.run_4v4(
            theme="AI是否应该取代大部分客服岗位",
            pro_position="AI应该取代大部分客服岗位",
            con_position="AI不应该取代大部分客服岗位",
            observer=observer,
        )

    # Validate event sequence
    event_names = [e[0] for e in events_log]
    print(f"\nTotal events: {len(events_log)}")
    print(f"Total LLM calls: {call_counter}")

    # Check new event types exist
    result_event_types = {e.event_type for e in result.events}
    assert EventType.FRAMEWORK in result_event_types, "Missing FRAMEWORK events"
    assert EventType.DEBATER_SUGGESTION in result_event_types, "Missing DEBATER_SUGGESTION events"
    assert EventType.RESEARCH in result_event_types, "Missing RESEARCH events"
    assert EventType.PLAN in result_event_types, "Missing PLAN events"

    # Check event sequence: framework_ready before debater_suggestion_ready before research_ready
    fw_idx = event_names.index("framework_ready")
    ds_idx = event_names.index("debater_suggestion_ready")
    rs_idx = event_names.index("research_ready")
    pf_idx = event_names.index("prep_finalized")
    plan_indices = [i for i, n in enumerate(event_names) if n == "plan_ready"]

    assert fw_idx < ds_idx, f"framework should come before suggestion: {fw_idx} vs {ds_idx}"
    assert ds_idx < rs_idx, f"suggestion should come before research: {ds_idx} vs {rs_idx}"
    assert rs_idx < pf_idx, f"research should come before finalize: {rs_idx} vs {pf_idx}"
    assert pf_idx < plan_indices[-1], f"finalize should come before last plan: {pf_idx}"

    # Check debate still works
    assert "speech_ready" in event_names, "Missing speech events"
    assert "judging_ready" in event_names, "Missing judging events"
    assert "summary_ready" in event_names, "Missing summary events"

    # Check result structure
    assert result.mode == "4v4"
    assert len(result.events) > 0
    agent_ids = {a.id for a in result.agents}
    assert "pro_research_coach" in agent_ids, "Missing pro_research_coach in agents"
    assert "con_research_coach" in agent_ids, "Missing con_research_coach in agents"

    print("\n=== ALL CHECKS PASSED ===")
    print(f"Event sequence: {' → '.join(dict.fromkeys(event_names))}")


async def test_deep_research_smoke() -> None:
    await run_smoke()
