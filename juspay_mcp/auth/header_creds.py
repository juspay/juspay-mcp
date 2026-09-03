# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt
"""Direct header-credential extraction.

Shared by `JuspayHeaderAuthMiddleware` and by `BearerAuthMiddleware`'s
no-bearer fallback, so both read exactly the same header set. The dict produced
here deliberately carries NO `auth_type` key: its absence is what makes
`juspay_dashboard_mcp/api/utils.py` validate the token at
`/api/ec/v1/validate/token` rather than `/ec/v2/authorize`.
"""

from __future__ import annotations

import os

from starlette.requests import Request

AI_STUDIO_MCP_TYPES = {"PP_AI_STUDIO", "AI_STUDIO"}

# Keys that represent an actual credential, as opposed to the edge-routing
# hints (base_url / tenant_id) which may accompany any request.
_CREDENTIAL_KEYS = (
    "api_key",
    "dashboard_token",
    "pp_ai_studio_api_key",
    "pp_ai_studio_token",
)


def _strip_bearer(value: str | None) -> str | None:
    if value and value[:7].lower() == "bearer ":
        return value[7:].strip() or None
    return value


def extract_header_credentials(request: Request) -> dict:
    """Pull Juspay credentials out of the request headers.

    Returns a possibly-empty dict. Missing values are not an error — the tool
    layer falls back to environment variables for anything absent.
    """
    api_key = request.headers.get("JUSPAY_API_KEY")
    merchant_id = request.headers.get("JUSPAY_MERCHANT_ID")
    dashboard_token = _strip_bearer(request.headers.get("JUSPAY_WEB_LOGIN_TOKEN"))
    pp_ai_studio_api_key = request.headers.get("PP_AI_STUDIO_API_KEY")
    pp_ai_studio_token = (
        request.headers.get("PP_AI_STUDIO_TOKEN")
        or request.headers.get("JUSPAY_AI_STUDIO_TOKEN")
    )

    base_url_override = request.headers.get("x-base-url")
    tenant_id_override = request.headers.get("x-tenant-id")

    creds: dict = {}
    if api_key:
        creds["api_key"] = api_key
    if merchant_id:
        creds["merchant_id"] = merchant_id
    if dashboard_token:
        creds["dashboard_token"] = dashboard_token
    if base_url_override:
        creds["base_url"] = base_url_override
    if tenant_id_override:
        creds["tenant_id"] = tenant_id_override
    if os.getenv("JUSPAY_MCP_TYPE", "").upper() in AI_STUDIO_MCP_TYPES:
        if pp_ai_studio_api_key:
            creds["pp_ai_studio_api_key"] = pp_ai_studio_api_key
        if pp_ai_studio_token:
            creds["pp_ai_studio_token"] = pp_ai_studio_token

    return creds


def has_credential(creds: dict) -> bool:
    """True when `creds` carries a real credential, not just routing hints.

    `x-base-url` / `x-tenant-id` alone must never count as authentication —
    otherwise any request through the edge would sail past the bearer check.
    """
    return any(creds.get(key) for key in _CREDENTIAL_KEYS)
