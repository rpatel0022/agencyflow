---
status: pending
priority: p2
issue_id: "008"
tags: [code-review, architecture, state-management, sse]
dependencies: []
---

# Pipeline State Machine Gaps

## Problem Statement

Multiple gaps exist in the pipeline state management specification. The REPORTING state exists in the enum but is not represented in the state machine transitions. The Performance Reporter runs in parallel with the main chain, but there is no way to represent concurrent states. SSE event specifications for the reporter versus the main chain are missing. Post-failure transitions and demo mode SSE behavior are undefined.

**Flagged by:** Architecture Strategist, Performance Oracle, Spec Flow Analyzer (3 agents)

**Effort:** Medium.

## Findings

1. **REPORTING state unreachable:** The state enum includes REPORTING but the state machine transition map has no edges leading to or from it. The Performance Reporter runs as a parallel task, meaning two states would need to be active simultaneously, which a simple linear state machine cannot represent.
2. **SSE event ambiguity:** No specification for what SSE event types fire for the reporter versus the main pipeline chain. The frontend cannot distinguish between "main chain progressed" and "reporter finished."
3. **Post-failure transitions undefined:** When a pipeline run fails, can a new run start? The state machine does not define a transition from FAILED back to IDLE or to a new run.
4. **Demo mode SSE simulation unspecified:** Does demo mode skip progress animation entirely, simulate it with rapid-fire events, or use a different event stream?

## Proposed Solutions

### Solution A: Parallel Event Streams with Separate Namespaces (Recommended)

Emit separate SSE event types for the main pipeline (`pipeline:progress`, `pipeline:complete`) and the reporter (`reporter:progress`, `reporter:complete`). The pipeline state machine tracks the main chain; the reporter has its own independent status.

**Pros:**
- Clean separation of concerns; frontend can render them independently.
- No need to model concurrency in the state machine -- each stream is linear.
- Easy to extend with additional parallel tasks later.

**Cons:**
- Frontend must handle two event streams and reconcile them for overall status.
- More SSE event types to document and test.

### Solution B: Composite State with Substates

Extend the state machine to support composite states: `ANALYZING(reporter=RUNNING)`, `COMPLETE(reporter=RUNNING)`, etc.

**Pros:**
- Single state machine captures the full system state.
- Easier to reason about the complete pipeline status at any point.

**Cons:**
- State explosion: each main state times each reporter state.
- More complex transition logic.
- Overkill if the reporter is the only parallel task.

### Solution C: Sequential Reporter Execution

Run the Performance Reporter after the main chain completes instead of in parallel.

**Pros:**
- Eliminates the concurrency problem entirely.
- Simple linear state machine with REPORTING as the final step before COMPLETE.

**Cons:**
- Increases total pipeline duration (reporter cannot start early).
- Wastes time if the reporter could have been working while later agents ran.

## Technical Details

### State Machine Transitions (Solution A)

```
Main pipeline:
  IDLE -> ANALYZING -> STRATEGIZING -> CREATING -> COMPLETE
  Any -> FAILED

Reporter (independent):
  IDLE -> RUNNING -> COMPLETE
  Any -> FAILED

Post-failure:
  FAILED -> IDLE  (triggered by new POST /api/pipeline/run)
```

### SSE Event Types

```
pipeline:state_change   { state: "ANALYZING", agent: "market_analyst" }
pipeline:agent_complete { agent: "market_analyst", duration_ms: 1234 }
pipeline:complete       { run_id: "...", duration_ms: 5678 }
pipeline:error          { error_type: "rate_limit", message: "..." }

reporter:start          { run_id: "..." }
reporter:complete       { run_id: "...", metrics: {...} }
reporter:error          { error_type: "...", message: "..." }
```

### Demo Mode Behavior

```
- Demo mode emits the same SSE event types as live mode.
- Events fire with 200-500ms delays to simulate real progress.
- Frontend renders identically; the only difference is data source.
```

## Acceptance Criteria

- [ ] State machine transition map includes all states in the enum, with no unreachable states.
- [ ] Post-failure transition is defined: FAILED allows new runs (transition to IDLE on new POST).
- [ ] SSE event types are specified for both the main pipeline and the reporter, with distinct namespaces.
- [ ] Demo mode SSE behavior is documented: rapid-fire events with simulated delays.
- [ ] Frontend can distinguish reporter events from main pipeline events.
- [ ] Integration tests verify state transitions for: happy path, failure, failure-then-retry, and demo mode.

## Work Log

| Date | Author | Note |
|------|--------|------|
| 2026-02-28 | Plan Review | Issue identified during plan review by 3 agents |

## Resources

- [SSE specification](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [State machine design patterns](https://refactoring.guru/design-patterns/state)
