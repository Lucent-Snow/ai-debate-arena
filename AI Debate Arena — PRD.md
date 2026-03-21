\# AI Debate Arena — PRD (for AI Development)

\#\# 1\. Project Overview

A multi-agent AI debate system. Two modes: 1v1 and 4v4. CLI-first, with a static web frontend for visualization.

Tech stack: Python 3.11+, OOP design, asyncio \+ httpx for LLM calls, typer for CLI, static HTML/JS for web.

No external agent frameworks. No LangChain, no CrewAI. Raw LLM API calls with custom orchestration.

\#\# 2\. Core Concepts

\#\#\# 2.1 Debate Topic

A debate requires:  
\- \`theme\`: string — the general topic (e.g., "AI是否会取代人类")  
\- \`pro\_position\`: string — the affirmative stance (e.g., "AI将取代人类")  
\- \`con\_position\`: string — the negative stance (e.g., "AI不会取代人类")

Topic can be provided in two ways:  
1\. User provides all three fields manually  
2\. User provides only \`theme\`, system uses LLM to generate \`pro\_position\` and \`con\_position\` as two maximally opposing stances

\#\#\# 2.2 Roles

\`\`\`  
BaseAgent (abstract)  
├── Debater          — delivers arguments in debate rounds  
├── Coach            — strategist, plans and gives per-round instructions (4v4 only)  
├── Judge            — scores the debate from a specific angle  
└── Summarizer       — produces post-debate analysis  
\`\`\`

Each agent has:  
\- \`role\`: enum (debater/coach/judge/summarizer)  
\- \`side\`: enum (pro/con/neutral) — judges and summarizer are neutral  
\- \`position\`: int (1-4 for debaters, 0 for coach) — only in 4v4  
\- \`model\_config\`: ModelConfig — which LLM to use  
\- \`system\_prompt\`: string — generated from role template \+ debate context  
\- \`message\_history\`: list\[Message\] — the agent's conversation history

\#\#\# 2.3 Model Configuration

\`\`\`python  
@dataclass  
class ModelConfig:  
    provider: str       \# "openai", "anthropic", "custom"  
    model: str          \# "gpt-4o", "claude-sonnet-4", etc.  
    base\_url: str       \# API endpoint  
    api\_key: str        \# API key  
    temperature: float  \# default 0.7  
    max\_tokens: int     \# default 4096  
\`\`\`

Configuration hierarchy:  
1\. Global default model (required)  
2\. Per-side override (optional): all agents on one side use this model  
3\. Per-role override (optional): e.g., all coaches use model X  
4\. Per-agent override (optional): e.g., pro\_debater\_2 uses model Y

Resolution order: per-agent \> per-role \> per-side \> global default.

Config file format: YAML

\`\`\`yaml  
default:  
  provider: openai  
  model: gpt-4o  
  base\_url: https://api.openai.com/v1  
  api\_key: ${OPENAI\_API\_KEY}  
  temperature: 0.7  
  max\_tokens: 4096

overrides:  
  \# per-side  
  pro:  
    model: claude-sonnet-4  
    provider: anthropic  
    base\_url: https://api.anthropic.com  
    api\_key: ${ANTHROPIC\_API\_KEY}  
    
  \# per-role  
  judge:  
    model: gpt-4o  
    temperature: 0.3  
    
  \# per-agent (format: {side}\_{role}\_{position})  
  con\_debater\_1:  
    model: deepseek-r1  
    provider: custom  
    base\_url: https://api.deepseek.com/v1  
    api\_key: ${DEEPSEEK\_API\_KEY}  
\`\`\`

\#\#\# 2.4 Information Visibility

This is critical. Different agents see different information.

\*\*Public channel\*\*: All debate speeches (what debaters say during rounds). Visible to everyone.

\*\*Team internal channel\*\*: Coach ↔ debater communication within a team. Invisible to the opposing team.

\*\*Private\*\*: An agent's own planning notes. Visible only to itself.

Visibility matrix:

| Content Type | Own Debater | Own Coach | Opposing Team | Judge | Summarizer |  
|---|---|---|---|---|---|  
| Public speeches | ✅ | ✅ | ✅ | ✅ | ✅ |  
| Own team coach instructions | ✅ (own only) | ✅ | ❌ | ❌ | ❌ |  
| Own team prep discussion | ❌ (only own parts) | ✅ | ❌ | ❌ | ❌ |  
| Own planning notes | ✅ (self only) | ❌ | ❌ | ❌ | ❌ |  
| Coach strategy plan | ❌ | ✅ (self only) | ❌ | ❌ | ❌ |

Implementation: Each agent's \`build\_context()\` method filters the global event log based on visibility rules and constructs the appropriate message history for the next LLM call.

\#\# 3\. Debate Modes

\#\#\# 3.1 Mode: 1v1

\*\*Participants\*\*: 2 debaters (pro \+ con)

\*\*Parameters\*\*:  
\- \`rounds\`: int — number of debate rounds (user-specified)  
\- \`replan\_after\`: int | null — optional, replan after this many rounds

\*\*Flow\*\*:

\`\`\`  
Phase 1: TOPIC SETUP  
  → User provides theme (+ optional positions)  
  → If positions not provided: LLM generates pro/con positions  
  → Display topic and positions

Phase 2: PLANNING  
  → Pro debater plans (private): analyze topic, list key arguments, predict opponent's strategy  
  → Con debater plans (private): same  
  → Output: each debater's plan (shown to user, not to opponent)

Phase 3: DEBATE  
  For each round i in 1..rounds:  
    → Pro debater speaks (sees: all previous public speeches \+ own plan)  
    → Con debater speaks (sees: all previous public speeches \+ own plan)  
      
    If replan\_after is set and i \== replan\_after:  
      → Pro debater replans (sees: all public speeches \+ own plan \+ own previous plan)  
      → Con debater replans (same)  
      → Continue debate with updated plans

Phase 4: JUDGING  
  → Multiple judge agents evaluate from different angles (see Section 4\)  
  → Output: structured evaluation document \+ winner declaration

Phase 5: SUMMARY  
  → Summarizer agent produces full debate analysis  
  → Output: comprehensive summary document  
\`\`\`

\*\*Context building for 1v1 debaters\*\*:

\`\`\`python  
def build\_context(self, event\_log: EventLog) \-\> list\[Message\]:  
    messages \= \[\]  
    \# System prompt with role, position, debate topic  
    messages.append(system\_prompt)  
    \# Own planning notes (private)  
    messages.extend(own\_plans)  
    \# All public speeches in chronological order  
    messages.extend(public\_speeches)  
    return messages  
\`\`\`

\#\#\# 3.2 Mode: 4v4

\*\*Participants\*\*:   
\- Pro team: 1 coach \+ 4 debaters (positions 1-4)  
\- Con team: 1 coach \+ 4 debaters (positions 1-4)

\*\*Parameters\*\*: Fixed 4 rounds. Round i features debater\_i vs debater\_i.

\*\*Flow\*\*:

\`\`\`  
Phase 1: TOPIC SETUP  
  → Same as 1v1

Phase 2: TEAM PREPARATION (both teams in parallel, invisible to each other)  
  For each team:  
    → Coach analyzes topic, drafts initial strategy  
    → Coach discusses with all 4 debaters:  
        \- Assigns focus areas to each debater  
        \- Debater 1: opening arguments, establish framework  
        \- Debater 2: evidence and examples  
        \- Debater 3: attack opponent's weaknesses  
        \- Debater 4: closing, synthesize and reinforce  
    → Each debater prepares their own notes based on coach's plan  
    → Output: team strategy document (visible to team only)

  Implementation of team prep discussion:  
    → Coach sends initial strategy → all debaters see it  
    → Each debater responds with their prepared approach  
    → Coach gives final instructions to each debater  
    → This is a structured 3-step discussion, not free-form chat

Phase 3: DEBATE (4 rounds)  
  For round\_num in 1..4:  
      
    \# Pre-round coaching (invisible to opponent)  
    → Pro coach gives instructions to pro\_debater\_{round\_num}  
      (sees: all public speeches so far \+ all own team internal comms)  
    → Con coach gives instructions to con\_debater\_{round\_num}  
      (sees: same for own team)  
      
    \# Debate exchange  
    → Pro debater {round\_num} speaks  
      (sees: all public speeches \+ own plan \+ coach's instruction for this round)  
    → Con debater {round\_num} speaks  
      (sees: same for own side)  
      
    \# Optional: multi-turn within a round  
    \# For v1: single exchange per round (pro speaks once, con speaks once)  
    \# Future: configurable sub-rounds per round

Phase 4: JUDGING  
  → Same as 1v1 but with richer content to evaluate

Phase 5: SUMMARY  
  → Same as 1v1  
\`\`\`

\*\*Context building for 4v4 debaters\*\*:

\`\`\`python  
def build\_context(self, event\_log: EventLog) \-\> list\[Message\]:  
    messages \= \[\]  
    messages.append(system\_prompt)  \# role, position, topic  
    messages.extend(team\_prep\_own\_parts)  \# own contributions in team prep  
    messages.extend(coach\_instructions\_to\_self)  \# coach's instructions to this debater  
    messages.extend(own\_planning\_notes)  \# private notes  
    messages.extend(all\_public\_speeches)  \# all public debate content  
    return messages  
\`\`\`

\*\*Context building for coaches\*\*:

\`\`\`python  
def build\_context(self, event\_log: EventLog) \-\> list\[Message\]:  
    messages \= \[\]  
    messages.append(system\_prompt)  
    messages.extend(all\_team\_internal\_comms)  \# full team discussion  
    messages.extend(own\_strategy\_notes)  \# private strategy  
    messages.extend(all\_public\_speeches)  \# all public debate content  
    return messages  
\`\`\`

\#\# 4\. Judging System

\#\#\# 4.1 Judge Agents

3 judge agents, each evaluating from a different angle:

| Judge | Angle | Focus |  
|---|---|---|  
| Logic Judge | 逻辑与论证 | Argument structure, logical consistency, fallacy detection, evidence quality |  
| Persuasion Judge | 说服力与表达 | Rhetorical effectiveness, audience impact, clarity, emotional appeal |  
| Clash Judge | 交锋与回应 | Direct engagement with opponent's arguments, rebuttal quality, adaptiveness |

Each judge sees ONLY public speeches (no internal team comms, no plans).

\#\#\# 4.2 Scoring

Each judge outputs:

\`\`\`python  
@dataclass  
class JudgeScore:  
    angle: str                    \# which angle this judge evaluates  
    pro\_score: float              \# 0-100  
    con\_score: float              \# 0-100  
    pro\_analysis: str             \# detailed analysis for pro side  
    con\_analysis: str             \# detailed analysis for con side  
    key\_moments: list\[str\]        \# notable moments in the debate  
    reasoning: str                \# why these scores  
\`\`\`

\#\#\# 4.3 Final Verdict

After all judges score:  
\- Aggregate scores (simple average or weighted — v1 uses simple average)  
\- Generate final evaluation document containing:  
  \- Per-judge detailed analysis  
  \- Aggregate scores  
  \- Winner declaration  
  \- Key turning points

Output format: Markdown document.

\#\# 5\. Post-Debate Summary

A separate Summarizer agent (not a judge) reads ALL public speeches and produces:

\- Debate overview: what was the core disagreement  
\- Argument map: key arguments from each side, how they were challenged  
\- Insight synthesis: what a reasonable person should take away — the "middle ground" or nuanced view  
\- Unanswered questions: what neither side adequately addressed

This is the core value proposition — "generating insight through opposition."

The summarizer's system prompt should emphasize: do NOT pick a side, synthesize both perspectives into actionable understanding.

\#\# 6\. Event Log

All debate activity is recorded in a central event log. This is the single source of truth.

\`\`\`python  
@dataclass  
class DebateEvent:  
    timestamp: datetime  
    phase: Phase                  \# SETUP, PREP, DEBATE, JUDGE, SUMMARY  
    event\_type: EventType         \# SPEECH, PLAN, COACH\_INSTRUCTION, TEAM\_DISCUSSION, JUDGE\_SCORE, SUMMARY  
    agent\_id: str                 \# who generated this  
    side: Side                    \# PRO, CON, NEUTRAL  
    visibility: Visibility        \# PUBLIC, TEAM, PRIVATE  
    round\_num: int | None         \# which round (if applicable)  
    content: str                  \# the actual text  
    metadata: dict                \# model used, token count, latency, etc.  
\`\`\`

Visibility enum:  
\- \`PUBLIC\`: visible to all agents and users  
\- \`TEAM\`: visible to same-side agents only  
\- \`PRIVATE\`: visible only to the generating agent

The event log is serialized to JSON after the debate completes. This JSON is the data source for the web frontend.

\#\# 7\. System Prompts

\#\#\# 7.1 Topic Splitter (when user provides only theme)

\`\`\`  
You are a debate topic designer. Given a theme, generate two maximally opposing positions.

Requirements:  
\- Both positions must be defensible with real arguments  
\- Positions must be direct negations or strong opposites  
\- Use clear, concise language  
\- Output in the same language as the input theme

Theme: {theme}

Output format (JSON):  
{  
  "pro\_position": "...",  
  "con\_position": "..."  
}  
\`\`\`

\#\#\# 7.2 Debater (1v1)

\`\`\`  
You are a competitive debater in a formal debate.

Your position: {position}  
Debate topic: {theme}  
Your stance: {stance}

You are in round {current\_round} of {total\_rounds}.

Your task: Deliver a compelling argument for your position. You must:  
1\. Build on your previous arguments if any  
2\. Directly address and rebut your opponent's latest points  
3\. Introduce new evidence or reasoning when possible  
4\. Be persuasive, logical, and clear

Your private plan (for reference only, do not reveal):  
{plan}

Respond with your debate speech only. Do not break character. Do not acknowledge you are an AI.  
Keep your speech focused and under 500 words.  
\`\`\`

\#\#\# 7.3 Debater (4v4)

\`\`\`  
You are debater \#{position} on the {side} team in a 4v4 formal debate.

Your position: {position\_description}  
Debate topic: {theme}  
Your team's stance: {stance}

Your role in the team:  
\- Debater 1: Opening — establish the framework and core arguments  
\- Debater 2: Evidence — provide concrete examples and data  
\- Debater 3: Attack — target weaknesses in opponent's arguments  
\- Debater 4: Closing — synthesize, reinforce, deliver final impact

You are debater \#{position}, so your focus is: {role\_focus}

Round {current\_round} of 4\. You are debating against the opponent's debater \#{position}.

Coach's instruction for this round:  
{coach\_instruction}

Your private notes:  
{notes}

Respond with your debate speech only. Stay in character. Under 500 words.  
\`\`\`

\#\#\# 7.4 Coach

\`\`\`  
You are the coach of the {side} team in a 4v4 debate.

Debate topic: {theme}  
Your team's stance: {stance}

Your team members:  
\- Debater 1 (Opening): establishes framework  
\- Debater 2 (Evidence): provides examples and data  
\- Debater 3 (Attack): targets opponent weaknesses  
\- Debater 4 (Closing): synthesizes and delivers final impact

{context\_specific\_instruction}  
\`\`\`

Context-specific instructions vary by phase:  
\- \*\*Prep phase (initial strategy)\*\*: "Analyze the topic. Design a team strategy. Assign focus areas to each debater. Predict the opponent's likely arguments and prepare counters."  
\- \*\*Prep phase (responding to debaters)\*\*: "Review your debaters' prepared approaches. Give final instructions and adjustments."  
\- \*\*Between rounds\*\*: "Based on the debate so far, give specific tactical instructions to debater \#{next\_round} for the upcoming round. What should they focus on? What opponent arguments need addressing?"

\#\#\# 7.5 Judge

\`\`\`  
You are a debate judge evaluating from the perspective of: {angle}

{angle\_description}

Debate topic: {theme}  
Pro position: {pro\_position}  
Con position: {con\_position}

Below is the complete debate transcript (public speeches only).

Evaluate both sides. Be fair and specific. Reference actual arguments made.

Output format (JSON):  
{  
  "pro\_score": \<0-100\>,  
  "con\_score": \<0-100\>,  
  "pro\_analysis": "...",  
  "con\_analysis": "...",  
  "key\_moments": \["...", "..."\],  
  "reasoning": "..."  
}  
\`\`\`

\#\#\# 7.6 Summarizer

\`\`\`  
You are an impartial analyst reviewing a completed debate.

Debate topic: {theme}  
Pro position: {pro\_position}  
Con position: {con\_position}

Your task is NOT to pick a winner. Your task is to synthesize both perspectives into actionable insight.

Produce a comprehensive analysis covering:  
1\. Core disagreement: What is the fundamental tension?  
2\. Argument map: Key arguments from each side and how they were challenged  
3\. Insight synthesis: What should a thoughtful person take away? Where is the nuanced truth?  
4\. Unanswered questions: What did neither side adequately address?  
5\. Practical implications: Based on this debate, what would you recommend to someone facing this decision?

Write in the same language as the debate. Be thorough but clear.  
\`\`\`

\#\# 8\. CLI Interface

\`\`\`bash  
\# Basic 1v1  
debate 1v1 \--topic "AI是否会取代人类" \--rounds 5

\# 1v1 with manual positions  
debate 1v1 \--pro "AI将在20年内取代大部分白领工作" \--con "AI永远无法取代人类的创造性工作" \--rounds 5

\# 1v1 with replan  
debate 1v1 \--topic "远程办公是否应该成为常态" \--rounds 8 \--replan-after 4

\# 4v4  
debate 4v4 \--topic "开源软件是否比商业软件更好"

\# Specify config file  
debate 1v1 \--topic "..." \--rounds 5 \--config models.yaml

\# Specify output  
debate 1v1 \--topic "..." \--rounds 5 \--output debate\_result.json

\# Web viewer (serves static files \+ opens browser)  
debate serve \--port 8080  
\`\`\`

CLI output during debate (v1: non-streaming, print after each agent completes):

\`\`\`  
🎯 Topic: AI是否会取代人类  
  ├─ Pro: AI将取代人类  
  └─ Con: AI不会取代人类

📋 Planning Phase  
  ├─ \[Pro\] Planning... ✓  
  └─ \[Con\] Planning... ✓

⚔️ Round 1/5  
  ├─ \[Pro\] (gpt-4o) ────────────────────  
  │  \<speech content\>  
  ├─ \[Con\] (claude-sonnet-4) ───────────  
  │  \<speech content\>

⚔️ Round 2/5  
  ...

📊 Judging  
  ├─ Logic Judge: Pro 72 / Con 78  
  ├─ Persuasion Judge: Pro 68 / Con 74  
  └─ Clash Judge: Pro 70 / Con 71

🏆 Winner: Con (avg: 74.3 vs 70.0)

📝 Summary saved to: debate\_result.json  
\`\`\`

\#\# 9\. Output Format (JSON)

The debate result JSON is the contract between CLI and web frontend.

\`\`\`json  
{  
  "version": "1.0",  
  "mode": "4v4",  
  "topic": {  
    "theme": "...",  
    "pro\_position": "...",  
    "con\_position": "..."  
  },  
  "config": {  
    "models": { ... }  
  },  
  "agents": \[  
    {  
      "id": "pro\_coach",  
      "role": "coach",  
      "side": "pro",  
      "position": 0,  
      "model": "gpt-4o"  
    },  
    {  
      "id": "pro\_debater\_1",  
      "role": "debater",  
      "side": "pro",  
      "position": 1,  
      "model": "gpt-4o"  
    }  
    // ... all agents  
  \],  
  "events": \[  
    {  
      "timestamp": "2026-03-16T03:00:00Z",  
      "phase": "PREP",  
      "event\_type": "TEAM\_DISCUSSION",  
      "agent\_id": "pro\_coach",  
      "side": "pro",  
      "visibility": "TEAM",  
      "round\_num": null,  
      "content": "...",  
      "metadata": {  
        "model": "gpt-4o",  
        "tokens\_in": 1200,  
        "tokens\_out": 800,  
        "latency\_ms": 3200  
      }  
    }  
    // ... all events in chronological order  
  \],  
  "judging": {  
    "scores": \[  
      {  
        "judge": "Logic Judge",  
        "angle": "逻辑与论证",  
        "pro\_score": 72,  
        "con\_score": 78,  
        "pro\_analysis": "...",  
        "con\_analysis": "...",  
        "key\_moments": \["..."\],  
        "reasoning": "..."  
      }  
      // ... 3 judges  
    \],  
    "final": {  
      "pro\_total": 70.0,  
      "con\_total": 74.3,  
      "winner": "con",  
      "verdict\_document": "..."  
    }  
  },  
  "summary": {  
    "content": "...",  
    "agent\_id": "summarizer",  
    "model": "gpt-4o"  
  },  
  "stats": {  
    "total\_tokens": 45000,  
    "total\_cost\_usd": 0.32,  
    "total\_duration\_seconds": 180,  
    "per\_agent\_stats": { ... }  
  }  
}  
\`\`\`

\#\# 10\. Project Structure

\`\`\`  
debate-arena/  
├── README.md  
├── pyproject.toml              \# project metadata, dependencies  
├── debate/  
│   ├── \_\_init\_\_.py  
│   ├── cli.py                  \# typer CLI entry point  
│   ├── config.py               \# YAML config loading, model resolution  
│   ├── models.py               \# dataclasses: DebateEvent, ModelConfig, AgentConfig, etc.  
│   ├── agents/  
│   │   ├── \_\_init\_\_.py  
│   │   ├── base.py             \# BaseAgent: LLM call, message history, context building  
│   │   ├── debater.py          \# Debater agent  
│   │   ├── coach.py            \# Coach agent  
│   │   ├── judge.py            \# Judge agent  
│   │   └── summarizer.py       \# Summarizer agent  
│   ├── engine/  
│   │   ├── \_\_init\_\_.py  
│   │   ├── event\_log.py        \# EventLog: central event store \+ visibility filtering  
│   │   ├── arena.py            \# DebateArena: orchestrates the full debate flow  
│   │   ├── mode\_1v1.py         \# 1v1 mode logic  
│   │   └── mode\_4v4.py         \# 4v4 mode logic  
│   ├── prompts/  
│   │   ├── \_\_init\_\_.py  
│   │   └── templates.py        \# all system prompt templates  
│   └── output/  
│       ├── \_\_init\_\_.py  
│       ├── formatter.py        \# CLI output formatting  
│       └── exporter.py         \# JSON export  
├── web/  
│   ├── index.html              \# single-page debate viewer  
│   ├── style.css  
│   └── app.js                  \# reads JSON, renders debate timeline  
├── examples/  
│   ├── config.yaml             \# example model config  
│   └── sample\_debate.json      \# example output for testing web viewer  
├── Dockerfile  
└── tests/  
    ├── test\_agents.py  
    ├── test\_engine.py  
    └── test\_config.py  
\`\`\`

\#\# 11\. Dependencies

\`\`\`  
httpx\>=0.27          \# async HTTP client for LLM API calls  
typer\>=0.12          \# CLI framework  
pyyaml\>=6.0          \# config file parsing  
rich\>=13.0           \# terminal output formatting  
jinja2\>=3.1          \# prompt template rendering  
\`\`\`

No LangChain. No LlamaIndex. No CrewAI. No agent frameworks.

\#\# 12\. LLM API Abstraction

Support OpenAI-compatible and Anthropic APIs. Most providers (DeepSeek, Groq, Together, local Ollama) use OpenAI-compatible format.

\`\`\`python  
class LLMClient:  
    """Unified LLM API client."""  
      
    async def chat(self, config: ModelConfig, messages: list\[Message\]) \-\> str:  
        if config.provider \== "anthropic":  
            return await self.\_call\_anthropic(config, messages)  
        else:  
            \# OpenAI-compatible (covers openai, deepseek, groq, ollama, etc.)  
            return await self.\_call\_openai\_compatible(config, messages)  
\`\`\`

\#\# 13\. Scope Boundaries

\#\#\# In scope (v1):  
\- 1v1 and 4v4 modes  
\- CLI with formatted output  
\- JSON export  
\- Static web viewer (reads JSON)  
\- Multi-model configuration  
\- 3-judge evaluation system  
\- Post-debate summary/insight generation  
\- Chinese and English support (follows input language)

\#\#\# Out of scope (v1):  
\- Streaming output  
\- Real-time web viewing  
\- Web search / RAG for evidence  
\- Voice output (TTS)  
\- User participation (playing as debater/coach)  
\- Persistent storage / debate history  
\- Authentication / multi-user

\#\#\# Future (v2+):  
\- Streaming CLI \+ real-time web via WebSocket  
\- Web search tool for debaters to find real evidence  
\- User plays as coach or debater  
\- Voice output for speeches  
\- Tournament mode (multiple debates, bracket)  
\- Custom judging criteria  
\- API server mode  
