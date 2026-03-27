import { create } from "zustand";
import type {
  DebateMode,
  DebateResult,
  DebateStatus,
  HistoryItem,
  Judging,
  Speech,
  SummaryResult,
  TeamMessage,
  Topic,
} from "../lib/protocol";

interface DebateState {
  status: DebateStatus;
  mode: DebateMode;
  topic: Topic | null;
  speeches: Speech[];
  proTeamMessages: TeamMessage[];
  conTeamMessages: TeamMessage[];
  currentRound: number;
  totalRounds: number;
  judging: Judging | null;
  summary: SummaryResult | null;
  result: DebateResult | null;
  history: HistoryItem[];
  error: string | null;
  showHistory: boolean;

  // Actions
  startDebate: (mode: DebateMode, totalRounds: number) => void;
  setTopic: (topic: Topic) => void;
  setRound: (current: number, total: number) => void;
  addSpeech: (speech: Speech) => void;
  addTeamMessage: (msg: TeamMessage) => void;
  setJudging: (judging: Judging) => void;
  setSummary: (summary: SummaryResult) => void;
  setComplete: (result: DebateResult) => void;
  setError: (message: string) => void;
  setHistory: (items: HistoryItem[]) => void;
  setShowHistory: (show: boolean) => void;
  loadResult: (result: DebateResult) => void;
  reset: () => void;
}

const initialState = {
  status: "idle" as DebateStatus,
  mode: "1v1" as DebateMode,
  topic: null,
  speeches: [],
  proTeamMessages: [] as TeamMessage[],
  conTeamMessages: [] as TeamMessage[],
  currentRound: 0,
  totalRounds: 3,
  judging: null,
  summary: null,
  result: null,
  history: [],
  error: null,
  showHistory: false,
};

export const useDebateStore = create<DebateState>((set) => ({
  ...initialState,

  startDebate: (mode, totalRounds) =>
    set({ ...initialState, status: "running", mode, totalRounds }),

  setTopic: (topic) => set({ topic }),

  setRound: (current, total) => set({ currentRound: current, totalRounds: total }),

  addSpeech: (speech) => set((s) => ({ speeches: [...s.speeches, speech] })),

  addTeamMessage: (msg) =>
    set((s) =>
      msg.side === "pro"
        ? { proTeamMessages: [...s.proTeamMessages, msg] }
        : { conTeamMessages: [...s.conTeamMessages, msg] },
    ),

  setJudging: (judging) => set({ judging, status: "judging" }),

  setSummary: (summary) => set({ summary }),

  setComplete: (result) => set({ result, status: "complete" }),

  setError: (message) => set({ error: message }),

  setHistory: (items) => set({ history: items }),

  setShowHistory: (show) => set({ showHistory: show }),

  loadResult: (result) => {
    const teamMessages: TeamMessage[] = result.events
      .filter((e) =>
        e.event_type === "TEAM_DISCUSSION" ||
        e.event_type === "PLAN" ||
        e.event_type === "COACH_INSTRUCTION" ||
        e.event_type === "FRAMEWORK" ||
        e.event_type === "DEBATER_SUGGESTION" ||
        e.event_type === "RESEARCH"
      )
      .map((e, i) => {
        let kind: TeamMessage["kind"];
        if (e.event_type === "FRAMEWORK") kind = "framework";
        else if (e.event_type === "DEBATER_SUGGESTION") kind = "debater_suggestion";
        else if (e.event_type === "RESEARCH") kind = "research";
        else if (e.event_type === "TEAM_DISCUSSION") kind = "strategy";
        else if (e.event_type === "PLAN") kind = "plan";
        else kind = "coach_instruction";

        let content = e.content;
        if (e.event_type === "RESEARCH" && e.metadata?.title) {
          const title = e.metadata.title as string;
          const url = (e.metadata.url as string) ?? "";
          content = `📎 ${title}\n${url}\n\n${content}`;
        }

        return {
          id: `hist-${i}`,
          kind,
          agent_id: e.agent_id,
          side: e.side,
          round_num: e.round_num,
          content,
          timestamp: new Date(e.timestamp).getTime(),
        };
      });

    set({
      status: "complete",
      mode: result.mode as DebateMode,
      topic: result.topic,
      judging: result.judging,
      summary: result.summary,
      result,
      speeches: result.events
        .filter((e) => e.event_type === "SPEECH")
        .map((e) => ({
          agent_id: e.agent_id,
          side: e.side,
          round_num: e.round_num ?? 0,
          content: e.content,
          model: (e.metadata?.model as string) ?? "",
        })),
      proTeamMessages: teamMessages.filter((m) => m.side === "pro"),
      conTeamMessages: teamMessages.filter((m) => m.side === "con"),
      showHistory: false,
    });
  },

  reset: () => set(initialState),
}));