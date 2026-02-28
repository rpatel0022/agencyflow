---
title: "google-genai SDK: response_schema not response_json_schema"
category: integration-issues
tags: [google-genai, gemini, structured-output, pydantic, sdk-api]
module: GeminiClient
symptom: "ValidationError: Extra inputs are not permitted - response_json_schema"
root_cause: "Wrong field name in GenerateContentConfig — SDK uses response_schema, not response_json_schema"
date: 2026-02-28
---

# google-genai SDK: Correct Field Name for Structured Output

## Problem

When configuring `GenerateContentConfig` for structured JSON output, using `response_json_schema` raises a Pydantic `ValidationError`:

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for GenerateContentConfig
response_json_schema
  Extra inputs are not permitted [type=extra_forbidden]
```

## Root Cause

The `google-genai` SDK (v1.14.0+) uses `response_schema` — not `response_json_schema`. The Context7 docs and some older examples show `response_json_schema`, but the actual SDK field (which uses Pydantic internally with `extra="forbid"`) is:

- `response_mime_type` — set to `"application/json"`
- `response_schema` — accepts a Pydantic `BaseModel` class directly (not `.model_json_schema()`)

## Solution

```python
from google.genai import types

config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=MyPydanticModel,  # NOT response_json_schema
)
```

You can pass the Pydantic model class directly — no need to call `.model_json_schema()` yourself. The SDK handles the conversion.

## How to Verify

```python
from google.genai import types
import inspect

sig = inspect.signature(types.GenerateContentConfig)
for name, param in sig.parameters.items():
    if 'response' in name.lower() or 'schema' in name.lower():
        print(f'{name}: {param.annotation}')
```

This prints: `responseSchema: Union[dict, type, Schema, ...]`

## Key Insight

The SDK internally uses camelCase (`responseSchema`) but accepts snake_case (`response_schema`) via Pydantic aliases. Always check the actual class signature if docs seem inconsistent.
