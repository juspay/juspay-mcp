"""Client-side analytics for the juspay-mcp docs + dashboard servers.

Events are emitted best-effort (fire-and-forget) to the genius cli-analytics ingest
endpoint; all session inference + storage lives server-side in genius. This package holds
no DB credentials, schema, or session logic.
"""

from .context import (
    AnalyticsRequestContext,
    clear_current_context,
    get_current_context,
    set_current_context,
)
from .tracker import record_stage_status, record_tool_call

__all__ = [
    "AnalyticsRequestContext",
    "clear_current_context",
    "get_current_context",
    "record_stage_status",
    "record_tool_call",
    "set_current_context",
]
