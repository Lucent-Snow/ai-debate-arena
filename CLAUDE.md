# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

CLI-first multi-agent AI debate system with real-time web console. Agents (debaters, coaches, judges, summarizer) debate topics in 1v1 or 4v4 mode. Results export as JSON. Web console provides real-time observation via WebSocket, plus history browsing.

## Commands

```bash
# Install
pip install -e .[dev]
pip install -e .[dev,web]   # includes FastAPI + uvicorn for web console

# Run debates (CLI)
debate 1v1 --topic "..." --rounds 3 --config examples/config.yaml
debate 4v4 --topic "..." --config examples/config.yaml

# Run web console
debate web --config examples/config.yaml --port 8080

# Frontend dev (in web/ directory)
cd web && npm install
cd web && npm run dev        # Vite dev server with proxy to backend
cd web && npm run build      # production build → web/dist/

# Test & lint
pytest                     # all tests
pytest -m live             # real API tests only
pytest -m slow             # long-running e2e
ruff check .               # lint
ruff check . --fix         # autofix
```

Required env vars for live tests and CLI usage:
- `AI_DEBATE_BASE_URL` (e.g. `https://dashscope.aliyuncs.com/compatible-mode/v1`)
- `AI_DEBATE_API_KEY`
- `AI_DEBATE_MODEL` (e.g. `qwen-plus`)

## Architecture

**Data flow:** Config → Arena → Agents → EventLog → JSON export → Web viewer

- `debate/config.py` — YAML + env var parsing. `ModelRegistry` resolves config with layered overrides: default → side → role → agent_id.
- `debate/models.py` — Domain types: `Side`, `Role`, `Phase`, `EventType`, `Visibility`, `DebateEvent`, `DebateResult`, etc.
- `debate/llm.py` — Unified async LLM client. OpenAI-compatible by default, Anthropic via dedicated path. Handles retries, token tracking, `response_format` for JSON output.
- `debate/agents/` — Each role (debater, coach, judge, summarizer) extends `BaseAgent`. Agents only handle prompt construction and LLM calls; they don't control debate flow.
- `debate/engine/arena.py` — Main orchestrator. `run_1v1()` and `run_4v4()` drive the full lifecycle: topic → planning → rounds → judging → summary. Observer pattern for real-time CLI events.
- `debate/engine/event_log.py` — Single source of truth. Events tagged with `Visibility` (PUBLIC/TEAM/PRIVATE); `visible_to()` filters what each agent can see.
- `debate/output/` — JSON serialization (`exporter.py`) and Rich terminal rendering (`formatter.py`).
- `debate/prompts/templates.py` — Jinja-style prompt builders for all agent roles. `JUDGE_ANGLES` defines 3 scoring dimensions (logic, persuasion, clash).
- `debate/cli.py` — Typer entry point. `debate` command with `1v1`, `4v4`, `web` subcommands.
- `debate/server/` — FastAPI web console backend (optional `[web]` dependency).
  - `app.py` — FastAPI factory, CORS, mounts static files from `web/dist/`.
  - `ws.py` — WebSocket endpoint. Bridges arena observer → asyncio.Queue → WebSocket.
  - `history.py` — REST API for debate history stored in `~/.debate-arena/history/`.
- `web/` — Vite + React 19 + TypeScript + Tailwind v4 frontend. Zustand state management. Connects to backend via WebSocket for real-time debate observation.

## Key Conventions

- **No mocks.** Tests call real LLM APIs. No fake transports or fabricated responses. Tests validate connectivity, flow completion, and JSON contract — not exact text output.
- **Module boundaries are strict.** `agents/` handles LLM interaction only. `engine/` handles orchestration only. `output/` handles display only. `server/` handles web transport only. `web/` is the React frontend.
- **Event log is the single source of truth.** All debate state flows through it. The web viewer receives events via WebSocket in real time.
- **Config layering.** `${VAR_NAME}` in YAML expands to env vars. Override resolution: default → side → role → agent_id.
- **Judge JSON repair.** Real models may truncate structured output; judge scoring includes fallback JSON repair logic.
- **Async throughout.** All LLM calls use `httpx` async. Debate phases run concurrently where possible.

## Ruff Config

Line length 100, target Python 3.10. Rules: `E`, `F`, `I`, `B`, `UP`.

## pytest Config

`asyncio_mode = "auto"`. Markers: `live` (real API), `slow` (e2e).
