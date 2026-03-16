---
status: pending
priority: p3
issue_id: "012"
tags: [code-review, api-design, agent-native]
dependencies: []
---

## Problem Statement

Individual agent endpoints were removed as a simplification, making agents only callable through the pipeline. While this reduces API surface area, it prevents independent agent execution, custom workflow composition, individual output retrieval, and programmatic access beyond the fixed pipeline.

## Findings

**Flagged by:** Agent-Native Reviewer

1. **No individual agent endpoints** — Agents can only be invoked through the pipeline orchestrator. This prevents:
   - Running agents independently for testing or targeted use.
   - Composing custom workflows that use a subset of agents.
   - Retrieving individual agent outputs without running the full pipeline.
   - Programmatic access patterns beyond the single pipeline flow.

2. **Missing supporting endpoints:**
   - `GET /pipeline/{run_id}/results` — No way to retrieve outputs after the SSE stream closes.
   - `GET /pipeline/{run_id}/status` — No polling fallback if SSE is unavailable or drops.
   - `POST /pipeline/{run_id}/cancel` — No way to cancel an in-progress pipeline run.
   - No pipeline run history or listing endpoint.

**Note on conflicting goals:** This conflicts with simplicity goals (see issue 011). For a demo, the pipeline-only API may be sufficient. However, for demonstrating "agent-native architecture" skills, individual endpoints are valuable and show that agents are first-class, independently addressable components.

## Proposed Solutions

1. **Restore individual agent endpoints** using `AGENT_REGISTRY` for dispatch:
   - `POST /api/v1/agents/{agent_name}` — Run a single agent with provided input.
   - Use the existing agent registry to look up and invoke the requested agent.

2. **Add supporting pipeline endpoints:**
   - `GET /api/v1/pipeline/{run_id}/results` — Return stored outputs for a completed run.
   - `GET /api/v1/pipeline/{run_id}/status` — Return current pipeline/agent state (polling fallback).
   - `POST /api/v1/pipeline/{run_id}/cancel` — Set a cancellation flag checked between agent steps.

## Technical Details

- The `AGENT_REGISTRY` already maps agent names to their implementations, so dispatch is straightforward.
- Individual agent endpoints need to handle input validation per agent type.
- Results storage requires keeping run outputs in memory (or a simple dict) beyond the SSE stream lifetime.
- Cancel requires a shared flag (e.g., `asyncio.Event`) checked between pipeline steps.
- Estimated cost: approximately 50-80 lines of router code for the core endpoints.

## Acceptance Criteria

- [ ] `POST /api/v1/agents/{agent_name}` endpoint exists and can invoke any registered agent independently.
- [ ] `GET /api/v1/pipeline/{run_id}/results` returns outputs for completed pipeline runs.
- [ ] `GET /api/v1/pipeline/{run_id}/status` returns current run state.
- [ ] `POST /api/v1/pipeline/{run_id}/cancel` cancels an in-progress run.
- [ ] All new endpoints include appropriate error handling (404 for unknown agents/runs, 409 for invalid state transitions).

## Work Log

_No work performed yet._

## Resources

- **Effort estimate:** Small-Medium
- **Flagged by:** Agent-Native Reviewer
- **Conflict:** Tension with simplicity goals (issue 011). Decision depends on project goal.
