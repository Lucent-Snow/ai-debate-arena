import { useDebateStore } from "../store/debateStore";

export default function SummaryPanel() {
  const summary = useDebateStore((s) => s.summary);
  const result = useDebateStore((s) => s.result);
  const reset = useDebateStore((s) => s.reset);

  if (!summary && !result) return null;

  const handleExport = () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `debate-${result.mode}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {summary && (
        <div className="max-w-2xl mx-auto">
          <p className="font-serif leading-relaxed whitespace-pre-wrap text-slate">
            {summary.content}
          </p>
        </div>
      )}

      {result && (
        <div className="max-w-3xl mx-auto">
          <h3 className="font-sans font-medium text-slate mb-4">统计</h3>
          <div className="grid grid-cols-5 gap-3 mb-6 text-center text-sm">
            <div className="bg-white rounded border border-ivory-dark p-3">
              <div className="text-slate-muted">模式</div>
              <div className="font-mono font-medium">{result.mode}</div>
            </div>
            <div className="bg-white rounded border border-ivory-dark p-3">
              <div className="text-slate-muted">总轮数</div>
              <div className="font-mono font-medium">
                {result.events.filter((e) => e.event_type === "SPEECH").length > 0
                  ? Math.max(
                      ...result.events
                        .filter((e) => e.round_num !== null)
                        .map((e) => e.round_num as number),
                    )
                  : 0}
              </div>
            </div>
            <div className="bg-white rounded border border-ivory-dark p-3">
              <div className="text-slate-muted">事件数</div>
              <div className="font-mono font-medium">{result.events.length}</div>
            </div>
            <div className="bg-white rounded border border-ivory-dark p-3">
              <div className="text-slate-muted">总 Tokens</div>
              <div className="font-mono font-medium">{(result.stats.total_tokens ?? 0).toLocaleString()}</div>
            </div>
            <div className="bg-white rounded border border-ivory-dark p-3">
              <div className="text-slate-muted">总耗时</div>
              <div className="font-mono font-medium">{(result.stats.total_duration_seconds ?? 0).toFixed(1)}s</div>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="text-left text-slate-muted border-b border-ivory-dark">
                  <th className="py-2 pr-4">Agent</th>
                  <th className="py-2 pr-4 font-mono">Calls</th>
                  <th className="py-2 pr-4 font-mono">Tokens In</th>
                  <th className="py-2 pr-4 font-mono">Tokens Out</th>
                  <th className="py-2 font-mono">Duration</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(result.stats.per_agent_stats ?? {}).map(([agentId, stats]) => (
                    <tr key={agentId} className="border-b border-ivory-dark/50">
                      <td className="py-2 pr-4 font-medium">{agentId}</td>
                      <td className="py-2 pr-4 font-mono">{stats.calls}</td>
                      <td className="py-2 pr-4 font-mono">{stats.tokens_in.toLocaleString()}</td>
                      <td className="py-2 pr-4 font-mono">{stats.tokens_out.toLocaleString()}</td>
                      <td className="py-2 font-mono">{stats.duration_seconds.toFixed(1)}s</td>
                    </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="flex justify-center gap-3 pt-4">
        {result && (
          <button
            onClick={handleExport}
            className="px-5 py-2.5 bg-slate text-ivory rounded font-medium text-sm hover:bg-slate-light transition-colors"
          >
            导出 JSON
          </button>
        )}
        <button
          onClick={reset}
          className="px-5 py-2.5 bg-terracotta text-white rounded font-medium text-sm hover:bg-terracotta-hover transition-colors"
        >
          新辩论
        </button>
      </div>
    </div>
  );
}
