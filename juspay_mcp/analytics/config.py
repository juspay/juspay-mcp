from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return int(raw)


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def is_local_development() -> bool:
    raw = os.getenv("DEPLOYMENT_ENV") or ""
    return raw.strip().lower() == "local"


@dataclass(frozen=True)
class AnalyticsConfig:
    enabled: bool
    ingest_url: str | None
    ingest_token: str | None
    event_max_bytes: int
    http_timeout_seconds: float


def load() -> AnalyticsConfig:
    ingest_url = os.getenv("CLI_ANALYTICS_INGEST_URL") or None
    ingest_token = os.getenv("CLI_ANALYTICS_INGEST_TOKEN") or None
    # Default on only when we have somewhere to send + a token to send with.
    enabled = _env_bool("CLI_ANALYTICS_ENABLED", bool(ingest_url and ingest_token))
    return AnalyticsConfig(
        enabled=enabled,
        ingest_url=ingest_url,
        ingest_token=ingest_token,
        event_max_bytes=_env_int("CLI_ANALYTICS_EVENT_MAX_BYTES", 32 * 1024),
        http_timeout_seconds=_env_float("CLI_ANALYTICS_HTTP_TIMEOUT_SECONDS", 2.0),
    )
