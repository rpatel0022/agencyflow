"""Agent registry — central dispatch for all pipeline agents."""

from .brief_parser import parse_brief
from .audience_researcher import research_audience
from .content_calendar import generate_calendar
from .creative_brief import generate_creative_brief
from .performance_reporter import generate_report

# WHY a registry dict: the pipeline orchestrator can look up agents by name
# (useful for logging, SSE events, and error reporting) without importing
# each function individually.
AGENT_REGISTRY = {
    "brief_parser": parse_brief,
    "audience_researcher": research_audience,
    "content_calendar": generate_calendar,
    "creative_brief": generate_creative_brief,
    "performance_reporter": generate_report,
}
