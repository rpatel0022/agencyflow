---
status: pending
priority: p1
issue_id: "003"
tags: [code-review, api-contract, architecture]
dependencies: []
---

# API Contract Undefined for Primary Endpoint

## Problem Statement

`POST /api/v1/pipeline/run` is the primary endpoint that triggers the entire pipeline, but its request format is not specified. Without a defined contract, the frontend cannot build the submission form, the backend cannot implement request parsing, and error handling is undefined.

Additionally, the Performance Reporter agent's trigger mechanism is undefined — how does the user provide metrics data?

## Findings

- **Flagged by:** Spec Flow Analyzer (1 agent)
- The plan references `POST /api/v1/pipeline/run` as the main entry point but does not specify:
  - **Request format:** Does it accept multipart form data, JSON, or both?
  - **Field names:** What are the expected fields? `file`? `text`? `brief`? Are they required or optional?
  - **Content-Type:** What does the frontend send — `multipart/form-data`, `application/json`, or content-negotiated?
  - **Validation errors (422):** What triggers validation failure? What is the error response shape?
  - **Conflict errors (409):** What happens if a pipeline is already running?
  - **Payload limits (413):** Is there a max file size? What is it?
- **Performance Reporter gap:** The plan does not define how metrics data reaches the Performance Reporter agent. Is it always `sample_metrics.json`? Can the user upload their own metrics file? Is it a separate endpoint?
- Without this contract, frontend and backend teams will make incompatible assumptions.

## Proposed Solutions

### Solution A: Define explicit multipart form data contract (Recommended)

Define `POST /api/v1/pipeline/run` as accepting `multipart/form-data` with:
- `file` (optional, `UploadFile`): Uploaded brief document (PDF, DOCX, TXT)
- `text` (optional, `Form`): Plain text brief content
- At least one of `file` or `text` must be provided; `file` takes precedence if both are sent.
- Performance Reporter always uses `sample_metrics.json` in v1.

**Pros:**
- Supports both file upload and text input in a single endpoint
- Clear precedence rule eliminates ambiguity
- Multipart form data is the standard for file uploads
- Simple v1 approach for Performance Reporter avoids scope creep

**Cons:**
- Multipart parsing is slightly more complex than pure JSON
- `sample_metrics.json` approach for Performance Reporter is inflexible (acceptable for demo)

### Solution B: Separate endpoints for file and text input

`POST /api/v1/pipeline/run/file` accepts file upload; `POST /api/v1/pipeline/run/text` accepts JSON body with text.

**Pros:**
- Each endpoint has a single, clear responsibility
- Simpler parsing logic per endpoint

**Cons:**
- Two endpoints to maintain instead of one
- Frontend must decide which endpoint to call based on user input
- Adds routing complexity for no clear benefit

### Solution C: JSON-only with base64 file encoding

Accept `application/json` with file content base64-encoded in a `file_content` field.

**Pros:**
- Single content type, simpler CORS and middleware configuration

**Cons:**
- Base64 encoding increases payload size by ~33%
- Not idiomatic for file uploads
- Worse developer experience

### Recommendation

**Solution A** — Multipart form data with optional `file` and optional `text` fields. This is the standard approach for endpoints that accept file uploads and is well-supported by FastAPI.

## Technical Details

- **Endpoint:** `POST /api/v1/pipeline/run`
- **Content-Type:** `multipart/form-data`
- **Request fields:**
  - `file` (optional): `UploadFile` — accepted formats: `.pdf`, `.docx`, `.txt`
  - `text` (optional): `Form(str)` — plain text brief content
  - Validation: at least one must be provided
  - Precedence: `file` takes priority if both are provided
- **Response (success):** `{ "run_id": "uuid", "status": "queued" }` with HTTP 202 Accepted
- **Error responses:**
  - `422 Unprocessable Entity`: Neither `file` nor `text` provided, or invalid file format
  - `409 Conflict`: A pipeline run is already active
  - `413 Payload Too Large`: File exceeds size limit (suggest 10MB for v1)
- **Performance Reporter:** Uses bundled `sample_metrics.json` in v1. Future versions may accept user-uploaded metrics.

## Acceptance Criteria

- [ ] `POST /api/v1/pipeline/run` request schema is documented with field names, types, and optionality
- [ ] Content-Type is specified as `multipart/form-data`
- [ ] Precedence rule for `file` vs. `text` is documented and implemented
- [ ] Error responses defined for 422, 409, and 413 status codes
- [ ] File size limit is defined and enforced
- [ ] Accepted file formats are listed and validated
- [ ] Performance Reporter data source is documented (sample_metrics.json for v1)
- [ ] FastAPI endpoint implementation matches the documented contract
- [ ] Frontend form submission matches the documented contract

## Work Log

| Date | Author | Note |
|------|--------|------|
| 2026-02-28 | Plan Review | Issue identified during P1 critical review |

## Resources

- FastAPI file upload documentation
- Spec Flow Analyzer review notes
- Current plan sections referencing the pipeline trigger endpoint
