---
title: "feat: Build AgencyFlow Multi-Agent Campaign Automation Platform"
type: feat
status: active
date: 2026-02-28
origin: docs/brainstorms/2026-02-28-agencyflow-multi-agent-platform-brainstorm.md
deepened: 2026-02-28
---

# feat: Build AgencyFlow Multi-Agent Campaign Automation Platform

## Enhancement Summary

**Deepened on:** 2026-02-28
**Sections enhanced:** 12
**Review agents used:** Frontend Design, Architecture Strategist, Python Reviewer, TypeScript Reviewer, Code Simplicity Reviewer, Performance Oracle, Security Sentinel, Pattern Recognition Specialist

### Key Improvements
1. **Typed everything** — Replaced all `dict` fields with proper Pydantic models (`ChannelAnalysis`, `MetricSummary`, `ChannelStrategy`). Every field now has constraints.
2. **Security-first prompts** — Delimiter-based prompt templates to resist injection. File upload hardening with size/type validation.
3. **Performance-realistic** — Token bucket rate limiter at 12 RPM (not 15), SSE for pipeline status (not polling), parallel Performance Reporter execution.
4. **Simplified architecture** — Reduced from ~35 to ~25 files. Plain agent functions + shared `call_gemini()` helper instead of class hierarchy. Merged test structure.
5. **Design system** — "Luxury Editorial" aesthetic with Instrument Serif + DM Mono, warm dark palette, gold accent. Professional agency feel.
6. **Pipeline modeled as DAG** — Acknowledged fan-in at Creative Brief agent. Explicit state machine for pipeline status.

### Key Tensions Resolved
- **Simplicity vs Structure**: The Code Simplicity Reviewer recommended plain functions; the Architecture/Python reviewers recommended Generic BaseAgent. **Resolution: Plain functions with a `call_gemini()` helper.** For a 5-agent demo, a class hierarchy is over-engineering. Each agent is a single async function with typed I/O.
- **Schema files**: Simplicity reviewer said merge all schemas into one file; Python reviewer said keep separate. **Resolution: One `schemas.py` file.** With 5 agents and ~15 models, one file is ~200 lines — manageable and easier to navigate.
- **PDF support**: Simplicity reviewer flagged PDF as stretch goal. **Resolution: Keep PDF but implement it simply.** pdfplumber is one function call. Worth it for demo impact ("upload a real PDF brief").

---

## Overview

Build AgencyFlow — a multi-agent AI platform that automates marketing agency campaign workflows. Five specialized AI agents handle different parts of the campaign lifecycle (brief parsing, audience research, content calendars, performance reporting, creative briefs), orchestrated through a FastAPI backend and visualized on a React dashboard. Powered by Google Gemini free tier. Designed as a portfolio demo project tailored to Ayzenberg Group's business.

## Problem Statement

Marketing agencies like Ayzenberg Group spend significant hours on repetitive campaign workflows: parsing client briefs, researching audiences, building content calendars, generating reports, and writing creative briefs. Each of these tasks follows predictable patterns that AI agents can automate, freeing agency teams to focus on creative strategy. AgencyFlow demonstrates this automation end-to-end. (see brainstorm: docs/brainstorms/2026-02-28-agencyflow-multi-agent-platform-brainstorm.md)

## Proposed Solution

A full-stack platform with:
- **Backend:** Python FastAPI with 5 agent functions, each with typed Pydantic I/O
- **Frontend:** React + Vite dashboard for triggering pipelines and viewing outputs
- **AI:** Google Gemini `gemini-2.0-flash` via `google-genai` SDK (free tier)
- **Architecture:** Orchestrated DAG pipeline with a central pipeline service
- **Demo mode:** Pre-computed outputs for reliable presentations + live API mode

## Technical Approach

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Dashboard                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │ Upload   │ │ Pipeline │ │ Agent    │ │ Demo Mode │  │
│  │ Brief    │ │ Progress │ │ Outputs  │ │ Toggle    │  │
│  └────┬─────┘ └──────────┘ └──────────┘ └───────────┘  │
│       │              SSE /api/v1/pipeline/stream →       │
└───────┼──────────────────────────────────────────────────┘
        │
┌───────▼──────────────────────────────────────────────────┐
│                   FastAPI Backend (:8000)                  │
│                                                           │
│  ┌─────────┐    ┌─────────────────────────────────────┐  │
│  │ Routers │───>│        Pipeline Service               │  │
│  │ /api/v1 │    │                                     │  │
│  └─────────┘    │  Brief Parser ──> Audience Research  │  │
│                 │       │                              │  │
│  ┌─────────┐   │       ▼                              │  │
│  │ Gemini  │<──│  Content Calendar ──> Creative Brief  │  │
│  │ Client  │   │                                       │  │
│  │ (token  │   │  Performance Reporter (parallel)      │  │
│  │ bucket) │   └─────────────────────────────────────┘  │
│  └─────────┘                                             │
│                                                           │
│  ┌──────────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ Schemas      │  │ Config   │  │ Sample Data      │   │
│  │ (Pydantic)   │  │ Settings │  │ (demo briefs)    │   │
│  └──────────────┘  └──────────┘  └──────────────────┘   │
└───────────────────────────────────────────────────────────┘
```

### Research Insights: Architecture

**Pipeline is a linear chain with accumulated state:**
The main pipeline is sequential: Brief Parser → Audience Research → Content Calendar → Creative Brief. Each step depends on prior steps' outputs. The pipeline service must accumulate outputs as it progresses (not just pipe the previous step's output forward), because Creative Brief needs data from all three prior agents. Performance Reporter runs in parallel as an independent branch.

**LLM Client Protocol:**
Define a `LLMClient` protocol (Python `Protocol` class) so Gemini is not hardcoded:
```python
class LLMClient(Protocol):
    async def generate(self, prompt: str, response_schema: type[BaseModel]) -> dict: ...
