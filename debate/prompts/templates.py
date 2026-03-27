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


# ── Deep research prep prompts ──────────────────────────────────────


def build_draft_strategy_prompt(
    *,
    theme: str,
    stance: str,
    mode: str,
    role_focus_dict: dict[int, str],
    total_rounds: int,
) -> str:
    roles = "\n".join(f"  {k}号辩手：{v}" for k, v in role_focus_dict.items())
    return (
        f"你是 {mode} 辩论中一方的教练。\n"
        f"辩题：{theme}\n"
        f"你方立场：{stance}\n"
        f"共 {total_rounds} 轮，每轮一位辩手发言。\n"
        f"辩手分工：\n{roles}\n\n"
        "请输出一份论证框架草案，包含：\n"
        "1. 核心论点（3-5条）\n"
        "2. 预判对手可能的攻击方向\n"
        "3. 每位辩手的重点任务\n"
        "4. 需要搜索补充的证据方向\n"
        "全部使用中文，不要写标题或开场白。"
    )


def build_debater_suggest_prompt(
    *,
    coach_strategy: str,
    theme: str,
    stance: str,
    position: int,
    role_focus: str,
) -> str:
    return (
        f"你是辩论队的 {position} 号辩手。\n"
        f"辩题：{theme}\n"
        f"你方立场：{stance}\n"
        f"你的职责：{role_focus}\n"
        f"教练的论证框架草案：\n{coach_strategy}\n\n"
        "请从你的角色出发，给教练提 1-2 条简短建议（每条不超过 100 字），"
        "可以是补充论点、需要搜索的证据、或对框架的修改意见。"
        "直接输出建议，不要写标题。"
    )


def build_plan_research_prompt(
    *,
    framework: str,
    debater_suggestions: str,
    theme: str,
    stance: str,
    existing_evidence: str,
) -> str:
    return (
        "你是辩论研究助手。根据论证框架和辩手建议，规划搜索任务。\n"
        f"辩题：{theme}\n"
        f"立场：{stance}\n"
        f"论证框架：\n{framework}\n"
        f"辩手建议：\n{debater_suggestions}\n"
        f"已有证据：\n{existing_evidence or '暂无'}\n\n"
        "请输出 JSON，格式为 {\"tasks\": [{\"query\": \"搜索词\", \"purpose\": \"目的\"}]}。\n"
        "搜索词应为英文或中文关键词短语，适合搜索引擎。\n"
        "最多 5 个任务，避免与已有证据重复。只输出 JSON。"
    )


def build_extract_summary_prompt(
    *,
    url_content: str,
    query: str,
    theme: str,
    stance: str,
) -> str:
    return (
        "你是辩论研究助手。从网页内容中提取与辩题相关的证据。\n"
        f"辩题：{theme}\n"
        f"立场：{stance}\n"
        f"搜索目的：{query}\n"
        f"网页内容：\n{url_content}\n\n"
        "请提取 1-2 段最相关的事实、数据或论据，用中文输出摘要（100-200字）。"
        '如果内容不相关，输出"无相关内容"。不要编造数据。'
    )


def build_reflect_prompt(
    *,
    framework: str,
    evidence_so_far: str,
    theme: str,
    stance: str,
    round_num: int,
    max_rounds: int,
) -> str:
    return (
        "你是辩论研究助手。判断是否需要继续搜索。\n"
        f"辩题：{theme}\n"
        f"立场：{stance}\n"
        f"当前研究轮次：{round_num}/{max_rounds}\n"
        f"论证框架：\n{framework}\n"
        f"已收集证据：\n{evidence_so_far}\n\n"
        "请判断：已有证据是否足够支撑论证框架？是否还有明显的证据缺口？\n"
        '输出 JSON：{"continue": true} 表示需要继续搜索，{"continue": false} 表示证据充足。\n'
        "只输出 JSON。"
    )


def build_finalize_prep_prompt(
    *,
    framework: str,
    evidence: str,
    role_focus_dict: dict[int, str],
) -> str:
    roles = "\n".join(f"  {k}号辩手：{v}" for k, v in role_focus_dict.items())
    return (
        "你是辩论教练。根据论证框架和收集的证据，为每位辩手准备弹药包。\n"
        f"论证框架：\n{framework}\n"
        f"收集的证据：\n{evidence}\n"
        f"辩手分工：\n{roles}\n\n"
        "请输出 JSON，格式为：\n"
        '{"overall_strategy": "总策略概述",'
        ' "debaters": ['
        '{"position": 1, "ammo": "该辩手的论点+证据+建议"},'
        '{"position": 2, "ammo": "..."},'
        '{"position": 3, "ammo": "..."},'
        '{"position": 4, "ammo": "..."}'
        "]}\n"
        "每位辩手的 ammo 应包含具体论点、可引用的证据和发言建议。只输出 JSON。"
    )


def build_debater_revise_prompt(
    *,
    framework: str,
    evidence: str,
    ammo: str,
    theme: str,
    stance: str,
    position: int,
    role_focus: str,
) -> str:
    return (
        f"你是辩论队的 {position} 号辩手。\n"
        f"辩题：{theme}\n"
        f"你方立场：{stance}\n"
        f"你的职责：{role_focus}\n"
        f"教练的论证框架终稿：\n{framework}\n"
        f"收集的证据：\n{evidence}\n"
        f"教练给你的弹药包：\n{ammo}\n\n"
        "请根据以上材料，输出你的修订发言计划（3条简洁要点）。"
        "不要写标题或开场白。"
    )
