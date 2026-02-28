"""Tests for Pydantic schema validation."""

import datetime
import uuid

import pytest
from pydantic import ValidationError

from app.schemas import (
    BriefParserInput,
    BriefParserOutput,
    CalendarEntry,
    ChannelMetrics,
    PipelineStatus,
    PipelineStatusEvent,
)


class TestBriefParserInput:

    def test_valid_input(self):
        inp = BriefParserInput(raw_text="A" * 20)
        assert len(inp.raw_text) == 20

    def test_rejects_short_text(self):
        with pytest.raises(ValidationError):
            BriefParserInput(raw_text="short")

    def test_rejects_too_long_text(self):
        with pytest.raises(ValidationError):
            BriefParserInput(raw_text="A" * 50_001)

    def test_strips_whitespace(self):
        inp = BriefParserInput(raw_text="  " + "A" * 20 + "  ")
        assert not inp.raw_text.startswith(" ")

    def test_filename_pattern_rejects_path_traversal(self):
        with pytest.raises(ValidationError):
            BriefParserInput(raw_text="A" * 20, source_filename="../etc/passwd")


class TestCalendarEntry:

    def test_valid_entry(self):
        entry = CalendarEntry(
            week=1, day="Monday", channel="Instagram",
            content_type="Reel", topic="Launch teaser",
            caption_hook="Get ready", hashtags=["#launch"], notes="Draft"
        )
        assert entry.week == 1

    def test_rejects_invalid_week(self):
        with pytest.raises(ValidationError):
            CalendarEntry(
                week=0, day="Monday", channel="Instagram",
                content_type="Reel", topic="Test", caption_hook="Test",
                hashtags=[], notes="Test"
            )


class TestChannelMetrics:

    def test_rejects_negative_impressions(self):
        with pytest.raises(ValidationError):
            ChannelMetrics(
                channel="Instagram", impressions=-1, reach=0,
                engagement_rate=0.0, clicks=0, conversions=0, spend=0.0
            )

    def test_rejects_engagement_over_100(self):
        with pytest.raises(ValidationError):
            ChannelMetrics(
                channel="Instagram", impressions=0, reach=0,
                engagement_rate=101.0, clicks=0, conversions=0, spend=0.0
            )


class TestPipelineStatus:

    def test_enum_values(self):
        assert PipelineStatus.IDLE == "idle"
        assert PipelineStatus.FAILED == "failed"
        assert PipelineStatus.COMPLETE == "complete"


class TestSSEEvents:

    def test_pipeline_status_event(self):
        event = PipelineStatusEvent(
            id=1,
            run_id=uuid.uuid4(),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            agent_name="brief_parser",
            status=PipelineStatus.PARSING,
            elapsed_ms=1500,
        )
        assert event.event_type == "status_update"
        assert event.elapsed_ms == 1500
