import type { ReactNode } from "react";

interface Props {
  children: ReactNode;
  onHistoryClick?: () => void;
  showHistoryButton?: boolean;
  wide?: boolean;
}

export default function Layout({ children, onHistoryClick, showHistoryButton, wide }: Props) {
  return (
    <div className="min-h-screen bg-ivory">
      <header className="border-b border-ivory-dark">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <h1 className="font-sans text-lg font-semibold text-slate tracking-tight">
            AI Debate Arena
          </h1>
          {showHistoryButton && onHistoryClick && (
            <button
              onClick={onHistoryClick}
              className="text-sm text-slate-muted hover:text-slate transition-colors"
            >
              历史记录
            </button>
          )}
        </div>
      </header>
      <main className={`${wide ? "max-w-[1400px]" : "max-w-6xl"} mx-auto px-6 py-8`}>
        {children}
      </main>
    </div>
  );
}
