# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt
"""
Per-request OAuth configuration for multi-tenant deployments.
"""

from __future__ import annotations

import dataclasses

from starlette.requests import Request

from .config import OAuthConfig

BASE_URL_HEADER = "x-base-url"
MCP_SERVER_URL_HEADER = "x-mcp-server-url"


def resolve(cfg: OAuthConfig, request: Request) -> OAuthConfig:
    """Specialise `cfg` to the tenant identified by the request's edge headers."""
    base_url = (request.headers.get(BASE_URL_HEADER) or "").strip().rstrip("/")
    mcp_server_url = (request.headers.get(MCP_SERVER_URL_HEADER) or "").strip().rstrip("/")
    if not base_url and not mcp_server_url:
        return cfg

    overrides: dict[str, str] = {}
    if base_url:
        overrides["portal_base_url"] = base_url
    if mcp_server_url:
        overrides["mcp_server_url"] = mcp_server_url

    return dataclasses.replace(cfg, **overrides)
