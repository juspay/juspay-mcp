"""Ships analytics events to the genius cli-analytics ingest endpoint.

Fire-and-forget: record_event schedules the POST as a background task and returns
immediately, so a tool call never waits on analytics. Failures are logged and dropped;
a 401/403 latches analytics off for the process lifetime. shutdown() flushes any pending
posts and closes the shared client.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from .config import load

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None
_pending: set[asyncio.Task] = set()
_disabled_reason: str | None = None
_disabled_logged = False


def _get_client(timeout: float) -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=timeout)
    return _client


def _disable(reason: str) -> None:
    global _disabled_reason, _disabled_logged
    _disabled_reason = reason
    if not _disabled_logged:
        logger.warning("Analytics disabled: %s", reason)
        _disabled_logged = True


async def _post(url: str, token: str, timeout: float, payload: dict[str, Any]) -> None:
    try:
        resp = await _get_client(timeout).post(
            url, json=payload, headers={"Authorization": f"Bearer {token}"}
        )
        if resp.status_code in (401, 403):
            _disable("ingest token rejected — check CLI_ANALYTICS_INGEST_TOKEN")
            return
        resp.raise_for_status()
    except Exception:
        logger.debug("Analytics ingest failed", exc_info=True)  # best-effort: drop the event


async def record_event(
    *,
    install_id: str,
    event: dict[str, Any],
    mid: str | None = None,
    occurred_at: datetime | None = None,
) -> None:
    """Schedule a fire-and-forget POST of one event and return immediately.

    Returns None — the session id is assigned server-side (genius) and not awaited here.
    """
    cfg = load()
    if _disabled_reason is not None:
        return None
    if not (cfg.enabled and cfg.ingest_url and cfg.ingest_token):
        return None

    payload = {
        "install_id": install_id,
        "mid": mid,
        "occurred_at": (occurred_at or datetime.now(timezone.utc)).isoformat(),
        "event": event,
    }
    task = asyncio.create_task(
        _post(cfg.ingest_url, cfg.ingest_token, cfg.http_timeout_seconds, payload)
    )
    _pending.add(task)
    task.add_done_callback(_pending.discard)
    return None


async def shutdown() -> None:
    """Flush pending posts and close the shared client (called from main.py's lifespan)."""
    if _pending:
        await asyncio.gather(*list(_pending), return_exceptions=True)
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
