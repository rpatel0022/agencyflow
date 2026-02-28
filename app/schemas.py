"""All Pydantic schemas for AgencyFlow agent I/O, pipeline state, and SSE events."""

import datetime
import uuid
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Brief Parser Agent
# =============================================================================

class BriefParserInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    raw_text: str = Field(..., min_length=10, max_length=50_000)
    source_filename: str | None = Field(None, max_length=255, pattern=r"^[a-zA-Z0-9_\-\.]+$")


class BriefParserOutput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    campaign_name: str = Field(..., max_length=200)
    client_name: str = Field(..., max_length=200)
    objectives: list[str] = Field(..., max_length=10)
    target_audience: str = Field(..., max_length=2000)
    budget: str | None = Field(None, max_length=200)
    timeline: str = Field(..., max_length=500)
    kpis: list[str] = Field(..., max_length=10)
    channels: list[str] = Field(..., max_length=10)
    key_messages: list[str] = Field(..., max_length=10)
    constraints: list[str] = Field(..., max_length=10)
    raw_summary: str = Field(..., max_length=1000)
    missing_fields: list[str] = Field(default_factory=list, max_length=10)


# =============================================================================
# Audience Research Agent
# =============================================================================

class Persona(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(..., max_length=100)
    age_range: str = Field(..., max_length=20)
    description: str = Field(..., max_length=500)
    motivations: list[str] = Field(..., max_length=10)
    pain_points: list[str] = Field(..., max_length=10)
    preferred_channels: list[str] = Field(..., max_length=10)
    content_preferences: list[str] = Field(..., max_length=10)


class AudienceOutput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    personas: list[Persona] = Field(..., max_length=5)
    targeting_recommendations: list[str] = Field(..., max_length=10)
    audience_size_estimate: str = Field(..., max_length=200)
    key_insights: list[str] = Field(..., max_length=10)
    suggested_tone: str = Field(..., max_length=200)


# =============================================================================
# Content Calendar Agent
# =============================================================================

class CalendarEntry(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    week: int = Field(..., ge=1, le=52)
    day: str = Field(..., max_length=20)
    channel: str = Field(..., max_length=50)
    content_type: str = Field(..., max_length=50)
    topic: str = Field(..., max_length=200)
    caption_hook: str = Field(..., max_length=500)
    hashtags: list[str] = Field(..., max_length=10)
    notes: str = Field(..., max_length=500)


class ChannelStrategy(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    channel: str = Field(..., max_length=50)
    strategy: str = Field(..., max_length=500)


class CalendarOutput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    campaign_duration: str = Field(..., max_length=100)
    posting_frequency: str = Field(..., max_length=100)
    entries: list[CalendarEntry] = Field(..., max_length=100)
    channel_strategies: list[ChannelStrategy] = Field(..., max_length=10)
    content_mix_rationale: str = Field(..., max_length=1000)


class CalendarSummary(BaseModel):
    """Condensed version passed to Creative Brief agent (reduces prompt size)."""
    campaign_duration: str
    posting_frequency: str
    channel_strategies: list[ChannelStrategy]
    content_mix_rationale: str


# =============================================================================
# Creative Brief Agent
# =============================================================================

class CreativeBriefInput(BaseModel):
    brief_data: BriefParserOutput
    audience_data: AudienceOutput
    calendar_summary: CalendarSummary


class CreativeBriefOutput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    project_name: str = Field(..., max_length=200)
    prepared_for: str = Field(..., max_length=200)
    date: datetime.date
    background: str = Field(..., max_length=2000)
    objective: str = Field(..., max_length=1000)
    target_audience_summary: str = Field(..., max_length=1000)
    key_message: str = Field(..., max_length=500)
    supporting_messages: list[str] = Field(..., max_length=10)
    tone_and_voice: str = Field(..., max_length=500)
    visual_direction: str = Field(..., max_length=1000)
    deliverables: list[str] = Field(..., max_length=20)
    timeline_summary: str = Field(..., max_length=500)
    success_metrics: list[str] = Field(..., max_length=10)
    mandatory_inclusions: list[str] = Field(..., max_length=10)


# =============================================================================
# Performance Reporter Agent
# =============================================================================

class ChannelMetrics(BaseModel):
    channel: str = Field(..., max_length=50)
    impressions: int = Field(..., ge=0, le=10_000_000_000)
    reach: int = Field(..., ge=0, le=10_000_000_000)
    engagement_rate: float = Field(..., ge=0.0, le=100.0)
    clicks: int = Field(..., ge=0, le=10_000_000_000)
    conversions: int = Field(..., ge=0, le=10_000_000_000)
    spend: float = Field(..., ge=0.0, le=100_000_000)


class PerformanceInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    campaign_name: str = Field(..., max_length=200)
    reporting_period: str = Field(..., max_length=100)
    channel_metrics: list[ChannelMetrics] = Field(..., max_length=20)
    goals: list[str] = Field(..., max_length=10)


class ChannelAnalysis(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    channel: str = Field(..., max_length=50)
    performance_rating: str = Field(..., max_length=50)
    key_metric: str = Field(..., max_length=200)
    insight: str = Field(..., max_length=500)
    recommendation: str = Field(..., max_length=500)


class MetricSummary(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    metric_name: str = Field(..., max_length=100)
    value: str = Field(..., max_length=100)
    trend: str = Field(..., max_length=50)


class PerformanceOutput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    executive_summary: str = Field(..., max_length=2000)
    overall_performance: str = Field(..., max_length=50)
    channel_analysis: list[ChannelAnalysis] = Field(..., max_length=20)
    top_performing_content: list[str] = Field(..., max_length=10)
    recommendations: list[str] = Field(..., max_length=10)
    next_steps: list[str] = Field(..., max_length=10)
    key_metrics_summary: list[MetricSummary] = Field(..., max_length=20)


# =============================================================================
# Pipeline State
# =============================================================================

class PipelineStatus(StrEnum):
    IDLE = "idle"
    PARSING = "parsing"
    RESEARCHING = "researching"
    CALENDARING = "calendaring"
    BRIEFING = "briefing"
    REPORTING = "reporting"
    COMPLETE = "complete"
    FAILED = "failed"


class PipelineRunResponse(BaseModel):
    run_id: str
    status: PipelineStatus


class AgentError(BaseModel):
    agent_name: str = Field(..., max_length=100)
    error_type: str = Field(..., max_length=50)
    message: str = Field(..., max_length=2000)
    retryable: bool


# =============================================================================
# SSE Event Schemas
# =============================================================================

class SSEEvent(BaseModel):
    """Base for all SSE events."""
    id: int
    run_id: uuid.UUID
    timestamp: datetime.datetime


class PipelineStatusEvent(SSEEvent):
    event_type: Literal["status_update"] = "status_update"
    agent_name: str = Field(..., max_length=100)
    status: PipelineStatus
    elapsed_ms: int = Field(..., ge=0)


class AgentCompleteEvent(SSEEvent):
    event_type: Literal["agent_complete"] = "agent_complete"
    agent_name: str = Field(..., max_length=100)
    output: dict


class ReporterStatusEvent(SSEEvent):
    """Separate event for Performance Reporter (runs in parallel)."""
    event_type: Literal["reporter_status"] = "reporter_status"
    status: PipelineStatus
    output: dict | None = None


class PipelineErrorEvent(SSEEvent):
    event_type: Literal["pipeline_failed"] = "pipeline_failed"
    failed_agent: str = Field(..., max_length=100)
    error: AgentError


class PipelineCompleteEvent(SSEEvent):
    event_type: Literal["pipeline_complete"] = "pipeline_complete"
