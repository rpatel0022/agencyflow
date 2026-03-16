---
status: pending
priority: p2
issue_id: "005"
tags: [code-review, python, schemas, security]
dependencies: []
---

# Unconstrained List Fields Across All Schemas

## Problem Statement

Every `list[str]` field across all schemas has no length constraints -- no minimum/maximum on the list itself, and no `max_length` on individual strings. Gemini could return 500 objectives with 10,000-character strings each. Additionally, typed list fields like `personas: list[Persona]` have no min/max enforcement despite the plan commenting "2-3 personas" as the intended range.

**Flagged by:** Python Reviewer, Security Sentinel, Spec Flow Analyzer (3 agents)

**Effort:** Small. Mechanical changes to schemas.py.

## Findings

1. All `list[str]` fields lack both list-level and item-level constraints.
2. No `min_length` or `max_length` on any list field in the schema definitions.
3. Individual string items within lists have no `max_length`, allowing arbitrarily long strings.
4. Typed lists such as `personas: list[Persona]` rely on code comments ("2-3 personas") rather than schema enforcement.
5. This creates a denial-of-service vector where the LLM could return payloads of unbounded size, consuming memory and bandwidth.

## Proposed Solutions

### Solution A: Annotated Types with Field Constraints

Add `Field(min_length=1, max_length=20)` to all list fields and use `Annotated[str, StringConstraints(max_length=500)]` for list items.

**Pros:**
- Pydantic validates automatically on deserialization.
- Self-documenting constraints visible in the schema definition.
- Catches oversized LLM responses immediately at parse time.

**Cons:**
- Requires touching every list field in schemas.py.
- May need tuning of max values per field (not all lists should share the same limit).

### Solution B: Custom Validator Decorator

Create a reusable `@constrained_list` validator that applies standard bounds unless overridden.

**Pros:**
- DRY approach: define defaults once, override per field.
- Easier to adjust global defaults later.

**Cons:**
- More abstraction to understand for new contributors.
- Still requires annotating each field to opt in.

### Solution C: Response Size Gate Before Parsing

Add a byte-size check on the raw LLM response before Pydantic parsing begins.

**Pros:**
- Catches extreme cases regardless of schema constraints.
- Simple to implement as middleware in the LLM client.

**Cons:**
- Coarse-grained: cannot distinguish which field is oversized.
- Does not replace per-field constraints; should be used in addition, not instead.

## Technical Details

```python
from pydantic import BaseModel, Field, StringConstraints
from typing import Annotated

ConstrainedStr = Annotated[str, StringConstraints(max_length=500)]

class MarketAnalysisOutput(BaseModel):
    objectives: list[ConstrainedStr] = Field(min_length=1, max_length=20)
    # ... other fields

class CreativeBriefOutput(BaseModel):
    personas: list[Persona] = Field(min_length=1, max_length=5)
    # ... other fields
```

All list fields in the following schemas need constraints:
- `MarketAnalysisOutput`
- `CreativeBriefOutput`
- `CampaignStrategyOutput`
- `AdCopyOutput`
- Any other schema with `list[str]` or `list[Model]` fields

## Acceptance Criteria

- [ ] Every `list[str]` field has `Field(min_length=..., max_length=...)`.
- [ ] Every string item in a list uses `Annotated[str, StringConstraints(max_length=...)]`.
- [ ] Every `list[Model]` field has `min_length` and `max_length` matching the plan's stated expectations.
- [ ] Unit tests verify that oversized lists and strings are rejected by Pydantic.
- [ ] No bare `list[str]` or unconstrained `list[Model]` fields remain in schemas.py.

## Work Log

| Date | Author | Note |
|------|--------|------|
| 2026-02-28 | Plan Review | Issue identified during plan review by 3 agents |

## Resources

- [Pydantic Field documentation](https://docs.pydantic.dev/latest/concepts/fields/)
- [Pydantic StringConstraints](https://docs.pydantic.dev/latest/api/types/#pydantic.types.StringConstraints)
