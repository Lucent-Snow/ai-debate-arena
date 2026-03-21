import Layout from "./components/Layout";
import SetupPanel from "./components/SetupPanel";
import BattleView from "./components/BattleView";
import BattleView4v4 from "./components/BattleView4v4";
import JudgingPanel from "./components/JudgingPanel";
import SummaryPanel from "./components/SummaryPanel";
import HistoryList from "./components/HistoryList";
import { useDebateStore } from "./store/debateStore";
import { useDebateSocket } from "./hooks/useDebateSocket";

export default function App() {
  const { status, mode, error, showHistory } = useDebateStore();
  const setShowHistory = useDebateStore((s) => s.setShowHistory);
  const { connected, sendStartDebate } = useDebateSocket();

  const wide = mode === "4v4" && (status === "running" || status === "judging" || status === "complete");

  return (
    <Layout
      onHistoryClick={() => setShowHistory(!showHistory)}
      showHistoryButton={status === "idle" || status === "complete"}
      wide={wide}
    >
      {error && (
        <div className="mb-6 px-4 py-3 bg-con-bg border border-con-border rounded text-con text-sm animate-fade-in">
          {error}
        </div>
      )}

      {!connected && status === "idle" && (
        <div className="mb-6 px-4 py-3 bg-ivory-dark rounded text-slate-muted text-sm text-center animate-fade-in">
          正在连接服务器...
        </div>
      )}

      {showHistory ? (
        <HistoryList onBack={() => setShowHistory(false)} />
      ) : (
        <>
          {status === "idle" && (
            <SetupPanel onStart={sendStartDebate} disabled={!connected} />
          )}
          {status === "running" && (mode === "4v4" ? <BattleView4v4 /> : <BattleView />)}
          {status === "judging" && <JudgingPanel />}
          {status === "complete" && <SummaryPanel />}
        </>
      )}
    </Layout>
  );
}
