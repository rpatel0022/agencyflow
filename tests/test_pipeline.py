"""Tests for pipeline orchestrator and API routes."""

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas import PipelineStatus
from app.services.pipeline_orchestrator import PipelineOrchestrator, PipelineRun

# Sample outputs — reused from test_agents.py patterns
SAMPLE_BRIEF = {"campaign_name": "Test Campaign", "client_name": "Test Co",
    "objectives": ["Reach 1M people"], "target_audience": "Adults 18-34",
    "budget": "$50,000", "timeline": "4 weeks", "kpis": ["1M impressions"],
    "channels": ["Instagram"], "key_messages": ["Test message"],
    "constraints": ["None"], "raw_summary": "A test campaign.", "missing_fields": []}

SAMPLE_AUDIENCE = {"personas": [{"name": "Test Persona", "age_range": "25-34",
    "description": "Test description", "motivations": ["Test"], "pain_points": ["Test"],
    "preferred_channels": ["Instagram"], "content_preferences": ["Video"]}],
    "targeting_recommendations": ["Target young adults"],
    "audience_size_estimate": "5M users", "key_insights": ["They like video"],
    "suggested_tone": "Casual and fun"}

SAMPLE_CALENDAR = {"campaign_duration": "4 weeks",
    "posting_frequency": "3 posts per week", "entries": [{"week": 1, "day": "Monday",
    "channel": "Instagram", "content_type": "Reel", "topic": "Launch teaser",
    "caption_hook": "Coming soon...", "hashtags": ["#Test"], "notes": "Use bright colors"}],
    "channel_strategies": [{"channel": "Instagram", "strategy": "Reels first"}],
    "content_mix_rationale": "Video-first for engagement."}

SAMPLE_CREATIVE = {"project_name": "Test Campaign Brief", "prepared_for": "Test Co",
    "date": "2026-03-01", "background": "Test background.", "objective": "Drive awareness.",
    "target_audience_summary": "Young adults.", "key_message": "Test message.",
    "supporting_messages": ["Support 1"], "tone_and_voice": "Casual.",
    "visual_direction": "Bright colors.", "deliverables": ["5 Reels"],
    "timeline_summary": "4 weeks.", "success_metrics": ["1M impressions"],
    "mandatory_inclusions": ["FTC disclosure"]}

SAMPLE_PERFORMANCE = {"executive_summary": "Campaign exceeded targets.",
    "overall_performance": "Exceeding targets", "channel_analysis": [{"channel": "Instagram",
    "performance_rating": "Strong", "key_metric": "4.7% engagement",
    "insight": "Reels drove engagement.", "recommendation": "More Reels."}],
    "top_performing_content": ["Launch Reel"], "recommendations": ["Increase Reels"],
    "next_steps": ["Plan Phase 2"], "key_metrics_summary": [
    {"metric_name": "Impressions", "value": "2M", "trend": "up"}]}


def _make_mock_client(responses: list[dict]) -> AsyncMock:
    """Create a mock LLM client that returns different responses for each call."""
    client = AsyncMock()
    client.generate = AsyncMock(side_effect=responses)
    return client


# ---------------------------------------------------------------------------
# Pipeline Orchestrator unit tests
# ---------------------------------------------------------------------------

