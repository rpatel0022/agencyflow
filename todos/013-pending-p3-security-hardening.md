---
status: pending
priority: p3
issue_id: "013"
tags: [code-review, security, hardening]
dependencies: []
---

## Problem Statement

Multiple low-priority security hardening items were identified. While none represent critical vulnerabilities, each addresses a defense-in-depth gap that would be expected in production-quality code.

## Findings

**Flagged by:** Security Sentinel

1. **Use SecretStr for GEMINI_API_KEY** — The API key is stored as a plain string in pydantic-settings. Using `SecretStr` prevents accidental logging or serialization of the key value (e.g., in `repr()`, debug output, or error tracebacks).

2. **Add security headers middleware** — No security headers are set on HTTP responses. Missing headers include:
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `Cache-Control: no-store` (for API responses)

3. **Validate pre-computed demo JSON files on startup** — Demo JSON files are loaded and served without validation against Pydantic schemas. Malformed demo data would cause runtime errors instead of a clear startup failure.

4. **Add request body size limit middleware** — Pydantic validation checks structure but not raw payload size. A large payload could consume memory before validation rejects it.

5. **Hardcode 127.0.0.1 bind in code** — The localhost bind address is only set via CLI flag. Hardcoding it in the application code as a default ensures the server never accidentally binds to 0.0.0.0 even if the CLI flag is omitted.

6. **source_filename regex is too restrictive** — The current regex rejects filenames containing spaces or unicode characters, which are common in real-world file names.

## Proposed Solutions

1. Change the `GEMINI_API_KEY` field type from `str` to `SecretStr` in the settings model. Access the value via `.get_secret_value()` where needed.

2. Add a Starlette/FastAPI middleware that sets security headers on all responses:
   ```python
   @app.middleware("http")
   async def security_headers(request, call_next):
       response = await call_next(request)
       response.headers["X-Content-Type-Options"] = "nosniff"
       response.headers["X-Frame-Options"] = "DENY"
       response.headers["Cache-Control"] = "no-store"
       return response
   ```

3. On application startup, load and validate each demo JSON file against its corresponding Pydantic model. Fail fast with a clear error message if validation fails.

4. Add request body size limit middleware or use an existing library (e.g., limit to 1MB for text input, appropriate size for file uploads).

5. Set `host="127.0.0.1"` as the default in the `uvicorn.run()` call, not just in CLI argument defaults.

6. Relax the `source_filename` regex to allow spaces, hyphens, underscores, and common unicode characters while still rejecting path traversal characters.

## Technical Details

- `SecretStr` is a built-in pydantic type; migration requires updating all access points to use `.get_secret_value()`.
- Security headers middleware is a few lines of code with no dependencies.
- Demo JSON validation can run in the FastAPI `startup` event handler.
- Body size limiting can be done via ASGI middleware or a custom dependency.
- The filename regex change should be tested against known-good and known-bad filenames (e.g., `../etc/passwd`, `file name.txt`, `resume.pdf`).

## Acceptance Criteria

- [ ] `GEMINI_API_KEY` uses `SecretStr` and is never exposed in logs or error output.
- [ ] All HTTP responses include `X-Content-Type-Options`, `X-Frame-Options`, and `Cache-Control` headers.
- [ ] Demo JSON files are validated against Pydantic schemas at startup; invalid files cause a clear startup error.
- [ ] Request body size is limited via middleware (configurable threshold).
- [ ] Server binds to `127.0.0.1` by default in application code.
- [ ] `source_filename` regex accepts filenames with spaces and common unicode characters while rejecting path traversal patterns.

## Work Log

_No work performed yet._

## Resources

- **Effort estimate:** Small per item
- **Flagged by:** Security Sentinel
