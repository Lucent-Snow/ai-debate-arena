// TypeScript types mirroring Python models

export type Side = "pro" | "con" | "neutral";
export type DebateStatus = "idle" | "running" | "judging" | "complete";
export type DebateMode = "1v1" | "4v4";

export interface Topic {
  theme: string;
  pro_position: string;
  con_position: string;
}

export interface AgentDescriptor {
  id: string;
  role: string;
  side: Side;
  position: number;
  model: string;
}

export interface DebateEvent {
  timestamp: string;
  phase: string;
  event_type: string;
  agent_id: string;
  side: Side;
  visibility: string;
  round_num: number | null;
  content: string;
  metadata: Record<string, unknown>;
}

export interface JudgeScore {
  judge: string;
  angle: string;
  pro_score: number;
  con_score: number;
  pro_analysis: string;
  con_analysis: string;
  key_moments: string[];
  reasoning: string;
}

export interface Verdict {
  pro_total: number;
  con_total: number;
  winner: string;
  verdict_document: string;
}

export interface Judging {
  scores: JudgeScore[];
  final: Verdict;
}

export interface SummaryResult {
  content: string;
  agent_id: string;
  model: string;
}

export interface AgentStats {
  calls: number;
  tokens_in: number;
  tokens_out: number;
  duration_seconds: number;
}

export interface DebateStats {
  total_tokens: number;
  total_cost_usd: number;
  total_duration_seconds: number;
  per_agent_stats: Record<string, AgentStats>;
}

export interface DebateResult {
  version: string;
  mode: string;
  topic: Topic;
  config: Record<string, unknown>;
  agents: AgentDescriptor[];
  events: DebateEvent[];
  judging: Judging;
  summary: SummaryResult;
  stats: DebateStats;
}

export interface Speech {
  agent_id: string;
  side: Side;
  round_num: number;
  content: string;
  model: string;
}

export interface TeamMessage {
  id: string;
  kind: "strategy" | "plan" | "coach_instruction";
  agent_id: string;
  side: Side;
  round_num: number | null;
  content: string;
  timestamp: number;
}

export interface HistoryItem {
  filename: string;
  mode: string;
  theme: string;
  date: string;
  winner: string;
}

// WebSocket message types

export interface StartDebatePayload {
  mode: DebateMode;
  theme: string;
  rounds: number;
  pro_position?: string;
  con_position?: string;
}

export type ClientMessage =
  | { type: "start_debate"; payload: StartDebatePayload }
  | { type: "get_history" };

export type ServerMessage =
  | { type: "event"; event: string; payload: Record<string, unknown> }
  | { type: "debate_complete"; result: DebateResult }
  | { type: "error"; message: string }
  | { type: "history"; items: HistoryItem[] };