class TestPipelineOrchestrator:

    @pytest.mark.asyncio
    async def test_full_pipeline_completes(self):
        """Full pipeline run with all 5 agents succeeding."""
        responses = [SAMPLE_BRIEF, SAMPLE_AUDIENCE, SAMPLE_CALENDAR,
                     SAMPLE_CREATIVE, SAMPLE_PERFORMANCE]
        client = _make_mock_client(responses)
        orchestrator = PipelineOrchestrator(client)

        run = await orchestrator.start_run("A" * 100)

        # Drain events until pipeline completes
        events = []
        while True:
            event = await asyncio.wait_for(run.event_queue.get(), timeout=10)
            if event is None:
                break
            events.append(event)

        assert run.status == PipelineStatus.COMPLETE
        assert run.brief_output is not None
        assert run.audience_output is not None
        assert run.calendar_output is not None
        assert run.creative_brief_output is not None
        assert run.performance_output is not None

        # Should have status updates + agent completions + pipeline_complete
        event_types = [e["event_type"] for e in events]
        assert "status_update" in event_types
        assert "agent_complete" in event_types
        assert "pipeline_complete" in event_types

    @pytest.mark.asyncio
    async def test_pipeline_emits_correct_event_sequence(self):
        """Events should follow the DAG order."""
        responses = [SAMPLE_BRIEF, SAMPLE_AUDIENCE, SAMPLE_CALENDAR,
                     SAMPLE_CREATIVE, SAMPLE_PERFORMANCE]
        client = _make_mock_client(responses)
        orchestrator = PipelineOrchestrator(client)

        run = await orchestrator.start_run("A" * 100)

        events = []
        while True:
            event = await asyncio.wait_for(run.event_queue.get(), timeout=10)
            if event is None:
                break
            events.append(event)

        # Extract agent_complete events in order
        completions = [e["agent_name"] for e in events if e["event_type"] == "agent_complete"]
        # Brief → Audience → Calendar must be in order (Creative Brief might be before or after reporter)
        assert completions.index("brief_parser") < completions.index("audience_researcher")
        assert completions.index("audience_researcher") < completions.index("content_calendar")

    @pytest.mark.asyncio
    async def test_rejects_concurrent_run(self):
        """Starting a second run while one is active should raise ValueError."""
        # Use a client whose generate() blocks forever
        block = asyncio.Event()

        async def hang(*args, **kwargs):
            await block.wait()
            return SAMPLE_BRIEF

        client = AsyncMock()
        client.generate = hang
        orchestrator = PipelineOrchestrator(client)

        await orchestrator.start_run("A" * 100)
        # Give the background task time to reach the first generate() call
        await asyncio.sleep(0.05)

        with pytest.raises(ValueError, match="already running"):
            await orchestrator.start_run("B" * 100)

        # Unblock so background task can clean up
        block.set()

    @pytest.mark.asyncio
    async def test_pipeline_handles_agent_failure(self):
        """Pipeline should emit failure event when an agent raises."""
        client = AsyncMock()
        client.generate = AsyncMock(side_effect=RuntimeError("LLM failed"))
        orchestrator = PipelineOrchestrator(client)

        run = await orchestrator.start_run("A" * 100)

        events = []
        while True:
            event = await asyncio.wait_for(run.event_queue.get(), timeout=10)
            if event is None:
                break
            events.append(event)

        assert run.status == PipelineStatus.FAILED
        assert run.failed_agent == "brief_parser"
        error_events = [e for e in events if e["event_type"] == "pipeline_failed"]
        assert len(error_events) == 1
        assert error_events[0]["error"]["error_type"] == "RuntimeError"

    @pytest.mark.asyncio
    async def test_allows_new_run_after_completion(self):
        """After a run completes, a new one should be allowed."""
        responses = [SAMPLE_BRIEF, SAMPLE_AUDIENCE, SAMPLE_CALENDAR,
                     SAMPLE_CREATIVE, SAMPLE_PERFORMANCE]
        client = _make_mock_client(responses * 2)  # Enough for two runs
        orchestrator = PipelineOrchestrator(client)

        run1 = await orchestrator.start_run("A" * 100)
        while True:
            event = await asyncio.wait_for(run1.event_queue.get(), timeout=10)
            if event is None:
                break

        # Should not raise
        run2 = await orchestrator.start_run("B" * 100)
        assert run2.run_id != run1.run_id


# ---------------------------------------------------------------------------
# API Route tests
# ---------------------------------------------------------------------------