```
This enables swapping to OpenAI/Anthropic later and makes testing trivial (inject a mock client).

**Retry lives in ONE place:**
The Gemini client handles rate limiting and retry. Agent functions do NOT retry — they call `call_gemini()` and let errors propagate to the pipeline service.

**Pipeline State Machine:**
```
idle → parsing → researching → calendaring → briefing → complete (terminal)
                                                       ↘ failed (terminal)
```
- Each state transition emits an SSE `status_update` event.
- `complete` and `failed` are **terminal states** — no transitions out.
- 409 Conflict only applies to **active** (non-terminal) states: `parsing`, `researching`, `calendaring`, `briefing`.
- New runs are always allowed after `complete` or `failed`.

**Retry behavior (on failure):**
- Frontend shows a **"Restart Pipeline"** button (not "Retry") to set correct expectations.
- Clicking it triggers a new `POST /pipeline/run` with the same brief content → new UUID, new SSE stream.
- This is a full restart — no intermediate state persistence. Simple and correct for demo scope.
- The failed run's outputs (any completed agents before failure) remain visible until the new run starts.

### Pipeline Design

**Main Pipeline (linear chain with fan-in at Creative Brief):**
```
Upload Brief ──> Brief Parser ──> Audience Research ──> Content Calendar ──> Creative Brief Generator
```
Each step depends on all prior outputs. Creative Brief receives accumulated data from Brief Parser + Audience Research + Calendar Summary. The main chain is sequential — no parallelism within it.

**Independent Branch (runs in parallel):**
```
Sample Metrics ──> Performance Reporter ──> Executive Report
```
The Performance Reporter runs concurrently with the main pipeline when metrics data is provided, saving ~14 seconds per full run.

**Agent Communication:** Each agent is an async function with typed Pydantic input/output. The pipeline service calls them, passing outputs as inputs. No message queue — clean function calls. (see brainstorm: resolved question #2)

### Research Insights: Pipeline Performance

**Rate Limit Math:**
- Free tier: 15 RPM. With 4s fixed spacing = 15 RPM exactly. Zero margin.
- **Use token bucket at 12 RPM** (20% safety margin) instead of fixed spacing.
- Realistic pipeline time: 5 agents × (rate limit wait + 5-15s API latency) = **60-120 seconds**.
- Running Performance Reporter in parallel saves one full agent cycle (~14s).

**SSE over Polling:**
- Pipeline emits only 5-6 status updates total. Polling wastes HTTP round-trips.
- FastAPI SSE is ~20 lines of code. Frontend uses native `EventSource` API.
- Eliminates the polling interval decision (too slow = laggy, too fast = wasteful).

**Schema Summarization for Downstream Agents:**
The Creative Brief agent receives all prior outputs. A 4-week calendar at 3 posts/week across 3 channels = ~36 CalendarEntry objects (8 fields each). This inflates the Gemini prompt to 3,000-5,000 tokens before the instruction.
- Create a `CalendarSummary` to pass to Creative Brief (just strategy + rationale, not all entries).

### Project Structure

```
agencyflow/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app, CORS, exception handler, lifespan
│   │   ├── config.py                  # Settings via pydantic-settings (validates GEMINI_API_KEY)
│   │   ├── schemas.py                 # ALL Pydantic models (agents + pipeline + errors)
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── pipeline.py            # POST /run, GET /stream/{run_id}, POST /demo
│   │   │   └── health.py              # GET /health
│   │   ├── agents/
│   │   │   ├── __init__.py            # AGENT_REGISTRY dict for dynamic dispatch
│   │   │   ├── brief_parser.py        # async def parse_brief(input, client) -> Output
│   │   │   ├── audience_researcher.py # async def research_audience(input, client) -> Output
│   │   │   ├── content_calendar.py    # async def generate_calendar(input, client) -> Output
│   │   │   ├── creative_brief.py      # async def generate_creative_brief(input, client) -> Output
│   │   │   └── performance_reporter.py# async def generate_report(input, client) -> Output
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── gemini_client.py       # GeminiClient: token bucket rate limiter, retry w/ jitter
│   │   │   ├── pipeline_orchestrator.py # Pipeline DAG execution, state machine, SSE
│   │   │   └── file_parser.py         # PDF/text extraction (thread pool, size limit)
│   │   └── data/
│   │       ├── sample_brief.txt       # Pre-loaded demo brief
│   │       ├── sample_brief.pdf       # Pre-loaded demo brief PDF
│   │       ├── sample_metrics.json    # Pre-loaded campaign metrics
│   │       └── precomputed/           # Pre-computed agent outputs for demo mode
│   │           ├── brief_parsed.json
│   │           ├── audience.json
│   │           ├── calendar.json
│   │           ├── creative_brief.json
│   │           └── performance.json
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_agents.py             # All 5 agents (mock gemini_client)
│   │   ├── test_pipeline.py           # Pipeline orchestration + state machine
│   │   ├── test_schemas.py            # Pydantic validation + constraints
│   │   └── test_gemini_client.py      # Rate limiter, retry, backoff
│   ├── pyproject.toml
│   ├── requirements.txt               # Pinned versions
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── components/
│   │   │   ├── Dashboard.tsx          # Main layout
│   │   │   ├── BriefUpload.tsx        # File upload + text paste
│   │   │   ├── PipelineProgress.tsx   # Vertical step list with SSE updates
│   │   │   ├── BriefOutput.tsx        # Brief parser: structured key-value pairs
│   │   │   ├── AudienceOutput.tsx     # Audience: persona cards
│   │   │   ├── CalendarOutput.tsx     # Calendar: table/grid view
│   │   │   ├── CreativeBriefOutput.tsx# Creative brief: formatted document
│   │   │   ├── PerformanceOutput.tsx  # Performance: metrics + insights
│   │   │   ├── WelcomeState.tsx       # Initial empty state with CTA
│   │   │   └── DemoToggle.tsx         # Switch between live/demo mode
│   │   ├── hooks/
│   │   │   ├── usePipeline.ts        # SSE connection + pipeline state
│   │   │   └── useApi.ts             # Typed API client functions
│   │   ├── types/
│   │   │   ├── agents.ts             # Agent I/O types (mirrors Pydantic)
│   │   │   └── pipeline.ts           # Pipeline state types
│   │   └── styles/
│   │       └── index.css
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json                  # strict: true
├── README.md
└── .gitignore                         # .env, *.env, node_modules, __pycache__, .venv
```

### Research Insights: Project Structure

**Changes from original (~35 files → ~25 files):**
- Merged 6 schema files into 1 `schemas.py` (~200 lines total — manageable)
- Removed `dependencies.py` (unnecessary for this scope — inject GeminiClient directly)
- Removed individual agent endpoints router (`agents.py`) — agents are only called through the pipeline
- Renamed `services/pipeline.py` → `services/pipeline_orchestrator.py` to avoid name collision with `routers/pipeline.py`
- Split `AgentOutput.tsx` into 5 per-agent output components (each renders differently)
- Split `types/index.ts` into `types/agents.ts` + `types/pipeline.ts`
- Added `hooks/usePipeline.ts` for SSE connection management
- Added `test_gemini_client.py` (rate limiter is complex enough to warrant its own tests)
- Added agent registry in `agents/__init__.py` for clean dispatch

**Agent Registry Pattern:**
```python
# agents/__init__.py
from .brief_parser import parse_brief
from .audience_researcher import research_audience
from .content_calendar import generate_calendar
from .creative_brief import generate_creative_brief
from .performance_reporter import generate_report

