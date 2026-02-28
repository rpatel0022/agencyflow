"""Pipeline API routes — run pipeline, stream SSE events, demo mode."""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from sse_starlette.sse import EventSourceResponse

from app.config import settings
from app.file_parser import parse_file
from app.schemas import PipelineRunResponse, PipelineStatus

logger = logging.getLogger("agencyflow.router.pipeline")

router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])

# Pre-computed demo outputs directory
DEMO_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "precomputed"


@router.post("/run", status_code=202)
async def run_pipeline(
    request: Request,
    file: UploadFile | None = File(None),
    text: str | None = Form(None),
) -> PipelineRunResponse:
    """Start a new pipeline run.

    Accepts either a file upload (PDF/TXT) or raw text. File takes precedence.
    Returns 202 Accepted with a run_id for SSE streaming.

    WHY 202 instead of 200: the pipeline takes 60-120 seconds. Returning 202
    tells the client "I accepted your request but it's not done yet — use the
    run_id to track progress via SSE."
    """
    orchestrator = request.app.state.orchestrator

    # Validate: at least one input provided
    if file is None and not text:
        raise HTTPException(status_code=422, detail="Provide either a file or text brief")

    if file is None and text and len(text.strip()) < 10:
        raise HTTPException(status_code=422, detail="Brief text is too short (minimum 10 characters)")

    raw_text: str
    source_filename: str | None = None

    if file is not None:
        # Read and validate uploaded file
        content = await file.read()

        if len(content) > settings.max_upload_size_bytes:
            raise HTTPException(status_code=413, detail="File exceeds 10MB size limit")

        if not file.filename:
            raise HTTPException(status_code=422, detail="File must have a filename")

        try:
            raw_text = await parse_file(file.filename, content)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        source_filename = file.filename
    else:
        raw_text = text  # type: ignore[assignment]

    # Start the pipeline — raises ValueError if one is already running
    try:
        run = await orchestrator.start_run(raw_text, source_filename)
    except ValueError:
        raise HTTPException(status_code=409, detail="A pipeline run is already in progress")

    return PipelineRunResponse(run_id=run.run_id, status=run.status)


@router.get("/stream/{run_id}")
async def stream_pipeline(request: Request, run_id: str) -> EventSourceResponse:
    """SSE endpoint — streams pipeline events in real-time.

    WHY SSE over WebSockets: the pipeline only sends events server→client
    (no bidirectional communication needed). SSE is simpler — uses plain HTTP,
    auto-reconnects, and the frontend uses the native EventSource API.
    """
    orchestrator = request.app.state.orchestrator
    run = orchestrator.get_run(run_id)

    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    async def event_generator():
        """Yield SSE events from the pipeline's event queue.

        WHY async generator: SSE needs a stream of events over time.
        An async generator lets FastAPI send each event as it arrives
        from the queue, keeping the HTTP connection open until the
        pipeline finishes (signaled by None in the queue).
        """
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break

            event = await run.event_queue.get()

            # None signals end of stream
            if event is None:
                break

            event_type = event.get("event_type", "message")
            yield {
                "event": event_type,
                "id": str(event.get("id", "")),
                "data": json.dumps(event),
            }

    return EventSourceResponse(event_generator())


@router.post("/demo", status_code=200)
async def run_demo(request: Request) -> dict:
    """Return pre-computed demo outputs instantly (no LLM calls).

    WHY a separate endpoint: demo mode skips the entire pipeline and rate
    limiting. It lets the frontend be developed and tested without burning
    API quota or waiting 60+ seconds per test.
    """
    if not DEMO_DATA_DIR.exists():
        raise HTTPException(status_code=404, detail="Demo data not available")

    outputs = {}
    for name in ["brief_parsed", "audience", "calendar", "creative_brief", "performance"]:
        filepath = DEMO_DATA_DIR / f"{name}.json"
        if filepath.exists():
            with open(filepath) as f:
                outputs[name] = json.load(f)
        else:
            raise HTTPException(
                status_code=404, detail=f"Demo data missing: {name}.json"
            )

    return {
        "status": "complete",
        "demo": True,
        "outputs": outputs,
    }
