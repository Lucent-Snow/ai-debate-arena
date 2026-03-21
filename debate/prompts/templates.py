from __future__ import annotations

JUDGE_ANGLES: dict[str, tuple[str, str]] = {
    "logic_judge": ("逻辑裁判", "关注论证结构、逻辑一致性、谬误识别与证据质量。"),
    "persuasion_judge": ("说服力裁判", "关注表达清晰度、修辞效果、受众影响与情绪感染力。"),
    "clash_judge": ("交锋裁判", "关注正反双方是否正面回应、反驳质量和临场调整能力。"),
}


def topic_splitter_prompt(theme: str) -> str:
    return (
        "你是辩题设计助手。请根据给定主题生成两个尽可能对立、但都可辩护的立场。"
        "只允许输出 JSON，并且对象中只能包含 pro_position 与 con_position 两个字段。"
        "所有输出必须使用中文。\n"
        f"主题：{theme}"
    )


def build_debater_prompt(
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
    if mode == "4v4":
        coach_part = coach_instruction or "本轮暂无额外教练指令。"
        return (
            f"你是 4v4 辩论中 {side_label} 方的第 {current_round} 位辩手。\n"
            f"辩题：{theme}\n"
            f"你方立场：{stance}\n"
            f"你的职责重点：{role_focus or '与团队整体策略保持一致。'}\n"
            f"教练给你的本轮指令：{coach_part}\n"
            f"你的私有准备笔记：\n{plan}\n"
            f"当前公开辩论记录：\n{public_transcript}\n"
            "请直接输出本轮发言，不要写标题，不要解释，不要暴露你的内部计划。"
            "必须使用中文，尽量有交锋感，控制在 300 字以内。"
        )
    return (
        "你是一名正式辩论中的竞争型辩手。\n"
        f"辩题：{theme}\n"
        f"你所属的一方：{side_label}\n"
        f"你的立场：{stance}\n"
        f"当前轮次：第 {current_round} / {total_rounds} 轮\n"
        f"你的私有计划：\n{plan}\n"
        f"当前公开辩论记录：\n{public_transcript}\n"
        "请直接给出下一段辩论发言。必须回应对手最近的关键点，并补充己方论证。"
        "必须使用中文，不要写标题，控制在 300 字以内。"
    )


def build_coach_prompt(
    *,
    side_label: str,
    theme: str,
    stance: str,
    context_instruction: str,
    public_transcript: str,
    team_context: str,
) -> str:
    return (
        f"你是 4v4 辩论中 {side_label} 方的教练。\n"
        f"辩题：{theme}\n"
        f"你方立场：{stance}\n"
        f"当前任务：{context_instruction}\n"
        f"内部团队信息：\n{team_context}\n"
        f"公开辩论记录：\n{public_transcript}\n"
        "请给出明确、可执行、针对性强的战术指令。所有输出必须使用中文，并尽量简洁。"
    )


def build_judge_prompt(
    *,
    angle_name: str,
    angle_description: str,
    theme: str,
    pro_position: str,
    con_position: str,
    transcript: str,
) -> str:
    return (
        f"你是一名辩论裁判，评判维度是：{angle_name}。\n"
        f"{angle_description}\n"
        f"辩题：{theme}\n"
        f"正方立场：{pro_position}\n"
        f"反方立场：{con_position}\n"
        f"完整公开辩论记录：\n{transcript}\n"
        "请只输出 JSON，字段为 pro_score、con_score、pro_analysis、con_analysis、"
        "key_moments、reasoning。所有分析必须使用中文。"
        "两边分析各不超过 80 字，reasoning 不超过 60 字，key_moments 最多 2 条短句。"
    )


def build_summarizer_prompt(
    *, theme: str, pro_position: str, con_position: str, transcript: str
) -> str:
    return (
        "你是一名中立的辩论总结者。\n"
        f"辩题：{theme}\n"
        f"正方立场：{pro_position}\n"
        f"反方立场：{con_position}\n"
        f"完整公开辩论记录：\n{transcript}\n"
        "请用中文输出总结，覆盖核心分歧、双方论证地图、综合洞见、"
        "尚未解决的问题、现实启示。不要选边站。"
    )
