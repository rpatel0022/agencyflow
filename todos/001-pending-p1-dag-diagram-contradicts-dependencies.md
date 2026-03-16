---
status: pending
priority: p1
issue_id: "001"
tags: [code-review, architecture, pipeline]
dependencies: []
---

# DAG Diagram Contradicts Actual Agent Dependencies

## Problem Statement

The pipeline DAG diagram shows Brief Parser fanning out to BOTH Audience Research AND Content Calendar in parallel. However, Content Calendar's input schema requires `AudienceOutput`, meaning it MUST wait for Audience Research to complete. The diagram is misleading — the main pipeline is actually linear: Brief Parser -> Audience Research -> Content Calendar -> Creative Brief.

## Findings

- **Flagged by:** Architecture Strategist, Performance Oracle, Spec Flow Analyzer (3 agents)
- The DAG diagram visually implies that Audience Research and Content Calendar can execute concurrently after Brief Parser completes.
- Content Calendar's input schema declares a dependency on `AudienceOutput`, which is only available after Audience Research finishes.
- This means the true execution order is a linear chain, not a parallel fan-out.
- Any developer or stakeholder reading the diagram will have an incorrect mental model of the pipeline's concurrency characteristics.

## Proposed Solutions

### Solution A: Fix the diagram to show linear chain (Recommended)

Update the DAG diagram to accurately reflect the sequential dependency chain: Brief Parser -> Audience Research -> Content Calendar -> Creative Brief.

**Pros:**
- Simple, low-effort change
- Accurately represents the runtime behavior
- Eliminates confusion for developers and reviewers
- No code changes required, documentation-only fix

**Cons:**
- Reveals that the pipeline has less parallelism than initially implied
- May prompt questions about whether more parallelism should be designed in

### Solution B: Remove Audience Research dependency from Content Calendar to enable true parallelism

Redesign Content Calendar so it does not require `AudienceOutput` as an input, enabling it to run in parallel with Audience Research.

**Pros:**
- Achieves actual parallel execution, improving pipeline throughput
- Makes the diagram truthful without changing it

**Cons:**
- Significant design change to Content Calendar agent
- Content Calendar may produce lower-quality output without audience data
- Increases complexity of the pipeline orchestration
- Requires careful validation that output quality is acceptable

### Recommendation

**Solution A** — Fix the diagram. The dependency exists for a good reason (Content Calendar needs audience data to produce relevant schedules). Misrepresenting the architecture is worse than having a linear pipeline.

## Technical Details

- **Affected component:** Pipeline DAG diagram in plan documentation
- **Input schema dependency:** `ContentCalendarInput` requires `AudienceOutput` (audience segments, preferences, demographics)
- **Actual execution order:** Brief Parser -> Audience Research -> Content Calendar -> Creative Brief
- **Diagrammed execution order (incorrect):** Brief Parser -> [Audience Research, Content Calendar] -> Creative Brief

## Acceptance Criteria

- [ ] DAG diagram updated to show linear chain: Brief Parser -> Audience Research -> Content Calendar -> Creative Brief
- [ ] No parallel fan-out shown between Audience Research and Content Calendar
- [ ] Diagram reviewed by at least one other team member for accuracy
- [ ] Any references to parallel execution of these two agents are corrected in surrounding documentation

## Work Log

| Date | Author | Note |
|------|--------|------|
| 2026-02-28 | Plan Review | Issue identified during P1 critical review |

## Resources

- Pipeline DAG diagram (current, incorrect version)
- Content Calendar input schema definition (`AudienceOutput` dependency)
- Architecture Strategist review notes
- Performance Oracle review notes
- Spec Flow Analyzer review notes
