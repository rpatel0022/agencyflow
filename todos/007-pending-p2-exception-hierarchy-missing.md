---
status: pending
priority: p2
issue_id: "007"
tags: [code-review, python, error-handling]
dependencies: []
---

# Exception Hierarchy Missing

## Problem Statement

The plan defines `AgentError` as a Pydantic response schema but does not define any actual Python exception classes. When the Gemini client hits a rate limit after 3 retries, there is no specified exception to raise. Without custom exceptions, the pipeline orchestrator would resort to bare `except Exception` blocks, which is an anti-pattern that swallows unrelated errors and makes debugging difficult.

Additionally, `LLMClient.generate()` returns `dict` but should return `T` (a TypeVar bound to BaseModel), which defeats the purpose of having a typed protocol.

**Flagged by:** Python Reviewer

**Effort:** Small-Medium.

## Findings

1. `AgentError` exists as a Pydantic model for API responses, but no corresponding Python exception classes exist for internal error handling.
2. No custom exception hierarchy is defined anywhere in the plan.
3. The pipeline orchestrator has no specified way to catch and handle specific failure modes (rate limit exhaustion, LLM response validation failure, file parsing errors).
4. `LLMClient.generate()` protocol method returns `dict` instead of a generic `T` bound to `BaseModel`, meaning callers lose type safety after the LLM call.
5. Without typed exceptions, retry logic cannot distinguish between retryable errors (rate limit) and permanent errors (invalid API key).

## Proposed Solutions

### Solution A: Custom Exception Hierarchy with Base Class (Recommended)

Define `AgencyFlowError` as the base exception, with specific subclasses for each failure mode.

**Pros:**
- Pipeline orchestrator can catch specific exceptions (`except RateLimitExhaustedError`) instead of bare `except Exception`.
- Each exception carries structured context (retry count, raw response, etc.).
- Follows Python best practices for library exception design.

**Cons:**
- Requires defining and maintaining the hierarchy.
- Callers need to be updated to catch the new exception types.

### Solution B: Single Exception with Error Code Enum

Define one `AgencyFlowError` exception that carries an `AgentErrorType` enum (from issue 006) to distinguish failure modes.

**Pros:**
- Simpler: only one exception class to import.
- Error type is already defined if issue 006 is resolved first.

**Cons:**
- Less Pythonic -- `except AgencyFlowError as e: if e.error_type == ...` is verbose.
- Cannot use different exception attributes per error type.
- Harder to add type-specific context.

### Solution C: Use Standard Library Exceptions with Custom Attributes

Subclass `ConnectionError`, `TimeoutError`, `ValueError` directly and add custom attributes.

**Pros:**
- Familiar exception types for Python developers.
- Works with existing `except TimeoutError` blocks.

**Cons:**
- Conflates application errors with system errors.
- Cannot catch "all AgencyFlow errors" with a single base class.
- Semantic mismatch: `ValueError` is not the right base for an LLM validation failure.

## Technical Details

```python
from typing import TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class AgencyFlowError(Exception):
    """Base exception for all AgencyFlow errors."""
    pass

class RateLimitExhaustedError(AgencyFlowError):
    """Raised when all retries are exhausted due to rate limiting."""
    def __init__(self, retries: int, last_status: int, message: str = ""):
        self.retries = retries
        self.last_status = last_status
        super().__init__(message or f"Rate limit exhausted after {retries} retries")

class LLMResponseError(AgencyFlowError):
    """Raised when the LLM response fails Pydantic validation."""
    def __init__(self, raw_response: str, validation_errors: list[dict], message: str = ""):
        self.raw_response = raw_response
        self.validation_errors = validation_errors
        super().__init__(message or "LLM response failed schema validation")

class FileParsingError(AgencyFlowError):
    """Raised when an uploaded file cannot be parsed."""
    def __init__(self, filename: str, reason: str):
        self.filename = filename
        self.reason = reason
        super().__init__(f"Failed to parse '{filename}': {reason}")

# Fix LLMClient protocol:
class LLMClient(Protocol):
    async def generate(self, prompt: str, response_model: type[T]) -> T:
        ...  # returns validated Pydantic model, not dict
```

## Acceptance Criteria

- [ ] `AgencyFlowError` base exception class is defined.
- [ ] `RateLimitExhaustedError`, `LLMResponseError`, and `FileParsingError` subclasses are defined with structured context attributes.
- [ ] `LLMClient.generate()` protocol return type is `T` (TypeVar bound to BaseModel), not `dict`.
- [ ] Pipeline orchestrator catches specific exception types instead of bare `except Exception`.
- [ ] Retry logic in the Gemini client raises `RateLimitExhaustedError` after exhausting retries.
- [ ] Unit tests verify each exception type carries the expected context attributes.

## Work Log

| Date | Author | Note |
|------|--------|------|
| 2026-02-28 | Plan Review | Issue identified during plan review by Python Reviewer |

## Resources

- [Python Exception Hierarchy Best Practices](https://docs.python.org/3/tutorial/errors.html#user-defined-exceptions)
- [Pydantic BaseModel](https://docs.pydantic.dev/latest/concepts/models/)
- [typing.Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol)
