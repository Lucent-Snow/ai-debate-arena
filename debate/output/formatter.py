from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def render_topic(console: Console, *, theme: str, pro: str, con: str) -> None:
    table = Table(show_header=False, box=None)
    table.add_row("辩题", theme)
    table.add_row("正方", pro)
    table.add_row("反方", con)
    console.print(Panel(table, title="辩题信息"))


def render_phase(console: Console, title: str) -> None:
    console.rule(f"[bold cyan]{title}[/bold cyan]")


def render_private_block(console: Console, *, title: str, content: str) -> None:
    console.print(Panel(content, title=title))


def render_round(
    console: Console, *, round_num: int, speaker: str, model: str, content: str
) -> None:
    console.print(Panel(content, title=f"第 {round_num} 轮 | {speaker} | {model}"))


def render_summary(console: Console, content: str) -> None:
    console.print(Panel(content, title="赛后总结"))


def render_judging_summary(console: Console, *, verdict: dict) -> None:
    final = verdict["final"]
    console.print(
        Panel(
            f"胜方：{final['winner']}\n"
            f"正方总分：{final['pro_total']:.2f}\n"
            f"反方总分：{final['con_total']:.2f}",
            title="裁判结果",
        )
    )
