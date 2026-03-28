#!/usr/bin/env python3
"""Run a real 4v4 debate with per-round judging."""
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from debate.config import ModelRegistry
from debate.engine.arena import DebateArena


def observer(event_name, payload):
    content = payload.get("content", "")
    agent = payload.get("agent_id", "?")
    side = payload.get("side", "?")
    rnd = payload.get("round_num", "")

    if event_name == "round_start":
        print(f"\n{'='*60}")
        print(f"  ⚔️  第 {rnd}/4 轮")
        print(f"{'='*60}")
    elif event_name == "speech_ready":
        short = content[:120] + "..." if len(content) > 120 else content
        label = "正方" if "pro" in agent else "反方"
        print(f"\n  🎤 {label} {agent}:")
        print(f"     {short}")
    elif event_name == "coach_instruction_ready":
        short = content[:80] + "..." if len(content) > 80 else content
        print(f"\n  📋 教练指令 ({side}): {short}")
    elif event_name == "round_judged":
        scores = payload.get("scores", [])
        for s in scores:
            print(f"  ⚖️  {s.get('angle','')}: 正方 {s.get('pro_score',0):.1f} / 反方 {s.get('con_score',0):.1f}")
            r = s.get("reasoning", "")
            if r:
                print(f"      {r[:80]}")
    elif event_name == "framework_ready":
        short = content[:100] + "..." if len(content) > 100 else content
        print(f"  🧠 框架 ({side}): {short}")
    elif event_name == "research_ready":
        title = payload.get("title", "")
        print(f"  🔍 搜索 ({side}): {title}")
    elif event_name == "prep_finalized":
        short = content[:100] + "..." if len(content) > 100 else content
        print(f"  ✅ 终稿 ({side}): {short}")
    elif event_name == "judging_ready":
        judging = payload.get("judging", {})
        final = judging.get("final", {})
        print(f"\n{'='*60}")
        print(f"  🏆 最终裁决")
        print(f"{'='*60}")
        print(f"  正方总分: {final.get('pro_total', 0):.1f}")
        print(f"  反方总分: {final.get('con_total', 0):.1f}")
        print(f"  胜方: {'正方' if final.get('winner') == 'pro' else '反方'}")
        print(f"\n  评判详情:")
        print(f"  {final.get('verdict_document', '')[:300]}")
    elif event_name == "summary_ready":
        short = content[:200] + "..." if len(content) > 200 else content
        print(f"\n  📝 总结: {short}")
    elif event_name == "plan_ready":
        short = content[:60] + "..." if len(content) > 60 else content
        print(f"  📝 辩手计划 ({side} {agent}): {short}")


async def main():
    registry = ModelRegistry.from_file("config.yaml")
    arena = DebateArena(registry=registry)

    print("🎯 辩题：现代社会更需要通才还是专才")
    print("📋 模式：4v4（含赛前深度准备 + 逐轮评分）")
    print(f"🤖 模型：{registry.default.model}")
    print()

    result = await arena.run_4v4(
        theme="现代社会更需要通才还是专才",
        pro_position="现代社会更需要通才",
        con_position="现代社会更需要专才",
        observer=observer,
    )

    # Save full result
    with open("debate_result.json", "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2, default=str)
    print(f"\n💾 完整结果已保存到 debate_result.json")


if __name__ == "__main__":
    asyncio.run(main())