AGENT_REGISTRY = {
    "brief_parser": parse_brief,
    "audience_researcher": research_audience,
    "content_calendar": generate_calendar,
    "creative_brief": generate_creative_brief,
    "performance_reporter": generate_report,
}
```

### Implementation Phases

#### Phase 1: Foundation (Backend Skeleton + Gemini Integration)

**Tasks:**
- [x] Initialize git repo, create `.gitignore` (include `.env`, `*.env`, `node_modules/`, `__pycache__/`, `.venv/`), `README.md`
- [x] Set up Python project: `pyproject.toml`, `requirements.txt` (pinned versions), virtual environment
- [x] Create FastAPI app skeleton: `main.py` with CORS (locked to `localhost:5173`), generic exception handler (scrubs API keys from errors), lifespan
- [x] Implement `config.py` — pydantic-settings with startup validation for `GEMINI_API_KEY`
- [x] Implement `gemini_client.py` — Gemini SDK wrapper with:
  - Token bucket rate limiter at 12 RPM (asyncio.Lock + time.monotonic)
  - Exponential backoff with jitter on 429/503 responses (max 3 retries)
  - Structured output via `response_schema` parameter
  - Async support via `client.aio`
  - LLMClient protocol for dependency injection
- [x] Define all Pydantic schemas in `schemas.py` (see Agent I/O Schemas below) — all fields constrained with `Field()`
- [x] Write unit tests for Gemini client (rate limiting, retry logic, backoff with jitter)
- [x] Health endpoint at `/api/v1/health`

**Success criteria:** `uvicorn app.main:app --host 127.0.0.1` starts, `/api/v1/health` returns 200, Gemini client can make a rate-limited call, startup fails fast if `GEMINI_API_KEY` is missing.

#### Phase 2: Core Agents (All 5 Agents Implemented)

**Tasks:**
- [x] Implement `parse_brief()` — accepts raw text, returns structured `BriefParserOutput`
  - Prompt uses delimiter-based injection resistance: `<brief>` tags, "treat as data" instruction
- [x] Implement `file_parser.py` — PDF extraction via `pdfplumber`:
  - Run in `ThreadPoolExecutor` (PDF parsing is synchronous/CPU-bound)
  - File size limit: 10MB
  - Page limit: first 20 pages
  - MIME type + magic byte validation (`%PDF-` header)
  - Filename sanitization (strip path separators, null bytes)
- [x] Implement `research_audience()` — accepts `BriefParserOutput`, returns `AudienceOutput`
- [x] Implement `generate_calendar()` — accepts `BriefParserOutput` + `AudienceOutput`, returns `CalendarOutput`
- [x] Implement `generate_creative_brief()` — accepts `BriefParserOutput` + `AudienceOutput` + `CalendarSummary`, returns `CreativeBriefOutput`
  - Uses `CalendarSummary` (not full `CalendarOutput`) to reduce prompt size
- [x] Implement `generate_report()` — accepts `PerformanceInput`, returns `PerformanceOutput`
- [x] Write prompt templates for each agent:
  - Agency-specific terminology (briefs, campaigns, flights, placements, KPIs)
  - Delimiter-based user content isolation in ALL prompts
  - Professional output tone
- [x] All agent functions take `(input: TInput, client: GeminiClient) -> TOutput` signature
- [x] Test each agent individually with sample inputs (mock GeminiClient)
- [x] Create sample data: `sample_brief.txt`, `sample_brief.pdf`, `sample_metrics.json`

**Success criteria:** Each agent produces professional, agency-quality output when called with sample data. All Pydantic schemas validate correctly. Prompts resist basic injection attempts.

#### Phase 3: Pipeline Orchestration + API Routes

**Tasks:**
- [x] Implement `pipeline_orchestrator.py`:
  - DAG execution: Brief Parser → (Audience Research) → Content Calendar → Creative Brief
  - Fan-in: Creative Brief receives accumulated outputs from prior steps
  - Parallel branch: Performance Reporter runs via `asyncio.gather` with main pipeline
  - Pipeline state machine: `idle → parsing → researching → calendaring → briefing → complete | failed`
  - Run ID (UUID) returned from POST, used for SSE streaming
  - `asyncio.Lock` around state mutations (prevent torn reads)
  - Reject concurrent runs with HTTP 409 Conflict
- [x] Implement `routers/pipeline.py`:
  - `POST /api/v1/pipeline/run` — see API Contract below
  - `GET /api/v1/pipeline/stream/{run_id}` — SSE endpoint, pushes events per SSE Event Schemas
  - `POST /api/v1/pipeline/demo` — runs pipeline with pre-computed outputs (instant)

**API Contract for `POST /api/v1/pipeline/run`:**
- **Content-Type:** `multipart/form-data`
- **Fields:**
  - `file` (optional, `UploadFile`): PDF or TXT brief. Max 10MB. Validated: extension + magic bytes.
  - `text` (optional, `Form(str)`): Plain text brief. 10–50,000 characters.
  - At least one of `file` or `text` must be provided. `file` takes precedence if both sent.
- **Success:** `202 Accepted` → `{"run_id": "uuid", "status": "parsing"}`
- **Errors:**
  - `422 Unprocessable Entity`: Neither field provided, or invalid file format
  - `409 Conflict`: Pipeline already running (non-terminal state)
  - `413 Payload Too Large`: File exceeds 10MB
- **Performance Reporter:** Always runs with bundled `sample_metrics.json` in v1. No user-provided metrics in initial scope.
- [x] Add file upload handling with validation (size limit, type check)
- [x] Generate pre-computed demo outputs (run pipeline once, save JSON outputs)
- [x] Write integration tests for pipeline + routes
- [x] Add `AgentError` schema for structured error responses

**Success criteria:** Full pipeline runs via API: upload brief → get all 5 agent outputs. Demo mode returns instant results. SSE pushes status updates in real-time. Concurrent run attempts return 409.

#### Phase 4: React Dashboard

**Tasks:**
- [x] Initialize React + Vite + TypeScript project with `strict: true` in tsconfig
- [x] Configure Vite proxy to FastAPI backend
- [x] Create TypeScript types in `types/agents.ts` and `types/pipeline.ts` mirroring backend schemas
- [x] Build `WelcomeState` — "Upload Brief" CTA + "Try Demo" button
- [x] Build `BriefUpload` — file drop zone (PDF only, 10MB limit) + text paste area
- [x] Build `PipelineProgress` — vertical step list with:
  - Agent name + status (pending/running/complete/failed)
  - Checkmark for completed, spinner for active, red X for failed
  - Elapsed time display
  - Connected via SSE (`usePipeline` hook wraps `EventSource`)
- [x] Build 5 per-agent output components:
  - `BriefOutput.tsx` — structured key-value pairs, highlights missing fields
  - `AudienceOutput.tsx` — persona cards with channel tags
  - `CalendarOutput.tsx` — table/grid view grouped by week
  - `CreativeBriefOutput.tsx` — formatted document layout
  - `PerformanceOutput.tsx` — metrics summary + channel breakdown
- [x] Build `Dashboard` layout — sidebar with pipeline steps, main content shows selected output
- [x] Build `DemoToggle` — switch between live API and pre-computed demo mode
- [x] All string rendering uses React's default JSX escaping (never `dangerouslySetInnerHTML`)
- [x] Style with design system (see Design System section below)
- [x] Test full user flow: upload → SSE progress → outputs

**Success criteria:** Full demo flow works in browser. Dashboard looks professional. Demo mode loads instantly. SSE updates feel real-time.

#### Phase 5: Polish, Testing, and Demo Prep

**Tasks:**
- [ ] Handle edge cases: empty brief, missing fields, API timeout, malformed PDF
- [ ] Add loading states and error states to all UI components
- [ ] Write comprehensive README: setup instructions, architecture diagram, demo guide
- [ ] Create a demo script: what to show, in what order, talking points
- [ ] Run full end-to-end test with a realistic agency brief
- [ ] Polish agent prompts for output quality
- [ ] Run `pip audit` and `npm audit` for dependency vulnerabilities
- [ ] Final UI polish pass
- [ ] Test prompt injection resistance (try common injection patterns, verify they fail)

**Success criteria:** The platform can be demo'd in a 10-minute meeting with zero crashes, professional output quality, and a clear narrative.

## Agent I/O Schemas

All schemas in a single `app/schemas.py` file. All string fields have `max_length`. All numeric fields have `ge`/`le` bounds. All models use `model_config = ConfigDict(str_strip_whitespace=True)`.

### BriefParserAgent

```python
# app/schemas.py
from pydantic import BaseModel, Field, ConfigDict
from enum import StrEnum
import datetime

class BriefParserInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    raw_text: str = Field(..., min_length=10, max_length=50_000)
    source_filename: str | None = Field(None, max_length=255, pattern=r'^[a-zA-Z0-9_\-\.]+$')

class BriefParserOutput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    campaign_name: str = Field(..., max_length=200)
    client_name: str = Field(..., max_length=200)
    objectives: list[str]
    target_audience: str = Field(..., max_length=2000)
    budget: str | None = Field(None, max_length=200)
    timeline: str = Field(..., max_length=500)
    kpis: list[str]
    channels: list[str]
    key_messages: list[str]
    constraints: list[str]
    raw_summary: str = Field(..., max_length=1000)
    missing_fields: list[str]
```

### AudienceResearchAgent

```python
class Persona(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(..., max_length=100)          # "Social-Savvy Sarah"
    age_range: str = Field(..., max_length=20)       # "25-34"
    description: str = Field(..., max_length=500)
    motivations: list[str]
    pain_points: list[str]
    preferred_channels: list[str]
    content_preferences: list[str]

class AudienceOutput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    personas: list[Persona]                          # 2-3 personas
    targeting_recommendations: list[str]
    audience_size_estimate: str = Field(..., max_length=200)
    key_insights: list[str]
    suggested_tone: str = Field(..., max_length=200)
```

### ContentCalendarAgent

```python
class CalendarEntry(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    week: int = Field(..., ge=1, le=52)
    day: str = Field(..., max_length=20)
    channel: str = Field(..., max_length=50)
    content_type: str = Field(..., max_length=50)
    topic: str = Field(..., max_length=200)
    caption_hook: str = Field(..., max_length=500)
    hashtags: list[str]
    notes: str = Field(..., max_length=500)

class ChannelStrategy(BaseModel):
    """Typed replacement for dict[str, str]"""
    channel: str = Field(..., max_length=50)
    strategy: str = Field(..., max_length=500)

class CalendarOutput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    campaign_duration: str = Field(..., max_length=100)
    posting_frequency: str = Field(..., max_length=100)
    entries: list[CalendarEntry]
    channel_strategies: list[ChannelStrategy]
    content_mix_rationale: str = Field(..., max_length=1000)

class CalendarSummary(BaseModel):
    """Condensed version passed to Creative Brief agent (reduces prompt size)"""
    campaign_duration: str
    posting_frequency: str
    channel_strategies: list[ChannelStrategy]
    content_mix_rationale: str
```

### CreativeBriefAgent

```python
class CreativeBriefInput(BaseModel):
    brief_data: BriefParserOutput
    audience_data: AudienceOutput
    calendar_summary: CalendarSummary       # Summary, not full calendar

class CreativeBriefOutput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    project_name: str = Field(..., max_length=200)
    prepared_for: str = Field(..., max_length=200)
    date: datetime.date                      # Proper date type, not str
    background: str = Field(..., max_length=2000)
    objective: str = Field(..., max_length=1000)
    target_audience_summary: str = Field(..., max_length=1000)
    key_message: str = Field(..., max_length=500)
    supporting_messages: list[str]
    tone_and_voice: str = Field(..., max_length=500)
    visual_direction: str = Field(..., max_length=1000)
    deliverables: list[str]
    timeline_summary: str = Field(..., max_length=500)
    success_metrics: list[str]
    mandatory_inclusions: list[str]
```

### PerformanceReporterAgent

```python
class ChannelMetrics(BaseModel):
    channel: str = Field(..., max_length=50)
    impressions: int = Field(..., ge=0, le=10_000_000_000)
    reach: int = Field(..., ge=0, le=10_000_000_000)
    engagement_rate: float = Field(..., ge=0.0, le=100.0)
    clicks: int = Field(..., ge=0, le=10_000_000_000)
    conversions: int = Field(..., ge=0, le=10_000_000_000)
    spend: float = Field(..., ge=0.0, le=100_000_000)

class PerformanceInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    campaign_name: str = Field(..., max_length=200)
    reporting_period: str = Field(..., max_length=100)
    channel_metrics: list[ChannelMetrics]
    goals: list[str]

class ChannelAnalysis(BaseModel):
    """Typed replacement for list[dict]"""
    channel: str = Field(..., max_length=50)
    performance_rating: str = Field(..., max_length=50)   # "Strong", "Moderate", "Weak"
    key_metric: str = Field(..., max_length=200)
    insight: str = Field(..., max_length=500)
    recommendation: str = Field(..., max_length=500)

class MetricSummary(BaseModel):
    """Typed replacement for dict[str, str]"""
    metric_name: str = Field(..., max_length=100)
    value: str = Field(..., max_length=100)
    trend: str = Field(..., max_length=50)                # "up", "down", "stable"

class PerformanceOutput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    executive_summary: str = Field(..., max_length=2000)
    overall_performance: str = Field(..., max_length=50)   # "On track" / "Below target" / "Exceeding"
    channel_analysis: list[ChannelAnalysis]
    top_performing_content: list[str]
    recommendations: list[str]
    next_steps: list[str]
    key_metrics_summary: list[MetricSummary]
```

### Pipeline Schemas

```python
class PipelineStatus(StrEnum):
    IDLE = "idle"
    PARSING = "parsing"
    RESEARCHING = "researching"
    CALENDARING = "calendaring"
    BRIEFING = "briefing"
    REPORTING = "reporting"
    COMPLETE = "complete"
    FAILED = "failed"

class PipelineRunResponse(BaseModel):
    run_id: str
    status: PipelineStatus

class AgentError(BaseModel):
    agent_name: str
    error_type: str       # "rate_limit", "timeout", "validation", "api_error"
    message: str
    retryable: bool
```

### SSE Event Schemas

Each SSE event is JSON-serialized in the `data:` field. Events include a monotonically increasing `id:` field for reconnection replay via `Last-Event-ID`.

```python
class SSEEvent(BaseModel):
    """Base for all SSE events."""
    id: int                                  # Monotonic, for reconnection replay
    run_id: uuid.UUID
    timestamp: datetime.datetime

class PipelineStatusEvent(SSEEvent):
    event_type: Literal["status_update"] = "status_update"
    agent_name: str
    status: PipelineStatus
    elapsed_ms: int

class AgentCompleteEvent(SSEEvent):
    event_type: Literal["agent_complete"] = "agent_complete"
    agent_name: str
    output: dict                             # Agent output JSON (inline for all agents)

class ReporterStatusEvent(SSEEvent):
    """Separate event for Performance Reporter (runs in parallel)."""
    event_type: Literal["reporter_status"] = "reporter_status"
    status: PipelineStatus                   # "reporting" | "complete" | "failed"
    output: dict | None = None               # Included on completion

class PipelineErrorEvent(SSEEvent):
    event_type: Literal["pipeline_failed"] = "pipeline_failed"
    failed_agent: str
    error: AgentError

class PipelineCompleteEvent(SSEEvent):
    event_type: Literal["pipeline_complete"] = "pipeline_complete"
```

**SSE behavior:**
- Agent outputs are delivered **inline** as they complete (each is <50KB — small enough).
- On client reconnect, server replays all events after the client's `Last-Event-ID`.
- Connecting mid-pipeline returns current state as the first event, then streams new events.
- Performance Reporter uses separate `reporter_status` event type (parallel to main chain).
- Pipeline continues running even if the SSE client disconnects.

## Design System

### Research Insights: Frontend Design

**Aesthetic: "Luxury Editorial / Refined Brutalism"**

This should NOT look like a generic SaaS dashboard. It should feel like a high-end agency portfolio piece.

**Typography:**
- Headings: Instrument Serif (Google Fonts) — editorial, warm, authoritative
- Body/data: DM Mono (Google Fonts) — technical precision, clean
- Agent output text: DM Sans (Google Fonts) — readable body copy

**Color Palette:**
```css
:root {
  --bg-primary: #0F0D0B;        /* Warm near-black */
  --bg-surface: #1A1714;        /* Card backgrounds */
  --bg-elevated: #242019;       /* Hover states, active elements */
  --text-primary: #E8E2D9;      /* Warm off-white */
  --text-secondary: #9B9080;    /* Muted labels */
  --accent-gold: #C8A96E;       /* Primary accent — antique gold */
  --accent-gold-dim: #8B7545;   /* Secondary accent */
  --status-success: #7BAE6E;    /* Olive green for completed */
  --status-running: #C8A96E;    /* Gold for active */
  --status-error: #C26E6E;      /* Muted red for failed */
  --border: #2A2520;            /* Subtle borders */
}
```

**Component Styling Principles:**
- **Pipeline Progress:** Vertical step list (not horizontal stepper). Each step is a row: status dot → agent name → elapsed time. Active step has a gold pulsing dot. Completed steps have an olive checkmark.
- **Agent Output Cards:** Full-width, stacked vertically. Each card has the agent name in DM Mono as a label, output content below. No unnecessary borders or shadows.
- **Brief Upload:** Large drop zone with dashed gold border. "Drop PDF here" in Instrument Serif. Text paste area below as a simple textarea.
- **Demo Toggle:** Small pill toggle in the top-right. "Live" / "Demo" labels.
- **Welcome State:** Centered vertically. Instrument Serif headline "AgencyFlow" with a one-line description. Two buttons: "Upload Brief" (gold) and "Try Demo" (outline).

**Anti-patterns to avoid:**
- No gradient buttons, no blue, no shadcn/ui defaults
- No sidebar navigation (single-page flow is enough)
- No loading skeletons (SSE updates are fast enough)
- No card shadows (use subtle borders only)

## Alternative Approaches Considered

1. **BrandPilot (Brand Consistency Engine)** — Deep but narrow. Only one agent, less impressive architecturally. Rejected because breadth matters more for showing AI engineering skill. (see brainstorm: Phase 2 — Approach B)

2. **CampaignForge (Brief Generator)** — More content generation than workflow automation. Less aligned with Ayzenberg's automation focus. Rejected because the goal is to show business understanding, not just AI content generation. (see brainstorm: Phase 2 — Approach C)

3. **Using LangChain/CrewAI/AutoGen** — Framework overhead adds complexity without benefit for a 5-agent sequential pipeline. Raw Python + Pydantic is simpler, more debuggable, and shows you understand the underlying patterns rather than just using a framework. If asked about frameworks, can explain the trade-off.

4. **Message queue architecture** — Redis/RabbitMQ for agent communication. Over-engineered for a demo. Direct function calls are simpler and right-sized. Can explain the upgrade path to queues for scaling. (see brainstorm: resolved question #2)

5. **BaseAgent class hierarchy** — Generic `BaseAgent[TInput, TOutput]` with `run()`, `build_prompt()`, `parse_response()` template methods. Rejected as over-engineering for 5 agents. Plain functions with a shared `call_gemini()` helper are simpler, more readable, and just as testable. Less code to understand.

## System-Wide Impact

### Interaction Graph

This is a greenfield project — no existing systems are affected. Internally:
- User uploads file → `file_parser` extracts text (in ThreadPoolExecutor) → `pipeline_orchestrator` calls agent functions as a DAG
- Each agent call → `gemini_client.generate()` → token bucket rate limiter → Gemini API → Pydantic validation
- Pipeline status transitions → SSE event pushed to frontend → UI updates instantly

### Error & Failure Propagation

**Rule: Main pipeline chain stops on failure. Independent branches run regardless.**

- Gemini API 429 (rate limit) → `gemini_client` retries with exponential backoff + jitter (max 3 attempts) → if still failing, raises error → pipeline marks step as failed → SSE emits `pipeline_failed` event → frontend shows error with "Restart Pipeline" button
- Gemini API returns malformed JSON → Pydantic validation catches it → raises `AgentError(retryable=True)` → pipeline marks step as failed
- PDF parsing failure → `file_parser` raises error → pipeline does not start → frontend shows "Could not parse this file" message
- Network timeout → `gemini_client` has 30s timeout → retries once → raises error
- **Linear chain failure:** If Brief Parser fails, no downstream agents run (they need its output). Pipeline stops at the failed step.
- **Independent branch:** Performance Reporter failure does not affect the main pipeline.

### State Lifecycle Risks

- All state is in-memory — server restart loses everything. Acceptable for demo.
- Pipeline runs are NOT concurrent — one run at a time. Second run attempt returns HTTP 409 Conflict (only for active/non-terminal states). New runs are always allowed after `complete` or `failed`.
- Each run has a UUID. State mutations are protected by `asyncio.Lock` to prevent torn reads during SSE streaming.
- Previous run state is cleared when a new run starts.
- Pre-computed demo outputs are static JSON files — no risk of corruption.

### API Surface Parity

Only one interface: the FastAPI REST API + SSE. Frontend consumes it. No other clients.

### Integration Test Scenarios

1. **Full pipeline with sample brief** — Upload `sample_brief.txt`, verify all 5 agents produce valid outputs, verify SSE events fire in correct order
2. **Demo mode** — Trigger demo endpoint, verify pre-computed outputs load instantly, verify frontend renders them
3. **Rate limit simulation** — Make 16 rapid Gemini calls, verify token bucket queues them correctly and none fail with 429
4. **Bad file upload** — Upload a corrupt PDF / oversized file / non-PDF, verify graceful error message
5. **Concurrent run rejection** — Start a pipeline, immediately POST another run, verify 409 response
6. **Prompt injection attempt** — Upload brief containing "Ignore all previous instructions...", verify output is still valid structured data

## Acceptance Criteria

### Functional Requirements

- [ ] Full pipeline runs: upload brief → Brief Parser → Audience Research → Content Calendar → Creative Brief
- [ ] Performance Reporter runs in parallel with main pipeline when metrics provided
- [ ] Each agent produces professional, agency-quality output with marketing terminology
- [ ] Demo mode loads pre-computed outputs instantly (no API calls)
- [ ] PDF and plain text brief uploads are supported (10MB limit, PDF type validation)
- [ ] Dashboard shows step-by-step pipeline progress via SSE (not polling)
- [ ] Each agent's output is formatted with a dedicated component (not raw JSON)
- [ ] Concurrent pipeline run attempts return 409 Conflict

### Non-Functional Requirements

- [ ] Full pipeline completes in under 2 minutes (live mode, with parallel Performance Reporter)
- [ ] Demo mode loads in under 1 second
- [ ] Dashboard uses design system (Instrument Serif, dark palette, gold accent)
- [ ] No crashes on common error cases (bad file, API timeout, rate limit, prompt injection)
- [ ] Codebase has clear separation: routers / services / agents / schemas
- [ ] All Pydantic fields have constraints (max_length, ge/le, pattern)

### Quality Gates

- [ ] Unit tests for Gemini client (token bucket rate limiting, retry with jitter)
- [ ] Unit tests for each agent (mock GeminiClient, validate Pydantic output)
- [ ] Integration test for full pipeline including SSE events
- [ ] README with setup instructions, architecture diagram, and demo guide
- [ ] All agent prompts produce consistent, professional output quality
- [ ] `pip audit` and `npm audit` pass with no critical vulnerabilities

## Success Metrics

- **Demo-ability:** Can run a complete demo in 10 minutes showing upload → SSE progress → outputs
- **Output quality:** Agent outputs read like professional agency deliverables, not AI slop
- **Code quality:** Clean architecture, typed throughout (zero `dict` fields), testable, follows FastAPI best practices
- **Business relevance:** Uses Ayzenberg/agency terminology, mirrors real campaign workflows
- **Reliability:** Demo mode provides zero-failure fallback for live presentations
- **Security baseline:** Prompts resist injection, files are validated, errors don't leak keys

## Dependencies & Prerequisites

| Dependency | Purpose | Install |
|-----------|---------|---------|
| Python 3.11+ | Runtime | System |
| Node.js 18+ | React frontend | System |
| `google-genai` | Gemini API SDK | `pip install google-genai` |
| `fastapi` | Backend framework | `pip install fastapi` |
| `uvicorn` | ASGI server | `pip install uvicorn` |
| `pydantic` | Data validation | Included with FastAPI |
| `pydantic-settings` | Config management | `pip install pydantic-settings` |
| `python-multipart` | File uploads | `pip install python-multipart` |
| `pdfplumber` | PDF text extraction | `pip install pdfplumber` |
| `sse-starlette` | SSE support | `pip install sse-starlette` |
| React + Vite | Frontend | `npm create vite@latest` |
| TypeScript | Frontend types | Included with Vite template |
| `GEMINI_API_KEY` | API access | https://aistudio.google.com/apikey |

## Risk Analysis & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Gemini rate limits hit during demo | High | Critical | Pre-computed demo mode. Token bucket at 12 RPM (not 15). Parallel Performance Reporter saves one cycle. |
| Agent output quality inconsistent | Medium | High | Iterate on prompts. Use structured output (`response_schema`). Test with multiple briefs. |
| Prompt injection corrupts output | Medium | High | Delimiter-based prompts. Pydantic validation rejects garbage. Input length limits. |
| PDF parsing produces garbage | Medium | Medium | Use `pdfplumber` in ThreadPoolExecutor. File size + type validation. Fall back to text paste. |
| Gemini free tier changes/removed | Low | Critical | Architecture uses LLMClient protocol — swap to any provider. |
| React dashboard looks generic | Medium | Medium | Custom design system (Instrument Serif, dark palette, gold accent). No shadcn/ui defaults. |
| Pipeline takes too long for live demo | Medium | High | Demo mode bypasses API entirely. Live mode shows SSE progress to manage expectations. Parallel execution saves ~14s. |
| API key leaked in error messages | Medium | Medium | Generic exception handler scrubs all errors. Never log full key. |

## Future Considerations

These are explicitly **out of scope** but could be mentioned in a conversation with Ayzenberg:
- **Soulmates.ai integration** — Feed Audience Research output into Soulmates.ai digital twins for audience testing
- **Real ad platform integrations** — Connect to Meta Ads, Google Ads APIs for live campaign data
- **Multi-user collaboration** — Auth + team workspaces
- **Campaign history** — Database persistence with SQLite/PostgreSQL
- **Message queue architecture** — Redis-based agent communication for scale
- **Streaming output** — Token-by-token streaming for agent output display (currently SSE is status-only)

## Documentation Plan

- [ ] `README.md` — Project overview, quick start, architecture diagram, demo guide, "no auth — localhost only" warning
- [ ] `.env.example` — Required environment variables with masked example key
- [ ] Inline code comments for complex prompt templates
- [ ] API auto-docs via FastAPI's built-in Swagger UI at `/docs`

## Sources & References

### Origin

- **Brainstorm document:** [docs/brainstorms/2026-02-28-agencyflow-multi-agent-platform-brainstorm.md](docs/brainstorms/2026-02-28-agencyflow-multi-agent-platform-brainstorm.md) — Key decisions carried forward: Python FastAPI + React stack, Google Gemini free tier, direct API call pipeline, no auth, local demo, 5-agent scope

### External References

- FastAPI project structure: https://fastapi.tiangolo.com/tutorial/bigger-applications/
- FastAPI CORS: https://fastapi.tiangolo.com/tutorial/cors/
- FastAPI SSE: https://github.com/sysid/sse-starlette
- google-genai SDK: https://googleapis.github.io/python-genai/
- Gemini rate limits: https://ai.google.dev/gemini-api/docs/rate-limits
- Gemini structured output: https://ai.google.dev/gemini-api/docs/structured-output
- Pydantic v2: https://docs.pydantic.dev/latest/
- Vite proxy config: https://vitejs.dev/config/server-options.html#server-proxy

### Company Research

- Ayzenberg Group: https://www.ayzenberg.com/ — Social-first brand acceleration agency
- Soulmates.ai: https://soulmates.ai/ — AI-powered audience research + digital twins platform (BrandOS, HEXACO framework, 93% fidelity score)
- Ayzenberg AI: https://ayzenberg.ai/ — Marketing consultant AI tool
