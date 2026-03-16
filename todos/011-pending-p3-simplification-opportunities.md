---
status: pending
priority: p3
issue_id: "011"
tags: [code-review, simplicity, yagni]
dependencies: []
---

## Problem Statement

Several production-grade patterns in the codebase are over-engineered for what is fundamentally a demo application. The Code Simplicity Reviewer identified components where simpler alternatives would achieve the same result with less code, fewer potential bugs, and easier comprehension.

## Findings

**Flagged by:** Code Simplicity Reviewer

1. **Token bucket rate limiter** — `asyncio.sleep(5)` achieves the same result with zero bugs. The token bucket implementation adds complexity without observable benefit in a demo context.
2. **State machine transition validation** — Only your own code writes state. External callers never set arbitrary states, so transition validation guards against a scenario that cannot occur.
3. **asyncio.Lock** — This is a single-writer system. The Python GIL prevents torn reads. The lock adds ceremony without preventing any real concurrency issue.
4. **Exponential backoff with jitter** — One retry with a 5-second wait is sufficient for a demo. The full exponential backoff algorithm is unnecessary when you are the only client.
5. **AgentError.retryable** — Nothing in the codebase reads this field to decide retry behavior. It is dead metadata.

**Important note on tension with other reviewers:** The Architecture Strategist explicitly approved the LLMClient Protocol and token bucket as good architectural patterns. There is a genuine tension here. Resolution: the decision should be based on the project's goal — "show I can build production systems" (keep the patterns) vs "build the simplest impressive demo" (simplify them).

## Proposed Solutions

For each item, the simplification path is:

1. Replace token bucket with `asyncio.sleep(5)` before LLM calls.
2. Remove state transition validation; set state directly.
3. Remove `asyncio.Lock` usage around state writes.
4. Replace exponential backoff with a single retry after a fixed delay.
5. Remove the `retryable` field from `AgentError` or wire it into actual retry logic.

Alternatively, keep all patterns and document them as intentional demonstrations of production-readiness.

## Technical Details

- Removing these patterns is straightforward but requires updating tests that assert on the specific behavior (e.g., token bucket timing, state transition errors).
- The token bucket and backoff logic may be tested in isolation; removing them means removing or rewriting those tests.
- The `retryable` field removal is the lowest-risk change since nothing depends on it.

## Acceptance Criteria

- [ ] A decision is made: production-showcase vs simplest-demo approach.
- [ ] If simplifying: each identified pattern is replaced with its simpler alternative.
- [ ] All existing tests pass or are updated to reflect the simplifications.
- [ ] If keeping patterns: add brief code comments explaining why each exists (to preempt future "YAGNI" observations).

## Work Log

_No work performed yet._

## Resources

- **Effort estimate:** Medium (removing things is sometimes harder than adding them)
- **Flagged by:** Code Simplicity Reviewer
- **Related tension:** Architecture Strategist approved LLMClient Protocol and token bucket patterns
