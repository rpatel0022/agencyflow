---
status: pending
priority: p1
issue_id: "002"
tags: [code-review, architecture, api-contract, frontend]
dependencies: []
---

# SSE Event Schema Undefined

## Problem Statement

The entire real-time UX depends on Server-Sent Events (SSE), but NO event schema is defined in the plan. Without a defined schema, the frontend team cannot implement event handling, the backend team cannot implement event emission, and there is no contract to test against.

## Findings

- **Flagged by:** Spec Flow Analyzer, Performance Oracle (2 agents)
- The plan describes a real-time pipeline monitoring UX powered by SSE but provides zero specification for the event format.
- **Unanswered questions:**
  - What fields are included in each SSE event?
  - Are agent outputs delivered inline via SSE data, or must they be fetched separately via a GET endpoint?
  - What event types exist? Candidates include: `status_update`, `agent_complete`, `pipeline_failed`, `pipeline_complete` — but none are confirmed.
  - Does the server include event IDs (`id:` field) to support automatic reconnection and replay of missed events?
  - What is the `data:` payload format — raw JSON, stringified JSON, or something else?
- Without this schema, frontend and backend development cannot proceed in parallel and integration will require significant rework.

## Proposed Solutions

### Solution A: Define typed SSE event models in schemas.py (Recommended)

Create explicit Pydantic models for each SSE event type: `PipelineStatusEvent`, `AgentCompleteEvent`, `PipelineErrorEvent`, `PipelineCompleteEvent`. Include agent output inline for small agents; omit output for large agents and require separate fetch.

**Pros:**
- Provides a clear, typed contract between frontend and backend
- Pydantic models can be used for both serialization and documentation
- Inline output for small agents reduces round-trips and improves UX responsiveness
- Separate fetch for large outputs prevents SSE connection bloat

**Cons:**
- Requires defining a size threshold for inline vs. fetch-separately (adds a design decision)
- Typed models need to be kept in sync as agents evolve
- Slightly more complex implementation than a generic event format

### Solution B: Keep SSE for status only, add GET /pipeline/{run_id}/results for output retrieval

SSE events carry only status information (which agent is running, progress, completion, errors). All agent outputs are retrieved via a separate REST endpoint after completion.

**Pros:**
- Simpler SSE implementation — events are lightweight status strings
- Clear separation of concerns: SSE for status, REST for data
- No risk of SSE connection issues from large payloads

**Cons:**
- Frontend must poll or wait for completion event before fetching results
- Higher latency for the user — cannot see partial results as agents complete
- More HTTP requests overall
- Loses the "real-time results streaming" feel

### Recommendation

**Solution A** — Define typed event models. The real-time UX is a core feature; keeping agent outputs inline (when small) preserves the live-updating experience that the plan envisions.

## Technical Details

- **Affected components:** `schemas.py` (new event models), SSE endpoint handler, frontend event listener
- **Proposed event types:**
  - `status_update` — Agent started/in-progress (fields: `run_id`, `agent_name`, `status`, `timestamp`)
  - `agent_complete` — Agent finished (fields: `run_id`, `agent_name`, `status`, `output` (optional inline), `output_url` (if fetched separately), `timestamp`)
  - `pipeline_failed` — Pipeline error (fields: `run_id`, `failed_agent`, `error_message`, `timestamp`)
  - `pipeline_complete` — All agents done (fields: `run_id`, `status`, `summary`, `timestamp`)
- **Reconnection:** Server should include monotonically increasing `id:` field; client uses `Last-Event-ID` header on reconnect
- **Data format:** JSON-serialized Pydantic models in the `data:` field

## Acceptance Criteria

- [ ] SSE event types are enumerated and documented
- [ ] Pydantic models defined for each event type in `schemas.py`
- [ ] Each event model includes: `run_id`, `event_type`, `timestamp`, and type-specific fields
- [ ] Decision documented on inline vs. fetch-separately threshold for agent outputs
- [ ] Event `id:` field included for reconnection replay support
- [ ] Frontend event handler types match backend event models
- [ ] At least one integration test validates SSE event format end-to-end

## Work Log

| Date | Author | Note |
|------|--------|------|
| 2026-02-28 | Plan Review | Issue identified during P1 critical review |

## Resources

- SSE specification: https://html.spec.whatwg.org/multipage/server-sent-events.html
- Spec Flow Analyzer review notes
- Performance Oracle review notes
- Current plan sections referencing real-time UX
