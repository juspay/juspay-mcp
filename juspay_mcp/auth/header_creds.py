# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt
"""Direct header-credential extraction, used by `JuspayHeaderAuthMiddleware`.

The token is validated by the dashboard tool layer: static `auth_...` tokens
at `/ec/v2/authorize`, other tokens at `/api/ec/v1/validate/token`.
"""

from __future__ import annotations

import os

from starlette.requests import Request

from .request_guards import trusted_base_url

AI_STUDIO_MCP_TYPES = {"PP_AI_STUDIO", "AI_STUDIO"}

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

    base_url_override = trusted_base_url(request.headers.get("x-base-url"), "x-base-url")

    creds: dict = {}
    if api_key:
        creds["api_key"] = api_key
    if merchant_id:
        creds["merchant_id"] = merchant_id
    if dashboard_token:
        creds["dashboard_token"] = dashboard_token
    if base_url_override:
        creds["base_url"] = base_url_override
    if os.getenv("JUSPAY_MCP_TYPE", "").upper() in AI_STUDIO_MCP_TYPES:
        if pp_ai_studio_api_key:
            creds["pp_ai_studio_api_key"] = pp_ai_studio_api_key
        if pp_ai_studio_token:
            creds["pp_ai_studio_token"] = pp_ai_studio_token

    return creds
