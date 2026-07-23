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
    agent: str | None = None


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


def _id_from_request(request: Request, query_key: str, header_key: str) -> str | None:
    # Query param first, header fallback. The query string is the durable carrier:
    # some clients don't forward custom headers at all (e.g. older Codex), and
    # TLS-inspecting corporate proxies strip custom headers — but the URL query
    # always reaches the origin. The header stays as a secondary path.
    return _empty_to_none(request.query_params.get(query_key)) or _empty_to_none(
        request.headers.get(header_key)
    )


def from_request(request: Request, mcp: str) -> AnalyticsRequestContext:
    # `agent` = the CLI-written query slug (claude/codex/cursor/…), falling back to the
    # client's User-Agent (a standard header proxies don't strip) when the slug is absent.
    agent = _empty_to_none(request.query_params.get("agent")) or _empty_to_none(
        request.headers.get("user-agent")
    )
    return AnalyticsRequestContext(
        mcp=mcp,
        install_id=_id_from_request(request, "install_id", INSTALL_ID_HEADER),
        mid=_mid_from_request(request),
        session_id=_id_from_request(request, "session_id", SESSION_ID_HEADER),
        agent=agent,
    )


def set_current_context(ctx: AnalyticsRequestContext | None) -> None:
    _current.set(ctx)


def get_current_context() -> AnalyticsRequestContext | None:
    return _current.get()


def clear_current_context() -> None:
    _current.set(None)
