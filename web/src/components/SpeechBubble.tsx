interface Props {
  side: "pro" | "con";
  agentId: string;
  roundNum: number;
  content: string;
  model: string;
  index: number;
}

function agentLabel(agentId: string): string {
  const map: Record<string, string> = {
    pro_debater_1: "正方一辩",
    pro_debater_2: "正方二辩",
    pro_debater_3: "正方三辩",
    pro_debater_4: "正方四辩",
    con_debater_1: "反方一辩",
    con_debater_2: "反方二辩",
    con_debater_3: "反方三辩",
    con_debater_4: "反方四辩",
  };
  return map[agentId] ?? agentId;
}

export default function SpeechBubble({ side, agentId, roundNum, content, model, index }: Props) {
  const isPro = side === "pro";

  return (
    <div
      className={`max-w-[85%] animate-fade-in-up ${isPro ? "" : "ml-auto"}`}
      style={{ animationDelay: `${index * 0.1}s` }}
    >
      <div
        className={`rounded px-4 py-3 ${
          isPro
            ? "border-l border-pro bg-pro-bg"
            : "border-r border-con bg-con-bg"
        }`}
      >
        <div className="flex items-center gap-2 mb-2">
          <span className={`font-sans text-sm font-medium ${isPro ? "text-pro" : "text-con"}`}>
            {agentLabel(agentId)}
          </span>
          <span className="text-xs px-1.5 py-0.5 rounded bg-ivory-dark text-slate-muted">
            R{roundNum}
          </span>
          <span className="font-mono text-xs text-slate-muted">{model}</span>
        </div>
        <div className="font-serif text-sm leading-relaxed whitespace-pre-wrap text-slate">
          {content}
        </div>
      </div>
    </div>
  );
}
