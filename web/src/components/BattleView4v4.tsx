import { useDebateStore } from "../store/debateStore";
import TeamChannel from "./TeamChannel";
import CenterStage from "./CenterStage";

function phaseSegments(currentRound: number, totalRounds: number) {
  const phases: { label: string; state: "done" | "active" | "upcoming" }[] = [];

  phases.push({
    label: "策略",
    state: currentRound > 0 ? "done" : "active",
  });

  for (let i = 1; i <= totalRounds; i++) {
    let state: "done" | "active" | "upcoming";
    if (i < currentRound) state = "done";
    else if (i === currentRound) state = "active";
    else state = "upcoming";
    phases.push({ label: `第${i}轮`, state });
  }

  phases.push({ label: "评判", state: "upcoming" });

  return phases;
}

export default function BattleView4v4() {
  const { topic, speeches, proTeamMessages, conTeamMessages, currentRound, totalRounds } =
    useDebateStore();

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
      <div className="text-center mb-4">
        <h2 className="font-serif text-xl text-slate mb-2">{topic.theme}</h2>
        <div className="flex justify-center gap-6 text-sm">
          <span className="text-pro font-medium">{topic.pro_position}</span>
          <span className="text-slate-muted">vs</span>
          <span className="text-con font-medium">{topic.con_position}</span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="mb-3">
        <div className="flex items-center justify-between mb-1">
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
      <div className="flex gap-1 mb-4 overflow-x-auto">
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

      {/* Three-column layout */}
      <div className="grid grid-cols-[280px_1fr_280px] gap-3 h-[calc(100vh-320px)] min-h-[400px]">
        <div className="border border-pro-border rounded overflow-hidden">
          <TeamChannel side="pro" messages={proTeamMessages} />
        </div>
        <div className="border border-ivory-dark rounded overflow-hidden">
          <CenterStage speeches={speeches} currentRound={currentRound} />
        </div>
        <div className="border border-con-border rounded overflow-hidden">
          <TeamChannel side="con" messages={conTeamMessages} />
        </div>
      </div>
    </div>
  );
}
