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
from .tenant import BASE_URL_HEADER, resolve as resolve_tenant

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
        skip_path_prefixes: tuple[str, ...] = (),
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
        self._skip_path_prefixes = skip_path_prefixes

    async def _validate_with_cache(
        self, token: str, cfg: OAuthConfig
    ) -> PortalUserInfo | None:
        # Dev bypass: useful for curl-driven smoke tests so we don't need a
        # real Portal token. The token value is configured via env and never
        # rotates, so it must NEVER be set in production.
        if cfg.dev_test_token and token == cfg.dev_test_token:
            return PortalUserInfo(
                merchant_id=cfg.dev_test_merchant_id,
                user_id="dev-user",
                email="dev@example.com",
                context="MERCHANT",
                username="dev",
                tenant_account_id=None,
                valid_host=None,
            )

        # Keyed by portal too: the same token string must not be treated as
        # validated for a tenant it was never presented to.
        cache_key = f"{cfg.portal_base_url}\n{token}"
        now = time.time()
        cached = self._cache.get(cache_key)
        if cached is not None:
            user_info, expiry = cached
            if expiry > now:
                return user_info
            self._cache.pop(cache_key, None)

        user_info = await self._portal.validate(
            token, portal_base_url=cfg.portal_base_url
        )
        if user_info is None:
            return None
        self._cache[cache_key] = (user_info, now + cfg.validation_cache_ttl_seconds)
        return user_info

    def _challenge_header(
        self, request: Request, cfg: OAuthConfig, error: str | None = None
    ) -> str:
        # Per RFC 9728 §5.1 the WWW-Authenticate header must point to the
        # resource_metadata URL. We use the per-mount path when present so the
        # client can fall back to well-known probing if the header is dropped
        # by an intermediary.
        path = request.url.path
        # Strip any trailing /messages or /stream suffix so we land on the
        # mount-level well-known doc.
        base = path.rsplit("/", 1)[0] if path.count("/") > 1 else path
        prm_url = f"{cfg.mcp_server_url}{base}/.well-known/oauth-protected-resource"
        parts = [f'Bearer resource_metadata="{prm_url}"']
        if cfg.scopes_supported:
            parts.append(f'scope="{" ".join(cfg.scopes_supported)}"')
        if error:
            parts.append(f'error="{error}"')
        return ", ".join(parts)

    def _unauthorized(
        self,
        request: Request,
        cfg: OAuthConfig,
        error: str | None = None,
        message: str = "Authentication required",
    ) -> Response:
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "error": {"code": -32001, "message": message},
                "id": None,
            },
            status_code=401,
            headers={"WWW-Authenticate": self._challenge_header(request, cfg, error)},
        )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        path = request.url.path
        if _is_public_path(path):
            return await call_next(request)
        if self._skip_path_prefixes and any(
            path == p or path.startswith(p + "/") for p in self._skip_path_prefixes
        ):
            return await call_next(request)

        cfg = resolve_tenant(self._cfg, request)

        auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            return self._unauthorized(request, cfg)

        token = auth_header[7:].strip()
        if not token:
            return self._unauthorized(request, cfg, error="invalid_token")

        user_info = await self._validate_with_cache(token, cfg)
        if user_info is None:
            return self._unauthorized(
                request, cfg, error="invalid_token", message="Invalid or expired token"
            )

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
        base_url_override = request.headers.get(BASE_URL_HEADER)
        tenant_id_override = request.headers.get("x-tenant-id")
        if base_url_override:
            request.state.juspay_credentials["base_url"] = base_url_override
        if tenant_id_override:
            request.state.juspay_credentials["tenant_id"] = tenant_id_override

        try:
            return await call_next(request)
        finally:
            clear_current()
