---
status: pending
priority: p2
issue_id: "006"
tags: [code-review, python, schemas, type-safety]
dependencies: []
---

# String-Typed Fields Should Be Enums

## Problem Statement

Several fields use free strings where the values are finite known sets. Comments in the code show expected values but the schema does not enforce them. This means the LLM can return any arbitrary string, the frontend cannot reliably switch on values, and typos or variations go undetected.

**Flagged by:** Python Reviewer

**Effort:** Small.

## Findings

1. `performance_rating` accepts any string but should only be "Strong", "Moderate", or "Weak".
2. `trend` accepts any string but should only be "up", "down", or "stable".
3. `overall_performance` accepts any string but should only be "On track", "Below target", or "Exceeding".
4. `AgentError.error_type` accepts any string but should only be "rate_limit", "timeout", etc.
5. `PipelineRunResponse.run_id` is typed as `str` but represents a UUID and should be `uuid.UUID`.
6. `CreativeBriefOutput.date` already uses `datetime.date` (good -- no change needed there).

## Proposed Solutions

### Solution A: StrEnum Classes (Recommended)

Create `StrEnum` subclasses for each constrained field: `PerformanceRating`, `Trend`, `OverallPerformance`, `AgentErrorType`.

**Pros:**
- Native Python enum support (3.11+ `StrEnum` or `enum.StrEnum` backport).
- JSON-serializable by default since they inherit from `str`.
- Frontend receives deterministic values it can switch on.
- Pydantic validates automatically -- invalid values rejected at parse time.

**Cons:**
- Adding a new valid value requires a code change and redeployment.
- Minor overhead of defining the enum classes.

### Solution B: Literal Types

Use `Literal["Strong", "Moderate", "Weak"]` directly in the field type annotation.

**Pros:**
- No extra classes needed.
- Pydantic validates against the literal values.

**Cons:**
- Values duplicated if used in multiple places.
- No named type to reference in other parts of the codebase.
- Harder to iterate over valid values programmatically.

### Solution C: Pydantic Field with Regex Pattern

Use `Field(pattern=r"^(Strong|Moderate|Weak)$")` on string fields.

**Pros:**
- No extra types needed.
- Works with plain strings.

**Cons:**
- Regex is less readable than enum or Literal.
- No IDE autocompletion or type checking.
- Easy to get wrong with escaping.

## Technical Details

```python
from enum import StrEnum
import uuid

class PerformanceRating(StrEnum):
    STRONG = "Strong"
    MODERATE = "Moderate"
    WEAK = "Weak"

class Trend(StrEnum):
    UP = "up"
    DOWN = "down"
    STABLE = "stable"

class OverallPerformance(StrEnum):
    ON_TRACK = "On track"
    BELOW_TARGET = "Below target"
    EXCEEDING = "Exceeding"

class AgentErrorType(StrEnum):
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    VALIDATION = "validation"
    UNKNOWN = "unknown"

class PipelineRunResponse(BaseModel):
    run_id: uuid.UUID  # was: str
    # ...
```

## Acceptance Criteria

- [ ] `PerformanceRating`, `Trend`, `OverallPerformance`, and `AgentErrorType` StrEnum classes are defined.
- [ ] All schema fields that previously used free strings for known value sets now use the corresponding StrEnum.
- [ ] `PipelineRunResponse.run_id` is typed as `uuid.UUID`.
- [ ] Unit tests verify that invalid enum values are rejected by Pydantic.
- [ ] Frontend code (if any) is updated to use the enum values for rendering logic.

## Work Log

| Date | Author | Note |
|------|--------|------|
| 2026-02-28 | Plan Review | Issue identified during plan review by Python Reviewer |

## Resources

- [Python StrEnum documentation](https://docs.python.org/3/library/enum.html#enum.StrEnum)
- [Pydantic Enum support](https://docs.pydantic.dev/latest/concepts/types/#enums)
