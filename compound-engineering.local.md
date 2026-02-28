---
review_agents:
  - kieran-python-reviewer
  - kieran-typescript-reviewer
  - security-sentinel
  - performance-oracle
  - architecture-strategist
  - code-simplicity-reviewer
---

## Review Context

AgencyFlow is a Python FastAPI + React/TypeScript multi-agent AI platform for marketing agencies.

**Backend:** Python 3.12, FastAPI, Pydantic v2, google-genai SDK, async throughout.
**Frontend:** React + Vite + TypeScript (strict), custom CSS design system.
**AI:** Google Gemini gemini-2.0-flash via structured output. Token bucket rate limiter at 12 RPM.

**Key patterns:**
- Plain async agent functions (no class hierarchy)
- Single schemas.py with all Pydantic models
- LLMClient Protocol for dependency injection
- SSE for real-time pipeline progress
- Delimiter-based prompt injection resistance

**Review focus areas:**
- Pydantic v2 best practices (ConfigDict, Field constraints, StrEnum)
- Async correctness (no blocking calls in async context)
- google-genai SDK usage (check docs/solutions/ for known gotchas)
- Security: prompt injection, file upload validation, API key handling
- Keep it simple — this is a demo project, not enterprise software
