# AI Debate Arena

CLI-first multi-agent AI debate system with 1v1 and 4v4 modes, JSON export, and a static web viewer.

## Stack

- Python 3.10+
- `typer` for CLI
- `httpx` for async LLM calls
- `rich` for terminal rendering
- Static `web/` viewer with plain HTML/CSS/JS

## Quick Start

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -e .[dev]
```

Create a config file based on [`examples/config.yaml`](examples/config.yaml) and provide API secrets via environment variables.

Recommended direct DashScope setup:

```bash
$env:AI_DEBATE_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:AI_DEBATE_API_KEY="your-key"
$env:AI_DEBATE_MODEL="qwen-plus"
```

Run a 1v1 debate:

```bash
debate 1v1 --topic "AI是否会取代人类" --rounds 3 --config examples/config.yaml --model your-model
```

Run a 4v4 debate:

```bash
debate 4v4 --topic "开源软件是否比商业软件更好" --config examples/config.yaml --model your-model
```

Start the static viewer:

```bash
debate serve --port 8080
```

## Testing

```bash
pytest
ruff check .
```

Optional live smoke test:

```bash
$env:AI_DEBATE_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:AI_DEBATE_API_KEY="your-key"
$env:AI_DEBATE_MODEL="qwen-plus"
pytest -q
```

## Notes

- LLM calls default to OpenAI-compatible APIs.
- Anthropic is supported through a dedicated request path.
- The project keeps tests deterministic with mocked transports; live API tests are opt-in.