class TestPipelineRoutes:

    @pytest.mark.asyncio
    async def test_run_with_text_returns_202(self):
        """POST /run with text should return 202 and a run_id."""
        responses = [SAMPLE_BRIEF, SAMPLE_AUDIENCE, SAMPLE_CALENDAR,
                     SAMPLE_CREATIVE, SAMPLE_PERFORMANCE]
        mock_client = _make_mock_client(responses)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Inject mock orchestrator
            app.state.orchestrator = PipelineOrchestrator(mock_client)

            response = await client.post(
                "/api/v1/pipeline/run",
                data={"text": "A" * 100},
            )

        assert response.status_code == 202
        body = response.json()
        assert "run_id" in body
        assert body["status"] == "parsing"

    @pytest.mark.asyncio
    async def test_run_with_file_returns_202(self):
        """POST /run with a TXT file should return 202."""
        responses = [SAMPLE_BRIEF, SAMPLE_AUDIENCE, SAMPLE_CALENDAR,
                     SAMPLE_CREATIVE, SAMPLE_PERFORMANCE]
        mock_client = _make_mock_client(responses)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            app.state.orchestrator = PipelineOrchestrator(mock_client)

            response = await client.post(
                "/api/v1/pipeline/run",
                files={"file": ("brief.txt", b"A" * 100, "text/plain")},
            )

        assert response.status_code == 202

    @pytest.mark.asyncio
    async def test_run_rejects_missing_input(self):
        """POST /run with no file or text should return 422."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            app.state.orchestrator = PipelineOrchestrator(AsyncMock())

            response = await client.post("/api/v1/pipeline/run")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_run_rejects_unsupported_file(self):
        """POST /run with a .docx file should return 422."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            app.state.orchestrator = PipelineOrchestrator(AsyncMock())

            response = await client.post(
                "/api/v1/pipeline/run",
                files={"file": ("brief.docx", b"content", "application/octet-stream")},
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_run_rejects_oversized_file(self):
        """POST /run with a file over 10MB should return 413."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            app.state.orchestrator = PipelineOrchestrator(AsyncMock())

            # 11MB of data
            big_content = b"A" * (11 * 1024 * 1024)
            response = await client.post(
                "/api/v1/pipeline/run",
                files={"file": ("brief.txt", big_content, "text/plain")},
            )

        assert response.status_code == 413

    @pytest.mark.asyncio
    async def test_concurrent_run_returns_409(self):
        """Second POST /run while pipeline is active should return 409."""
        block = asyncio.Event()

        async def hang(*args, **kwargs):
            await block.wait()
            return SAMPLE_BRIEF

        hanging_client = AsyncMock()
        hanging_client.generate = hang

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            app.state.orchestrator = PipelineOrchestrator(hanging_client)

            # First run starts OK
            resp1 = await client.post("/api/v1/pipeline/run", data={"text": "A" * 100})
            assert resp1.status_code == 202

            await asyncio.sleep(0.05)

            # Second run should be rejected
            resp2 = await client.post("/api/v1/pipeline/run", data={"text": "B" * 100})
            assert resp2.status_code == 409

        block.set()

    @pytest.mark.asyncio
    async def test_demo_endpoint_returns_all_outputs(self):
        """POST /demo should return pre-computed outputs."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            app.state.orchestrator = PipelineOrchestrator(AsyncMock())

            response = await client.post("/api/v1/pipeline/demo")

        assert response.status_code == 200
        body = response.json()
        assert body["demo"] is True
        assert body["status"] == "complete"
        assert "brief_parsed" in body["outputs"]
        assert "audience" in body["outputs"]
        assert "calendar" in body["outputs"]
        assert "creative_brief" in body["outputs"]
        assert "performance" in body["outputs"]

    @pytest.mark.asyncio
    async def test_stream_unknown_run_returns_404(self):
        """GET /stream/{bad_id} should return 404."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            app.state.orchestrator = PipelineOrchestrator(AsyncMock())

            response = await client.get("/api/v1/pipeline/stream/nonexistent-id")

        assert response.status_code == 404
