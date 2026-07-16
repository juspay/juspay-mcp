from __future__ import annotations

import logging
import time
from typing import Any

from .config import load
from .context import get_current_context
from .redaction import fit_jsonb_payload
from .client import record_event

logger = logging.getLogger(__name__)


async def _emit(payload: dict[str, Any], *, mid: str | None = None) -> None:
    ctx = get_current_context()
    event_type = str(payload.get("type") or "unknown")
    tool = payload.get("tool")
    if ctx is None:
        logger.debug("Analytics skipped: no request context type=%s tool=%s", event_type, tool)
        return
    if not ctx.install_id:
        logger.info("Analytics skipped: missing install_id mcp=%s type=%s tool=%s", ctx.mcp, event_type, tool)
        return

    cfg = load()
    if not cfg.enabled:
        logger.debug("Analytics skipped: disabled mcp=%s type=%s tool=%s", ctx.mcp, event_type, tool)
        return

    event = {
        "mcp": ctx.mcp,
        **payload,
    }
    event = fit_jsonb_payload(event, cfg.event_max_bytes)
    event_mid = mid or ctx.mid
    # Fire-and-forget: record_event schedules the POST and returns None immediately.
    await record_event(install_id=ctx.install_id, mid=event_mid, event=event)


async def record_stage_status(
    *,
    phase: str,
    status: str,
    product: str | None = None,
    platform: str | None = None,
    framework: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    await _emit(
        {
            "type": "stage_status",
            "tool": "juspay_track_integration_stage",
            "phase": phase,
            "status": status,
            "product": product,
            "platform": platform,
            "framework": framework,
            "metadata": metadata or {},
        }
    )


async def record_tool_call(
    *,
    tool: str,
    status: str,
    started_at: float,
    arguments: dict[str, Any] | None = None,
    error: str | None = None,
    mid: str | None = None,
) -> None:
    payload: dict[str, Any] = {
        "type": "tool_call",
        "tool": tool,
        "status": status,
        "duration_ms": int((time.perf_counter() - started_at) * 1000),
        "arguments": arguments or {},
    }
    if error:
        payload["error"] = error
    await _emit(payload, mid=mid)
