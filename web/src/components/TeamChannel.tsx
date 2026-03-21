import { useEffect, useRef } from "react";
import type { TeamMessage } from "../lib/protocol";

interface Props {
  side: "pro" | "con";
  messages: TeamMessage[];
}

const agentLabel: Record<string, string> = {
  pro_coach: "正方教练",
  con_coach: "反方教练",
  pro_debater_1: "正方一辩",
  pro_debater_2: "正方二辩",
  pro_debater_3: "正方三辩",
  pro_debater_4: "正方四辩",
  con_debater_1: "反方一辩",
  con_debater_2: "反方二辩",
  con_debater_3: "反方三辩",
  con_debater_4: "反方四辩",
};

const kindBadge: Record<TeamMessage["kind"], { label: string; cls: string }> = {
  strategy: { label: "策略", cls: "bg-terracotta/15 text-terracotta" },
  plan: { label: "计划", cls: "bg-slate-muted/15 text-slate-muted" },
  coach_instruction: { label: "指令", cls: "bg-terracotta/15 text-terracotta" },
};

export default function TeamChannel({ side, messages }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const isPro = side === "pro";

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages.length]);

  return (
    <div className="flex flex-col h-full min-h-0">
      <div
        className={`px-3 py-2 text-xs font-medium border-b ${
          isPro
            ? "text-pro bg-pro-bg/60 border-pro-border"
            : "text-con bg-con-bg/60 border-con-border"
        }`}
      >
        {isPro ? "正方频道" : "反方频道"}
      </div>
      <div
        ref={scrollRef}
        className={`flex-1 overflow-y-auto p-2 space-y-2 ${
          isPro ? "bg-pro-bg/30" : "bg-con-bg/30"
        }`}
      >
        {messages.map((msg) => {
          const badge = kindBadge[msg.kind];
          return (
            <div
              key={msg.id}
              className={`rounded px-2.5 py-2 text-xs animate-fade-in ${
                msg.kind === "strategy"
                  ? isPro
                    ? "bg-pro-bg border border-pro-border"
                    : "bg-con-bg border border-con-border"
                  : "bg-white/70 border border-ivory-dark"
              }`}
            >
              <div className="flex items-center gap-1.5 mb-1">
                <span className={`font-medium ${isPro ? "text-pro" : "text-con"}`}>
                  {agentLabel[msg.agent_id] ?? msg.agent_id}
                </span>
                <span className={`px-1 py-0.5 rounded text-[10px] font-medium ${badge.cls}`}>
                  {msg.round_num != null ? `R${msg.round_num} ${badge.label}` : badge.label}
                </span>
              </div>
              <div className="text-slate leading-relaxed whitespace-pre-wrap line-clamp-[12]">
                {msg.content}
              </div>
            </div>
          );
        })}
        {messages.length === 0 && (
          <p className="text-center text-slate-muted text-xs py-6">等待团队消息...</p>
        )}
      </div>
    </div>
  );
}
