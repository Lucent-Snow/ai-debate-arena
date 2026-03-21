import { useState } from "react";
import type { Speech, Topic } from "../lib/protocol";

interface Props {
  speeches: Speech[];
  currentRound: number;
  totalRounds: number;
  topic: Topic | null;
}

function dotColor(side: string): string {
  if (side === "pro") return "bg-pro";
  if (side === "con") return "bg-con";
  return "bg-slate-muted";
}

function shortLabel(agentId: string, side: string): string {
  const sideLabel = side === "pro" ? "正" : side === "con" ? "反" : "";
  const match = agentId.match(/_(\d)$/);
  const num = match?.[1] ?? "";
  return `${sideLabel}${num ? num + "辩" : agentId}`;
}

export default function Timeline({ speeches, currentRound, totalRounds, topic }: Props) {
  const [collapsed, setCollapsed] = useState(false);

  // Group speeches by round
  const rounds = new Map<number, Speech[]>();
  for (const s of speeches) {
    const list = rounds.get(s.round_num) ?? [];
    list.push(s);
    rounds.set(s.round_num, list);
  }

  return (
    <div className="text-xs">
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center gap-1 text-slate-muted hover:text-slate mb-2 transition-colors"
      >
        <span className="text-[10px]">{collapsed ? "+" : "-"}</span>
        <span className="font-medium">时间线</span>
      </button>

      {!collapsed && (
        <div className="relative pl-4">
          {/* Vertical line */}
          <div className="absolute left-[5px] top-1 bottom-1 w-px bg-ivory-dark" />

          {/* Topic node */}
          {topic && (
            <div className="relative flex items-start gap-2 mb-3">
              <div className="absolute left-[-11px] top-1 w-2 h-2 rounded-full bg-terracotta" />
              <span className="text-slate-muted leading-tight truncate">{topic.theme}</span>
            </div>
          )}

          {/* Round groups */}
          {Array.from({ length: totalRounds }, (_, i) => i + 1).map((r) => {
            const isActive = r === currentRound;
            const items = rounds.get(r) ?? [];
            return (
              <div key={r} className="mb-2">
                <div className="relative flex items-center gap-2 mb-1">
                  <div
                    className={`absolute left-[-11px] w-2 h-2 rounded-full ${
                      isActive ? "bg-terracotta" : items.length > 0 ? "bg-slate-muted" : "bg-ivory-dark"
                    }`}
                  />
                  <span className={`font-medium ${isActive ? "text-terracotta" : "text-slate-muted"}`}>
                    第 {r} 轮
                  </span>
                </div>
                {items.map((s, idx) => (
                  <div key={idx} className="relative flex items-center gap-1.5 ml-2 mb-0.5">
                    <div className={`w-1.5 h-1.5 rounded-full ${dotColor(s.side)}`} />
                    <span className="text-slate-muted truncate">{shortLabel(s.agent_id, s.side)}</span>
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
