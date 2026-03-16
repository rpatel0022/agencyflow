---
status: pending
priority: p1
issue_id: "004"
tags: [code-review, architecture, ux, state-management]
dependencies: []
---

# Retry Behavior and Post-Failure State Transitions Undefined

## Problem Statement

The plan mentions a "Retry" button in the frontend that appears on pipeline failure, but does not define what retry means. Additionally, post-failure state transitions are undefined in the state machine, leaving open questions about run lifecycle management after errors.

## Findings

- **Flagged by:** Spec Flow Analyzer, Agent-Native Reviewer (2 agents)
- The plan references a retry mechanism in the frontend but does not specify:
  - **Full restart vs. resume:** Does clicking "Retry" restart the entire pipeline with a new UUID and re-process everything from scratch? Or does it resume from the failed step, requiring persisted intermediate outputs?
  - **Run identity:** Does a retry create a new `run_id` or reuse the failed one?
  - **Intermediate output persistence:** If resuming, where are intermediate agent outputs stored? How long are they retained?
- **Post-failure state machine gaps:**
  - Can a new pipeline run be started after a failure, or does the failed run block new runs?
  - Is the failed run still considered "active" for the purpose of 409 Conflict responses?
  - What is the valid state transition from `failed`? Is it `failed -> queued` (retry) or `failed -> (terminal)` with a new run?
- Without these definitions, the frontend retry button behavior is ambiguous and the backend state management may have bugs around concurrent/blocked runs.

## Proposed Solutions

### Solution A: Full restart with new UUID (Recommended)

Clicking "Retry" triggers a completely new pipeline run with a new `run_id`. The failed run is marked as terminal. The button label says "Restart Pipeline" to set correct user expectations.

**Pros:**
- Simple implementation — no intermediate state persistence needed
- Clean state management — each run is independent and immutable once terminal
- No ambiguity about which outputs belong to which run
- Failed state is terminal; new runs are always allowed after failure
- Appropriate for demo scope

**Cons:**
- Re-processes all agents from scratch, even those that succeeded before the failure
- Slightly slower recovery if the failure occurred late in the pipeline
- May feel wasteful to users if most agents had already completed

### Solution B: Resume from failed step

Persist intermediate agent outputs. On retry, skip already-completed agents and resume from the one that failed.

**Pros:**
- Faster recovery — only re-runs the failed agent and subsequent ones
- Better UX for long pipelines where early agents are expensive
- More sophisticated error recovery

**Cons:**
- Requires intermediate output persistence (storage, retention policy, cleanup)
- Complex state management — must track per-agent completion status within a run
- Risk of stale intermediate data if the brief or context has changed
- Must handle edge cases: what if the agent's input schema changed? What if a dependency agent's output is corrupted?
- Significant implementation complexity for demo scope

### Solution C: Hybrid approach

Default to full restart, but allow resume for specific known-safe failure modes (e.g., transient network errors on the last agent).

**Pros:**
- Gets the simplicity of Solution A for most cases
- Enables optimization for specific scenarios

**Cons:**
- Most complex to implement and reason about
- Overkill for demo scope
- Must classify failure modes as "resumable" vs. "non-resumable"

### Recommendation

**Solution A** — Full restart with new UUID. For demo scope, simplicity and correctness are more important than optimization. The pipeline is not so long that restarting from scratch is a significant cost.

## Technical Details

- **State machine update:**
  - `failed` is a terminal state (no transitions out)
  - A new run can always be started regardless of whether a previous run is in `failed` state
  - Only `queued` or `running` states should trigger 409 Conflict
  - Valid terminal states: `completed`, `failed`
- **Frontend behavior:**
  - On `pipeline_failed` SSE event, show error message and "Restart Pipeline" button
  - Button triggers a new `POST /api/v1/pipeline/run` with the same brief content
  - New `run_id` is returned; frontend subscribes to new SSE stream
  - Previous failed run's UI state can be dismissed or kept for reference
- **Backend behavior:**
  - Failed runs are immutable — no state changes after `failed`
  - 409 Conflict only applies when a run is in `queued` or `running` state
  - No intermediate output persistence required in v1

## Acceptance Criteria

- [ ] Retry behavior is explicitly defined as full restart (new UUID, new run)
- [ ] State machine updated: `failed` is terminal, does not block new runs
- [ ] 409 Conflict logic only checks for `queued` or `running` states, not `failed`
- [ ] Frontend "Retry" button is labeled "Restart Pipeline"
- [ ] Frontend sends a new `POST /api/v1/pipeline/run` on retry, with original brief content
- [ ] Frontend subscribes to new SSE stream for the new run
- [ ] Post-failure state transitions are documented in the state machine diagram
- [ ] Edge case tested: start new run after a failed run completes without 409

## Work Log

| Date | Author | Note |
|------|--------|------|
| 2026-02-28 | Plan Review | Issue identified during P1 critical review |

## Resources

- Spec Flow Analyzer review notes
- Agent-Native Reviewer review notes
- Current plan sections referencing retry UX and state machine
- State machine diagram (to be updated)
