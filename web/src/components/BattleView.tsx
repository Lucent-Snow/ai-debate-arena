import { useEffect, useRef } from "react";
import { useDebateStore } from "../store/debateStore";
import SpeechBubble from "./SpeechBubble";
import Timeline from "./Timeline";

function phaseSegments(currentRound: number, totalRounds: number) {
  const phases: { label: string; state: "done" | "active" | "upcoming" }[] = [];

  // Planning phase
  phases.push({
    label: "准备",
    state: currentRound > 0 ? "done" : "active",
  });

  // Round phases
  for (let i = 1; i <= totalRounds; i++) {
    let state: "done" | "active" | "upcoming";
    if (i < currentRound) state = "done";
    else if (i === currentRound) state = "active";
    else state = "upcoming";
    phases.push({ label: `第${i}轮`, state });
  }

  // Judging phase
  phases.push({ label: "评判", state: "upcoming" });

  return phases;
}

export default function BattleView() {
  const { topic, speeches, currentRound, totalRounds } = useDebateStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new speech
  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [speeches.length]);

  if (!topic) {
    return (
      <div className="flex items-center justify-center py-20 animate-fade-in">
        <p className="text-slate-muted font-serif">等待辩题生成...</p>
      </div>
    );
  }

  const progress = totalRounds > 0 ? currentRound / totalRounds : 0;
  const phases = phaseSegments(currentRound, totalRounds);

  return (
    <div className="animate-fade-in">
      {/* Topic header */}
      <div className="text-center mb-6">
        <h2 className="font-serif text-xl text-slate mb-3">{topic.theme}</h2>
        <div className="flex justify-center gap-6 text-sm">
          <span className="text-pro font-medium">{topic.pro_position}</span>
          <span className="text-slate-muted">vs</span>
          <span className="text-con font-medium">{topic.con_position}</span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs text-slate-muted">
            第 {currentRound} / {totalRounds} 轮
          </span>
        </div>
        <div className="h-1 bg-ivory-dark rounded-full overflow-hidden">
          <div
            className="h-full bg-terracotta rounded-full transition-all duration-500"
            style={{ width: `${Math.min(progress * 100, 100)}%` }}
          />
        </div>
      </div>

      {/* Phase indicators */}
      <div className="flex gap-1 mb-6 overflow-x-auto">
        {phases.map((p) => (
          <span
            key={p.label}
            className={`text-xs px-2 py-1 rounded whitespace-nowrap ${
              p.state === "active"
                ? "bg-terracotta text-white"
                : p.state === "done"
                  ? "bg-slate-muted/20 text-slate-muted"
                  : "bg-ivory-dark text-slate-muted/50"
            }`}
          >
            {p.label}
          </span>
        ))}
      </div>

      {/* Main content area */}
      <div className="flex gap-6">
        {/* Speeches column */}
        <div ref={scrollRef} className="flex-1 space-y-4 min-w-0">
          {speeches.map((s, i) => (
            <SpeechBubble
              key={i}
              side={s.side === "pro" ? "pro" : "con"}
              agentId={s.agent_id}
              roundNum={s.round_num}
              content={s.content}
              model={s.model}
              index={i}
            />
          ))}
          {speeches.length === 0 && (
            <p className="text-center text-slate-muted text-sm py-8">等待发言...</p>
          )}
        </div>

        {/* Timeline sidebar - hidden on mobile */}
        <aside className="hidden lg:block w-48 shrink-0">
          <Timeline
            speeches={speeches}
            currentRound={currentRound}
            totalRounds={totalRounds}
            topic={topic}
          />
        </aside>
      </div>
    </div>
  );
}
