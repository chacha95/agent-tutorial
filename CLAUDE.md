# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run the Gradio web UI (accessible at http://127.0.0.1:7860)
uv run python src/app.py

# Run all tests
uv run pytest -v

# Run a single test file
uv run pytest tests/test_pipeline.py -v

# Run a single test
uv run pytest tests/test_models.py::test_name -v
```

## Environment Setup

Copy `.env.local` (preferred) or `.env` with:
```
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
```

`.env.local` takes precedence over `.env`. Both are gitignored.

## Architecture

This is a **PydanticAI multi-agent tutorial** that generates YouTube Shorts content from a keyword.

### Pipeline Flow

```
keyword → Research Agent (Tavily search) → TrendData
        → Writer Agent                   → ShortsScript
        → Editor Agent                   → ContentPackage
        → Gradio UI
```

The three agents chain via `model_dump_json()` — PydanticAI agents communicate via text/JSON strings, not Python objects. Passing a Python object directly to `agent.run()` will fail; always serialize with `.model_dump_json()` first.

### Module Responsibilities

| File | PydanticAI Concept | Purpose |
|---|---|---|
| `src/models.py` | Structured Output | Pydantic output schemas (`TrendData`, `ShortsScript`, `ContentPackage`) |
| `src/deps.py` | Dependency Injection | `AppDeps` dataclass loaded from env vars; accessed via `ctx.deps` in tools |
| `src/agents.py` | Multi-Agent | Three `Agent` instances with `output_type` declared |
| `src/tools.py` | Tool Use | `@research_agent.tool` registers Tavily search on the research agent |
| `src/pipeline.py` | Agent Chaining | Orchestrates the three agents sequentially |
| `src/app.py` | Gradio UI | Async Gradio callbacks calling `run_pipeline()` |

### Critical Import Order

`pipeline.py` imports `src.tools` explicitly to register the Tavily tool on `research_agent`. The correct import chain is: `agents.py` → `tools.py` → `pipeline.py`. If `tools.py` is not imported before running the pipeline, the research agent will have no tools.

### Async Pattern

Gradio 4+ natively supports `async def` callbacks — do **not** use `asyncio.run()` inside Gradio callbacks (event loop is already running). The Tavily SDK is synchronous; it's wrapped with `asyncio.to_thread()` in `tools.py` to avoid blocking.

### Testing

Tests use `conftest.py` with `autouse=True` to inject fake API keys via `monkeypatch`, so no real API calls are made in unit tests. `pytest-asyncio` is configured with `asyncio_mode = "auto"` (no `@pytest.mark.asyncio` needed on individual tests).
