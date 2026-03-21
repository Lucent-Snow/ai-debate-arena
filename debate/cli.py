from __future__ import annotations

import asyncio
import sys
from typing import Any

import typer
from rich.console import Console

from .config import ModelRegistry
from .engine.arena import DebateArena
from .output.exporter import export_result
from .output.formatter import (
    render_judging_summary,
    render_phase,
    render_private_block,
    render_round,
    render_summary,
    render_topic,
)

app = typer.Typer(no_args_is_help=True)
console = Console()


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")


_configure_stdio()


def _load_arena(config: str) -> DebateArena:
    registry = ModelRegistry.from_file(config)
    return DebateArena(registry=registry)


def _default_output(theme: str, mode: str) -> str:
    return f"debate-{mode}.json"


def _winner_label(value: str) -> str:
    return {"pro": "正方", "con": "反方"}.get(value, value)


def _agent_label(agent_id: str) -> str:
    if agent_id == "pro_coach":
        return "正方教练"
    if agent_id == "con_coach":
        return "反方教练"
    if agent_id == "summarizer":
        return "总结者"
    if agent_id == "logic_judge":
        return "逻辑裁判"
    if agent_id == "persuasion_judge":
        return "说服力裁判"
    if agent_id == "clash_judge":
        return "交锋裁判"
    if agent_id.startswith("pro_debater_"):
        return f"正方{agent_id.rsplit('_', 1)[-1]}辩"
    if agent_id.startswith("con_debater_"):
        return f"反方{agent_id.rsplit('_', 1)[-1]}辩"
    return agent_id


def _observe(
    console: Console,
    *,
    show_private: bool,
    show_summary: bool,
    show_judging_details: bool,
):
    def handler(event: str, payload: dict[str, Any]) -> None:
        if event == "topic_ready":
            topic = payload["topic"]
            render_phase(console, "辩题确认")
            render_topic(console, theme=topic.theme, pro=topic.pro_position, con=topic.con_position)
        elif event == "team_strategy_ready" and show_private:
            side = "正方" if payload["side"] == "pro" else "反方"
            render_phase(console, f"{side}团队策略")
            render_private_block(console, title=f"{side}教练策略", content=payload["content"])
        elif event in {"plan_ready", "replan_ready"} and show_private:
            side = "正方" if payload["side"] == "pro" else "反方"
            round_num = payload.get("round_num")
            suffix = f"（第 {round_num} 轮后重规划）" if round_num else ""
            render_private_block(
                console,
                title=f"{side}计划 {_agent_label(payload['agent_id'])}{suffix}",
                content=payload["content"],
            )
        elif event == "round_start":
            render_phase(console, f"第 {payload['round_num']} / {payload['total_rounds']} 轮")
        elif event == "coach_instruction_ready" and show_private:
            side = "正方" if payload["side"] == "pro" else "反方"
            render_private_block(
                console,
                title=f"{side}教练指令 第 {payload['round_num']} 轮",
                content=payload["content"],
            )
        elif event == "speech_ready":
            speaker = _agent_label(payload["agent_id"])
            render_round(
                console,
                round_num=payload["round_num"],
                speaker=speaker,
                model=payload["model"],
                content=payload["content"],
            )
        elif event == "judging_ready":
            render_phase(console, "裁判评议")
            judging = payload["judging"]
            copied = {
                "scores": judging["scores"],
                "final": {
                    **judging["final"],
                    "winner": _winner_label(judging["final"]["winner"]),
                },
            }
            render_judging_summary(console, verdict=copied)
            if show_judging_details:
                for score in copied["scores"]:
                    render_private_block(
                        console,
                        title=f"{score['angle']} 细项",
                        content=(
                            f"正方：{score['pro_score']}\n"
                            f"反方：{score['con_score']}\n"
                            f"正方分析：{score['pro_analysis']}\n"
                            f"反方分析：{score['con_analysis']}\n"
                            f"关键时刻：{'；'.join(score['key_moments'])}\n"
                            f"理由：{score['reasoning']}"
                        ),
                    )
        elif event == "summary_ready" and show_summary:
            render_phase(console, "赛后总结")
            render_summary(console, payload["summary"])

    return handler


