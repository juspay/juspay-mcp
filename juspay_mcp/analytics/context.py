from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass

from starlette.requests import Request


INSTALL_ID_HEADER = "x-juspay-install-id"
SESSION_ID_HEADER = "x-juspay-session-id"


@dataclass(frozen=True)
class AnalyticsRequestContext:
    mcp: str
    install_id: str | None
    mid: str | None
    session_id: str | None = None


_current: ContextVar[AnalyticsRequestContext | None] = ContextVar(
    "juspay_mcp_analytics_context",
    default=None,
)


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _mid_from_request(request: Request) -> str | None:
    oauth_context = getattr(request.state, "oauth_context", None)
    if oauth_context and getattr(oauth_context, "user_info", None):
        return _empty_to_none(getattr(oauth_context.user_info, "merchant_id", None))

    creds = getattr(request.state, "juspay_credentials", None)
    if isinstance(creds, dict):
        return _empty_to_none(creds.get("merchant_id"))
    return None


def from_request(request: Request, mcp: str) -> AnalyticsRequestContext:
    return AnalyticsRequestContext(
        mcp=mcp,
        install_id=_empty_to_none(request.headers.get(INSTALL_ID_HEADER)),
        mid=_mid_from_request(request),
        session_id=_empty_to_none(request.headers.get(SESSION_ID_HEADER)),
    )


def set_current_context(ctx: AnalyticsRequestContext | None) -> None:
    _current.set(ctx)


def get_current_context() -> AnalyticsRequestContext | None:
    return _current.get()


def clear_current_context() -> None:
    _current.set(None)
