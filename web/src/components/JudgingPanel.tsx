import { useDebateStore } from "../store/debateStore";
import ScoreBoard from "./ScoreBoard";
import type { JudgeScore } from "../lib/protocol";

function JudgeCard({ score, index }: { score: JudgeScore; index: number }) {
  return (
    <div
      className="bg-white rounded-lg border border-ivory-dark p-5 animate-fade-in-up"
      style={{ animationDelay: `${index * 0.2}s` }}
    >
      <h4 className="font-sans font-medium text-slate mb-3">{score.angle}</h4>

      <div className="text-center text-sm font-mono mb-4">
        <span className="text-pro">{score.pro_score}</span>
        <span className="text-slate-muted mx-2">:</span>
        <span className="text-con">{score.con_score}</span>
      </div>

      <div className="space-y-3 text-sm">
        <p className="text-pro">{score.pro_analysis}</p>
        <p className="text-con">{score.con_analysis}</p>
      </div>

      {score.key_moments.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-3">
          {score.key_moments.map((moment, i) => (
            <span
              key={i}
              className="inline-block px-2 py-0.5 text-xs bg-ivory-dark text-slate-muted rounded"
            >
              {moment}
            </span>
          ))}
        </div>
      )}

      <p className="mt-3 text-sm font-serif italic text-slate-muted leading-relaxed">
        {score.reasoning}
      </p>
    </div>
  );
}

export default function JudgingPanel() {
  const judging = useDebateStore((s) => s.judging);

  if (!judging) {
    return (
      <div className="text-center py-12 text-slate-muted animate-fade-in">
        评审进行中...
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <ScoreBoard
        proTotal={judging.final.pro_total}
        conTotal={judging.final.con_total}
        winner={judging.final.winner}
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {judging.scores.map((score, i) => (
          <JudgeCard key={score.angle} score={score} index={i} />
        ))}
      </div>

      <div className="max-w-2xl mx-auto pt-6 pb-2">
        <p className="font-serif text-slate leading-relaxed whitespace-pre-wrap">
          {judging.final.verdict_document}
        </p>
      </div>
    </div>
  );
}
