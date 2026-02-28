# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
Global rules (compound engineering, user preferences) live in `~/.claude/CLAUDE.md`.

## Project Overview

AgencyFlow — multi-agent AI platform automating marketing agency campaign workflows for Ayzenberg Group. Five specialized agents (Brief Parser, Audience Research, Content Calendar, Creative Brief, Performance Reporter) orchestrated through a FastAPI backend, visualized on a React dashboard, powered by Google Gemini free tier.

## Commands

```bash
# Activate virtual environment (always do this first)
source .venv/bin/activate

# Run all tests
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_gemini_client.py -v

# Run a single test by name
python -m pytest tests/test_gemini_client.py -k "test_generate_retries_on_429" -v

# Start backend (dev mode with reload)
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Start frontend (when created)
cd frontend && npm run dev

# Install dependencies
pip install -r requirements.txt
```

## Architecture

**Backend pipeline flow:**
```
POST /api/v1/pipeline/run (multipart: file or text)
  → Brief Parser → Audience Research → Content Calendar → Creative Brief
  → Performance Reporter (runs in parallel via asyncio.gather)
  → SSE events pushed to GET /api/v1/pipeline/stream/{run_id}
```

**Key architectural decisions:**
- **Plain async agent functions**, not a class hierarchy. Each agent is `async def agent_name(input: TInput, client: LLMClient) -> TOutput`
- **Single `app/schemas.py`** — all 15+ Pydantic models in one file (~240 lines). Don't split.
- **`LLMClient` Protocol** (`app/gemini_client.py`) — dependency injection for testing. Agents accept a client, never instantiate one.
- **`GeminiClient`** wraps `google-genai` SDK with token bucket rate limiter (12 RPM) and exponential backoff with jitter on 429/503
- **Config** via pydantic-settings (`app/config.py`), reads `.env`. App fails fast on missing `GEMINI_API_KEY`.
- **SSE** (not polling) for real-time pipeline progress to frontend

**SDK gotcha:** Use `google-genai` (NOT `google-generativeai`). The structured output field is `response_schema` not `response_json_schema`. See `docs/solutions/integration-issues/google-genai-structured-output-field-name.md`.

## Conventions

- **Pydantic v2 everywhere:** `ConfigDict(str_strip_whitespace=True)`, `Field()` with constraints on all fields, `StrEnum` for statuses
- **Async throughout:** No blocking calls in async context. CPU-bound work (PDF parsing) runs in `ThreadPoolExecutor`
- **Feature branches** off `main`, PRs with summary + testing notes
- **pytest config** in `pyproject.toml`: `asyncio_mode = "auto"`, testpaths = `["tests"]`

## Knowledge Base

- `docs/solutions/` — Project-specific solved problems. Check here before debugging.
- `docs/plans/` — Implementation plans. Check off items as completed.
- `docs/brainstorms/` — Design exploration context.
- `todos/` — Review findings (P1/P2/P3).
