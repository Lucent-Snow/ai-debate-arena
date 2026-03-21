import { useEffect, useRef, useCallback, useState } from "react";
import { useDebateStore } from "../store/debateStore";
import type { ClientMessage, ServerMessage, Speech, StartDebatePayload, TeamMessage } from "../lib/protocol";

export function useDebateSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const retriesRef = useRef(0);
  const maxRetries = 3;

  const {
    startDebate,
    setTopic,
    setRound,
    addSpeech,
    addTeamMessage,
    setJudging,
    setSummary,
    setComplete,
    setError,
    setHistory,
  } = useDebateStore();

  const connect = useCallback(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      retriesRef.current = 0;
    };

    ws.onclose = () => {
      setConnected(false);
      if (retriesRef.current < maxRetries) {
        const delay = Math.min(1000 * 2 ** retriesRef.current, 8000);
        retriesRef.current++;
        setTimeout(connect, delay);
      }
    };

    ws.onerror = () => {
      ws.close();
    };

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data) as ServerMessage;
      handleMessage(msg);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleMessage = useCallback(
    (msg: ServerMessage) => {
      if (msg.type === "event") {
        const { event, payload } = msg;

        if (event === "topic_ready" && payload.topic) {
          setTopic(payload.topic as { theme: string; pro_position: string; con_position: string });
        } else if (event === "round_start") {
          setRound(payload.round_num as number, payload.total_rounds as number);
        } else if (event === "speech_ready") {
          addSpeech({
            agent_id: payload.agent_id as string,
            side: payload.side as Speech["side"],
            round_num: payload.round_num as number,
            content: payload.content as string,
            model: payload.model as string,
          });
        } else if (event === "team_strategy_ready") {
          addTeamMessage({
            id: `ts-${Date.now()}`,
            kind: "strategy",
            agent_id: payload.agent_id as string,
            side: payload.side as TeamMessage["side"],
            round_num: null,
            content: payload.content as string,
            timestamp: Date.now(),
          });
        } else if (event === "plan_ready" && useDebateStore.getState().mode === "4v4") {
          addTeamMessage({
            id: `pl-${Date.now()}-${payload.agent_id}`,
            kind: "plan",
            agent_id: payload.agent_id as string,
            side: payload.side as TeamMessage["side"],
            round_num: null,
            content: payload.content as string,
            timestamp: Date.now(),
          });
        } else if (event === "coach_instruction_ready") {
          addTeamMessage({
            id: `ci-${Date.now()}`,
            kind: "coach_instruction",
            agent_id: payload.agent_id as string,
            side: payload.side as TeamMessage["side"],
            round_num: payload.round_num as number | null,
            content: payload.content as string,
            timestamp: Date.now(),
          });
        } else if (event === "judging_ready" && payload.judging) {
          setJudging(
            payload.judging as { scores: []; final: { pro_total: number; con_total: number; winner: string; verdict_document: string } },
          );
        } else if (event === "summary_ready" && payload.summary) {
          const raw = payload.summary;
          setSummary(
            typeof raw === "string"
              ? { content: raw, agent_id: "", model: "" }
              : (raw as { content: string; agent_id: string; model: string }),
          );
        }
      } else if (msg.type === "debate_complete") {
        setComplete(msg.result);
      } else if (msg.type === "error") {
        setError(msg.message);
      } else if (msg.type === "history") {
        setHistory(msg.items);
      }
    },
    [setTopic, setRound, addSpeech, addTeamMessage, setJudging, setSummary, setComplete, setError, setHistory],
  );

  const sendMessage = useCallback((msg: ClientMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  const sendStartDebate = useCallback(
    (payload: StartDebatePayload) => {
      startDebate(payload.mode, payload.rounds);
      sendMessage({ type: "start_debate", payload });
    },
    [startDebate, sendMessage],
  );

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  return { connected, sendMessage, sendStartDebate };
}
