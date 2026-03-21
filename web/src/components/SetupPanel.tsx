import { useState } from "react";
import type { DebateMode } from "../lib/protocol";

interface Props {
  onStart: (payload: {
    mode: DebateMode;
    theme: string;
    rounds: number;
    pro_position?: string;
    con_position?: string;
  }) => void;
  disabled: boolean;
}

export default function SetupPanel({ onStart, disabled }: Props) {
  const [mode, setMode] = useState<DebateMode>("1v1");
  const [theme, setTheme] = useState("");
  const [rounds, setRounds] = useState(3);
  const [pro, setPro] = useState("");
  const [con, setCon] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!theme.trim()) return;
    onStart({
      mode,
      theme: theme.trim(),
      rounds,
      pro_position: pro.trim() || undefined,
      con_position: con.trim() || undefined,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-xl mx-auto space-y-6">
      <div className="text-center mb-8">
        <h2 className="font-serif text-2xl text-slate mb-2">发起辩论</h2>
        <p className="text-slate-muted text-sm">
          输入辩题，选择模式，开始一场 AI 辩论
        </p>
      </div>

      {/* Mode toggle */}
      <div className="flex gap-2 justify-center">
        {(["1v1", "4v4"] as const).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => setMode(m)}
            disabled={disabled}
            className={`px-4 py-2 rounded text-sm font-medium transition-colors duration-200 ${
              mode === m
                ? "bg-slate text-ivory"
                : "bg-ivory-dark text-slate-muted hover:text-slate"
            }`}
          >
            {m}
          </button>
        ))}
      </div>

      {/* Topic */}
      <div>
        <label className="block text-sm font-medium text-slate mb-1.5">辩题</label>
        <input
          type="text"
          value={theme}
          onChange={(e) => setTheme(e.target.value)}
          placeholder="例如：人工智能是否会取代人类工作"
          disabled={disabled}
          className="w-full px-3 py-2.5 bg-white border border-ivory-dark rounded text-slate placeholder:text-slate-muted/50 focus:outline-none focus:border-slate-muted transition-colors"
        />
      </div>

      {/* Rounds (1v1 only) */}
      {mode === "1v1" && (
        <div>
          <label className="block text-sm font-medium text-slate mb-1.5">
            轮数: {rounds}
          </label>
          <input
            type="range"
            min={1}
            max={5}
            value={rounds}
            onChange={(e) => setRounds(Number(e.target.value))}
            disabled={disabled}
            className="w-full accent-terracotta"
          />
          <div className="flex justify-between text-xs text-slate-muted mt-1">
            <span>1</span><span>2</span><span>3</span><span>4</span><span>5</span>
          </div>
        </div>
      )}

      {/* Optional positions */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-pro mb-1.5">
            正方立场（可选）
          </label>
          <input
            type="text"
            value={pro}
            onChange={(e) => setPro(e.target.value)}
            placeholder="自动生成"
            disabled={disabled}
            className="w-full px-3 py-2 bg-pro-bg border border-pro-border rounded text-slate placeholder:text-slate-muted/50 focus:outline-none focus:border-pro text-sm transition-colors"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-con mb-1.5">
            反方立场（可选）
          </label>
          <input
            type="text"
            value={con}
            onChange={(e) => setCon(e.target.value)}
            placeholder="自动生成"
            disabled={disabled}
            className="w-full px-3 py-2 bg-con-bg border border-con-border rounded text-slate placeholder:text-slate-muted/50 focus:outline-none focus:border-con text-sm transition-colors"
          />
        </div>
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={disabled || !theme.trim()}
        className="w-full py-3 bg-terracotta text-white rounded font-medium hover:bg-terracotta-hover disabled:opacity-40 disabled:cursor-not-allowed transition-colors duration-200"
      >
        开始辩论
      </button>
    </form>
  );
}