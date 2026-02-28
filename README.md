# AgencyFlow

Multi-agent AI platform that automates marketing agency campaign workflows. Five specialized AI agents handle different parts of the campaign lifecycle — brief parsing, audience research, content calendars, performance reporting, and creative briefs — orchestrated through a FastAPI backend and visualized on a React dashboard.

**Built for:** Ayzenberg Group — social-first brand acceleration agency.

## Architecture

```
                    ┌─────────────┐
                    │  React SPA  │  (Vite + TypeScript)
                    │   :5173     │
                    └──────┬──────┘
                           │ SSE + REST
                    ┌──────▼──────┐
                    │   FastAPI   │
                    │   :8000     │
                    └──────┬──────┘
                           │
                ┌──────────▼──────────┐
                │ Pipeline Orchestrator│
                │    (DAG Runner)      │
                └──────────┬──────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
   │Brief Parser │ │  Audience   │ │  Content    │
   │             │ │ Researcher  │ │  Calendar   │
   └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
                    ┌──────▼──────┐
                    │asyncio.gather│
                    ├──────┬──────┤
               ┌────▼───┐ ┌▼────────────┐
               │Creative│ │ Performance │
               │ Brief  │ │  Reporter   │
               └────────┘ └─────────────┘
```

**Pipeline DAG:** Brief Parser → Audience Research → Content Calendar → (Creative Brief + Performance Reporter in parallel)

**Key patterns:**
- Agents are stateless async functions with Pydantic-typed I/O
- Pipeline runs as a background `asyncio.Task` with SSE event streaming
- Token bucket rate limiter at 12 RPM (Gemini free tier safety margin)
- Pre-computed demo mode for instant presentations without API calls

## Tech Stack

- **Backend:** Python 3.12+ / FastAPI / Pydantic v2
- **Frontend:** React 19 / Vite / TypeScript (strict mode)
- **AI:** Google Gemini (`gemini-2.0-flash`) via `google-genai` SDK
- **Design:** "Luxury Editorial" — Instrument Serif + DM Mono, warm dark palette, gold accent

## Setup

### Prerequisites

- Python 3.12+
- Node.js 18+
- Google Gemini API key ([get one free](https://aistudio.google.com/apikey))

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "GEMINI_API_KEY=your-key-here" > .env

# Start the API server
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`. Health check: `GET /api/v1/health`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The dashboard opens at `http://localhost:5173`. The Vite dev server proxies `/api` requests to the backend.

### Demo Mode

Click "Demo" in the header to load pre-computed outputs instantly — no API key needed for the frontend demo.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/pipeline/run` | Start pipeline (text or file upload) → 202 + run_id |
| `GET` | `/api/v1/pipeline/stream/{run_id}` | SSE stream of pipeline events |
| `POST` | `/api/v1/pipeline/demo` | Pre-computed demo outputs (no LLM) |
| `GET` | `/api/v1/health` | Health check |

## Running Tests

```bash
# All tests (set GEMINI_API_KEY to any value for tests — they mock the client)
GEMINI_API_KEY=test python -m pytest tests/ -q

# Single test file
GEMINI_API_KEY=test python -m pytest tests/test_pipeline.py -q
```

## Project Structure

```
app/
├── agents/          # 5 agent functions (brief_parser, audience, calendar, creative, performance)
├── routers/         # FastAPI route handlers (pipeline, health)
├── services/        # Pipeline orchestrator (DAG execution, SSE events)
├── schemas.py       # All Pydantic models (agent I/O, pipeline state)
├── gemini_client.py # Gemini API client with rate limiting + retry
├── file_parser.py   # PDF/TXT file extraction
├── config.py        # Environment settings
└── main.py          # FastAPI app entrypoint

frontend/src/
├── components/      # React components (Dashboard, outputs, upload, progress)
├── hooks/           # usePipeline (SSE), useApi (REST)
├── types/           # TypeScript interfaces mirroring backend schemas
└── styles/          # CSS design system

data/
├── precomputed/     # Demo JSON outputs
└── sample_metrics.json
```
