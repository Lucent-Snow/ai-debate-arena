import { useEffect } from "react";
import { useDebateStore } from "../store/debateStore";
import type { DebateResult, HistoryItem } from "../lib/protocol";

interface Props {
  onBack: () => void;
}

export default function HistoryList({ onBack }: Props) {
  const history = useDebateStore((s) => s.history);
  const loadResult = useDebateStore((s) => s.loadResult);
  const setShowHistory = useDebateStore((s) => s.setShowHistory);

  useEffect(() => {
    fetch("/api/history")
      .then((r) => r.json())
      .then((items: HistoryItem[]) => useDebateStore.getState().setHistory(items))
      .catch(() => {});
  }, []);

  const handleClick = async (filename: string) => {
    try {
      const res = await fetch(`/api/history/${filename}`);
      const data = (await res.json()) as DebateResult;
      loadResult(data);
      setShowHistory(false);
    } catch {
      // ignore
    }
  };

  const winnerLabel = (w: string) =>
    w === "pro" ? "正方胜" : w === "con" ? "反方胜" : w;

  return (
    <div className="animate-fade-in">
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={onBack}
          className="text-sm text-slate-muted hover:text-slate transition-colors"
        >
          &larr; 返回
        </button>
        <h2 className="font-serif text-xl text-slate">历史辩论</h2>
      </div>

      {history.length === 0 ? (
        <p className="text-center text-slate-muted py-12">暂无历史记录</p>
      ) : (
        <div className="space-y-2">
          {history.map((item) => (
            <button
              key={item.filename}
              onClick={() => handleClick(item.filename)}
              className="w-full text-left px-4 py-3 bg-white border border-ivory-dark rounded hover:border-slate-muted/30 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="font-serif text-slate">{item.theme}</span>
                <span className="text-xs font-mono text-slate-muted">{item.mode}</span>
              </div>
              <div className="flex items-center gap-3 mt-1 text-xs text-slate-muted">
                <span>{item.date}</span>
                {item.winner && (
                  <span
                    className={`px-1.5 py-0.5 rounded ${
                      item.winner === "pro"
                        ? "bg-pro-bg text-pro"
                        : "bg-con-bg text-con"
                    }`}
                  >
                    {winnerLabel(item.winner)}
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}