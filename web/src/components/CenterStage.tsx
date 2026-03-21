import { useEffect, useRef } from "react";
import type { Speech } from "../lib/protocol";
import SpeechBubble from "./SpeechBubble";

interface Props {
  speeches: Speech[];
  currentRound: number;
}

export default function CenterStage({ speeches, currentRound }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [speeches.length]);

  // Group speeches by round for dividers
  const elements: React.ReactNode[] = [];
  let lastRound = 0;

  speeches.forEach((s, i) => {
    if (s.round_num !== lastRound) {
      lastRound = s.round_num;
      elements.push(
        <div key={`divider-${s.round_num}`} className="flex items-center gap-3 py-2">
          <div className="flex-1 h-px bg-ivory-dark" />
          <span className="text-xs text-slate-muted font-medium whitespace-nowrap">
            第 {s.round_num} 轮
          </span>
          <div className="flex-1 h-px bg-ivory-dark" />
        </div>,
      );
    }
    elements.push(
      <SpeechBubble
        key={`speech-${i}`}
        side={s.side === "pro" ? "pro" : "con"}
        agentId={s.agent_id}
        roundNum={s.round_num}
        content={s.content}
        model={s.model}
        index={i}
      />,
    );
  });

  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="px-3 py-2 text-xs font-medium text-slate-muted border-b border-ivory-dark bg-ivory/60">
        公开舞台 {currentRound > 0 && `· 第 ${currentRound} 轮`}
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-3">
        {elements.length > 0 ? (
          elements
        ) : (
          <p className="text-center text-slate-muted text-sm py-8">等待正式发言...</p>
        )}
      </div>
    </div>
  );
}
