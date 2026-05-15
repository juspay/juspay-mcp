# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt
"""Bearer auth middleware.

For any non-public path it requires `Authorization: Bearer <token>`, validates
the token against Portal (with a short-lived LRU cache to avoid hammering the
upstream), and pushes a PortalUserInfo onto a ContextVar so tool handlers can
read it. On failure it returns a JSON-RPC `-32001` error with the
`WWW-Authenticate` header demanded by RFC 9728 §5.1.
"""

from __future__ import annotations

import logging
import time
from typing import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .config import OAuthConfig
from .context import OAuthRequestContext, PortalUserInfo, clear_current, set_current
from .portal_client import PortalClient

logger = logging.getLogger(__name__)

# Paths that bypass the bearer check entirely. The MCP transport endpoints
# themselves are NOT in this list — they require auth.
_PUBLIC_PATH_PREFIXES = (
    "/health",
    "/.well-known/",
    "/oauth/",
)


def _is_public_path(path: str) -> bool:
    if path in ("/health", "/health/ready"):
        return True
    for prefix in _PUBLIC_PATH_PREFIXES:
        if path.startswith(prefix):
            return True
    # Per-mount well-known docs (e.g. /juspay-dashboard-stream/.well-known/...)
    if "/.well-known/" in path:
        return True
    return False


class BearerAuthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        cfg: OAuthConfig,
        portal: PortalClient,
        validation_cache: dict[str, tuple[PortalUserInfo, float]] | None = None,
    ) -> None:
        super().__init__(app)
        self._cfg = cfg
        self._portal = portal
        # token -> (user_info, expiry_epoch). When `validation_cache` is passed
        # in, the same dict is also shared with /oauth/revoke so that revoked
        # tokens are evicted immediately instead of lingering until their TTL.
        self._cache: dict[str, tuple[PortalUserInfo, float]] = (
            validation_cache if validation_cache is not None else {}
        )

    async def _validate_with_cache(self, token: str) -> PortalUserInfo | None:
        # Dev bypass: useful for curl-driven smoke tests so we don't need a
        # real Portal token. The token value is configured via env and never
        # rotates, so it must NEVER be set in production.
        if self._cfg.dev_test_token and token == self._cfg.dev_test_token:
            return PortalUserInfo(
                merchant_id=self._cfg.dev_test_merchant_id,
                user_id="dev-user",
                email="dev@example.com",
                context="MERCHANT",
                username="dev",
                tenant_account_id=None,
                valid_host=None,
            )

        now = time.time()
        cached = self._cache.get(token)
        if cached is not None:
            user_info, expiry = cached
            if expiry > now:
                return user_info
            self._cache.pop(token, None)

        user_info = await self._portal.validate(token)
        if user_info is None:
            return None
        self._cache[token] = (user_info, now + self._cfg.validation_cache_ttl_seconds)
        return user_info

    def _challenge_header(self, request: Request, error: str | None = None) -> str:
        # Per RFC 9728 §5.1 the WWW-Authenticate header must point to the
        # resource_metadata URL. We use the per-mount path when present so the
        # client can fall back to well-known probing if the header is dropped
        # by an intermediary.
        path = request.url.path
        # Strip any trailing /messages or /stream suffix so we land on the
        # mount-level well-known doc.
        base = path.rsplit("/", 1)[0] if path.count("/") > 1 else ""
        prm_url = f"{self._cfg.mcp_server_url}{base}/.well-known/oauth-protected-resource"
        parts = [f'Bearer resource_metadata="{prm_url}"']
        if self._cfg.scopes_supported:
            parts.append(f'scope="{" ".join(self._cfg.scopes_supported)}"')
        if error:
            parts.append(f'error="{error}"')
        return ", ".join(parts)

    def _unauthorized(
        self, request: Request, error: str | None = None, message: str = "Authentication required"
    ) -> Response:
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "error": {"code": -32001, "message": message},
                "id": None,
            },
            status_code=401,
            headers={"WWW-Authenticate": self._challenge_header(request, error)},
        )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if _is_public_path(request.url.path):
            return await call_next(request)

        auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            return self._unauthorized(request)

        token = auth_header[7:].strip()
        if not token:
            return self._unauthorized(request, error="invalid_token")

        user_info = await self._validate_with_cache(token)
        if user_info is None:
            return self._unauthorized(request, error="invalid_token", message="Invalid or expired token")

        ctx = OAuthRequestContext(access_token=token, user_info=user_info)
        set_current(ctx)
        # Also stash on request.state so existing handlers can read it inline.
        request.state.oauth_context = ctx
        # Compatibility shim for the legacy ContextVar in juspay_mcp.tools:
        # populate juspay_credentials with the Portal-issued token so existing
        # handlers keep working without any modification. The dashboard mcp
        # already expects `dashboard_token`; core expects `api_key` +
        # `merchant_id`. We provide all three so both modes work.
        request.state.juspay_credentials = {
            "api_key": token,
            "merchant_id": user_info.merchant_id,
            "dashboard_token": token,
            # Signals to the dashboard tool handlers (which have their own
            # token-validation step) that this request is OAuth-sourced. They
            # branch on this to hit /ec/v2/authorize instead of the legacy
            # /api/ec/v1/validate/token endpoint. See
            # juspay_dashboard_mcp/api/utils.py:get_juspay_host_from_api.
            "auth_type": "oauth",
        }

        try:
            return await call_next(request)
        finally:
            clear_current()
