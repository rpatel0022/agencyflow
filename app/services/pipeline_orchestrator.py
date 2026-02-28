"""Pipeline orchestrator — runs the 5-agent DAG with SSE event streaming."""

import asyncio
import datetime
import json
import logging
import uuid

from app.agents.brief_parser import parse_brief
from app.agents.audience_researcher import research_audience
from app.agents.content_calendar import generate_calendar
from app.agents.creative_brief import generate_creative_brief
from app.agents.performance_reporter import generate_report
from app.gemini_client import LLMClient
from pydantic import ValidationError

from app.schemas import (
    AudienceOutput,
    BriefParserInput,
    BriefParserOutput,
    CalendarOutput,
    CalendarSummary,
    ChannelStrategy,
    CreativeBriefInput,
    CreativeBriefOutput,
    PerformanceInput,
    PerformanceOutput,
    PipelineStatus,
)

logger = logging.getLogger("agencyflow.pipeline")


class PipelineRun:
    """Holds state for a single pipeline execution.

    WHY a class here but not for agents: the orchestrator manages mutable state
    (status, outputs, event queue) across multiple async steps. A class groups
    that state together. Agents are stateless pure functions — no state to group.
    """

    def __init__(self, run_id: str, raw_text: str, source_filename: str | None = None):
        self.run_id = run_id
        self.raw_text = raw_text
        self.source_filename = source_filename
        self.status = PipelineStatus.IDLE
        self.start_time: float | None = None

        # Agent outputs stored as they complete
        self.brief_output: BriefParserOutput | None = None
        self.audience_output: AudienceOutput | None = None
        self.calendar_output: CalendarOutput | None = None
        self.creative_brief_output: CreativeBriefOutput | None = None
        self.performance_output: PerformanceOutput | None = None
        self.error: str | None = None
        self.failed_agent: str | None = None

        # SSE event queue — subscribers read from this
        # WHY asyncio.Queue: it's an async-safe FIFO that lets the pipeline
        # producer push events and the SSE endpoint consumer pull them
        # without polling or shared mutable state.
        self.event_queue: asyncio.Queue[dict | None] = asyncio.Queue()
        self._event_counter = 0

    def _emit(self, event_type: str, **data) -> None:
        """Push an SSE event onto the queue."""
        self._event_counter += 1
        event = {
            "id": self._event_counter,
            "run_id": self.run_id,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "event_type": event_type,
            **data,
        }
        self.event_queue.put_nowait(event)

    def _emit_status(self, agent_name: str, status: PipelineStatus, elapsed_ms: int) -> None:
        """Emit a status_update event."""
        self.status = status
        self._emit("status_update", agent_name=agent_name, status=status.value, elapsed_ms=elapsed_ms)

    def _elapsed_ms(self) -> int:
        """Milliseconds since pipeline started."""
        if self.start_time is None:
            return 0
        import time
        return int((time.monotonic() - self.start_time) * 1000)