@app.command("1v1", help="运行 1v1 辩论")
def command_1v1(
    topic: str = typer.Option(..., "--topic", "--主题", help="辩题主题"),
    rounds: int = typer.Option(3, "--rounds", "--轮数", help="辩论轮数"),
    pro: str | None = typer.Option(None, "--pro", "--正方", help="正方立场，不填则自动生成"),
    con: str | None = typer.Option(None, "--con", "--反方", help="反方立场，不填则自动生成"),
    replan_after: int | None = typer.Option(
        None, "--replan-after", "--重规划轮次", help="在指定轮次后重新规划"
    ),
    config: str = typer.Option(..., "--config", "--配置", help="模型配置文件路径"),
    output: str | None = typer.Option(None, "--output", "--输出", help="结果 JSON 输出路径"),
    show_private: bool = typer.Option(
        True, "--show-private/--hide-private", "--显示内部/--隐藏内部", help="是否显示内部计划"
    ),
    show_judging_details: bool = typer.Option(
        False,
        "--show-judge-details/--hide-judge-details",
        "--显示裁判细项/--隐藏裁判细项",
        help="是否显示每位裁判的细项分析",
    ),
    show_summary: bool = typer.Option(
        True, "--show-summary/--hide-summary", "--显示总结/--隐藏总结", help="是否显示赛后总结"
    ),
) -> None:
    _configure_stdio()
    arena = _load_arena(config)
    result = asyncio.run(
        arena.run_1v1(
            theme=topic,
            rounds=rounds,
            pro_position=pro,
            con_position=con,
            replan_after=replan_after,
            observer=_observe(
                console,
                show_private=show_private,
                show_summary=show_summary,
                show_judging_details=show_judging_details,
            ),
        )
    )
    output_path = export_result(result, output or _default_output(topic, "1v1"))
    console.print(f"结果已保存到：{output_path}")


@app.command("4v4", help="运行 4v4 辩论")
def command_4v4(
    topic: str = typer.Option(..., "--topic", "--主题", help="辩题主题"),
    pro: str | None = typer.Option(None, "--pro", "--正方", help="正方立场，不填则自动生成"),
    con: str | None = typer.Option(None, "--con", "--反方", help="反方立场，不填则自动生成"),
    config: str = typer.Option(..., "--config", "--配置", help="模型配置文件路径"),
    output: str | None = typer.Option(None, "--output", "--输出", help="结果 JSON 输出路径"),
    show_private: bool = typer.Option(
        True, "--show-private/--hide-private", "--显示内部/--隐藏内部", help="是否显示内部计划"
    ),
    show_judging_details: bool = typer.Option(
        False,
        "--show-judge-details/--hide-judge-details",
        "--显示裁判细项/--隐藏裁判细项",
        help="是否显示每位裁判的细项分析",
    ),
    show_summary: bool = typer.Option(
        True, "--show-summary/--hide-summary", "--显示总结/--隐藏总结", help="是否显示赛后总结"
    ),
) -> None:
    _configure_stdio()
    arena = _load_arena(config)
    result = asyncio.run(
        arena.run_4v4(
            theme=topic,
            pro_position=pro,
            con_position=con,
            observer=_observe(
                console,
                show_private=show_private,
                show_summary=show_summary,
                show_judging_details=show_judging_details,
            ),
        )
    )
    output_path = export_result(result, output or _default_output(topic, "4v4"))
    console.print(f"结果已保存到：{output_path}")


@app.command("web", help="启动 Web 控制台")
def command_web(
    config: str = typer.Option(..., "--config", "--配置", help="模型配置文件路径"),
    port: int = typer.Option(8080, "--port", "--端口", help="服务端口"),
) -> None:
    import uvicorn

    from .server import create_app

    web_app = create_app(config_path=config)
    uvicorn.run(web_app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    app()