class PipelineOrchestrator:
    """Manages pipeline runs. Only one run at a time (single-user local demo).

    WHY asyncio.Lock: without it, two near-simultaneous POST /run requests
    could both pass the "is idle?" check before either sets status to PARSING.
    The lock makes the check-and-set atomic.
    """

    def __init__(self, client: LLMClient):
        self._client = client
        self._lock = asyncio.Lock()
        self._current_run: PipelineRun | None = None
        self._runs: dict[str, PipelineRun] = {}

    @property
    def current_run(self) -> PipelineRun | None:
        return self._current_run

    def get_run(self, run_id: str) -> PipelineRun | None:
        return self._runs.get(run_id)

    async def start_run(
        self, raw_text: str, source_filename: str | None = None
    ) -> PipelineRun:
        """Start a new pipeline run. Raises ValueError if one is already running."""
        async with self._lock:
            if self._current_run and self._current_run.status not in (
                PipelineStatus.COMPLETE,
                PipelineStatus.FAILED,
                PipelineStatus.IDLE,
            ):
                raise ValueError("Pipeline is already running")

            run_id = str(uuid.uuid4())
            run = PipelineRun(run_id, raw_text, source_filename)
            # Set status before the task starts so the 202 response shows "parsing"
            run.status = PipelineStatus.PARSING
            self._current_run = run
            self._runs[run_id] = run

        # Fire and forget — the pipeline runs in the background while
        # the SSE endpoint streams events from the queue.
        asyncio.create_task(self._execute(run))
        return run

    async def _execute(self, run: PipelineRun) -> None:
        """Execute the full agent pipeline.

        DAG:
            Brief Parser → Audience Research → Content Calendar → Creative Brief
                                                                  ↑
                                        Performance Reporter runs in parallel
                                        (via asyncio.gather with the main chain)
        """
        import time
        run.start_time = time.monotonic()

        try:
            # Step 1: Brief Parser
            run._emit_status("brief_parser", PipelineStatus.PARSING, run._elapsed_ms())
            brief_input = BriefParserInput(
                raw_text=run.raw_text, source_filename=run.source_filename
            )
            run.brief_output = await parse_brief(brief_input, self._client)
            run._emit(
                "agent_complete",
                agent_name="brief_parser",
                output=run.brief_output.model_dump(mode="json"),
            )

            # Step 2: Audience Research
            run._emit_status("audience_researcher", PipelineStatus.RESEARCHING, run._elapsed_ms())
            run.audience_output = await research_audience(run.brief_output, self._client)
            run._emit(
                "agent_complete",
                agent_name="audience_researcher",
                output=run.audience_output.model_dump(mode="json"),
            )

            # Step 3: Content Calendar
            run._emit_status("content_calendar", PipelineStatus.CALENDARING, run._elapsed_ms())
            run.calendar_output = await generate_calendar(
                run.brief_output, run.audience_output, self._client
            )
            run._emit(
                "agent_complete",
                agent_name="content_calendar",
                output=run.calendar_output.model_dump(mode="json"),
            )

            # Step 4 + 5: Creative Brief and Performance Reporter in parallel
            # WHY asyncio.gather: these two agents are independent — Creative Brief
            # needs only prior outputs (already computed), and Performance Reporter
            # uses separate metrics data. Running them simultaneously saves one full
            # agent cycle (~14 seconds with rate limiting + API latency).
            run._emit_status("creative_brief", PipelineStatus.BRIEFING, run._elapsed_ms())
            run._emit("reporter_status", status=PipelineStatus.REPORTING.value, output=None)

            calendar_summary = CalendarSummary(
                campaign_duration=run.calendar_output.campaign_duration,
                posting_frequency=run.calendar_output.posting_frequency,
                channel_strategies=run.calendar_output.channel_strategies,
                content_mix_rationale=run.calendar_output.content_mix_rationale,
            )
            creative_input = CreativeBriefInput(
                brief_data=run.brief_output,
                audience_data=run.audience_output,
                calendar_summary=calendar_summary,
            )

            # Load bundled metrics for Performance Reporter
            metrics_input = _load_sample_metrics(run.brief_output.campaign_name)

            creative_result, performance_result = await asyncio.gather(
                generate_creative_brief(creative_input, self._client),
                generate_report(metrics_input, self._client),
            )

            run.creative_brief_output = creative_result
            run._emit(
                "agent_complete",
                agent_name="creative_brief",
                output=run.creative_brief_output.model_dump(mode="json"),
            )

            run.performance_output = performance_result
            run._emit(
                "reporter_status",
                status=PipelineStatus.COMPLETE.value,
                output=run.performance_output.model_dump(mode="json"),
            )

            # Done
            run.status = PipelineStatus.COMPLETE
            run._emit("pipeline_complete")
            logger.info(f"Pipeline {run.run_id} completed in {run._elapsed_ms()}ms")

        except ValidationError as exc:
            run.status = PipelineStatus.FAILED
            run.error = f"Agent returned invalid data: {exc.error_count()} validation error(s)"
            run.failed_agent = _detect_failed_agent(run)
            run._emit(
                "pipeline_failed",
                failed_agent=run.failed_agent,
                error={
                    "agent_name": run.failed_agent,
                    "error_type": "ValidationError",
                    "message": run.error,
                    "retryable": True,
                },
            )
            logger.error(f"Pipeline {run.run_id} validation error at {run.failed_agent}: {exc}")

        except Exception as exc:
            run.status = PipelineStatus.FAILED
            run.error = str(exc)
            # Figure out which agent failed based on what output is missing
            run.failed_agent = _detect_failed_agent(run)
            run._emit(
                "pipeline_failed",
                failed_agent=run.failed_agent,
                error={
                    "agent_name": run.failed_agent,
                    "error_type": type(exc).__name__,
                    "message": str(exc)[:2000],
                    "retryable": _is_retryable(exc),
                },
            )
            logger.error(f"Pipeline {run.run_id} failed at {run.failed_agent}: {exc}")

        finally:
            # Signal end of stream — SSE endpoint stops when it reads None
            run.event_queue.put_nowait(None)


def _load_sample_metrics(campaign_name: str) -> PerformanceInput:
    """Load bundled sample_metrics.json for the Performance Reporter.

    In v1, we always use bundled metrics (no user-provided metrics endpoint).
    """
    from pathlib import Path
    metrics_path = Path(__file__).parent.parent.parent / "data" / "sample_metrics.json"
    with open(metrics_path) as f:
        data = json.load(f)
    # Use the campaign name from the parsed brief
    data["campaign_name"] = campaign_name
    return PerformanceInput.model_validate(data)


def _detect_failed_agent(run: PipelineRun) -> str:
    """Determine which agent failed by checking what's missing."""
    if run.brief_output is None:
        return "brief_parser"
    if run.audience_output is None:
        return "audience_researcher"
    if run.calendar_output is None:
        return "content_calendar"
    if run.creative_brief_output is None and run.performance_output is None:
        return "creative_brief_or_performance_reporter"
    if run.creative_brief_output is None:
        return "creative_brief"
    if run.performance_output is None:
        return "performance_reporter"
    return "unknown"


def _is_retryable(exc: Exception) -> bool:
    """Check if the error is retryable (rate limit, server error, or timeout)."""
    if isinstance(exc, (TimeoutError, asyncio.TimeoutError)):
        return True
    status_code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    return status_code in {429, 503}
