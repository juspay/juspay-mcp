# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt
"""OAuth metadata document builders.

`protected_resource_metadata` — RFC 9728 doc returned at
`/.well-known/oauth-protected-resource` (and per-mount variants). Tells the
MCP client which authorization server(s) issue valid tokens for this resource.

`authorization_server_metadata` — RFC 8414 doc returned at
`/.well-known/oauth-authorization-server` (and aliased at
`/.well-known/openid-configuration` for OIDC discovery fallback). Advertises
endpoints, supported grant types, PKCE methods, and DCR endpoint.
"""

from __future__ import annotations

from .config import OAuthConfig


def protected_resource_metadata(cfg: OAuthConfig, resource_url: str | None = None) -> dict:
    """Build the protected-resource metadata document.

    `resource_url` lets callers override the canonical resource per mount-point
    (e.g. `…/juspay-dashboard-stream`). When omitted we advertise the bare
    issuer URL, which Claude Code accepts.
    """
    return {
        "resource": resource_url or cfg.mcp_server_url,
        "authorization_servers": [cfg.mcp_server_url],
        "bearer_methods_supported": ["header"],
        "scopes_supported": cfg.scopes_supported,
    }


def authorization_server_metadata(cfg: OAuthConfig) -> dict:
    base = cfg.mcp_server_url
    return {
        "issuer": base,
        "authorization_endpoint": f"{base}/oauth/authorize",
        "token_endpoint": f"{base}/oauth/token",
        "registration_endpoint": f"{base}/oauth/register",
        "revocation_endpoint": f"{base}/oauth/revoke",
        "jwks_uri": f"{base}/.well-known/jwks.json",
        "scopes_supported": cfg.scopes_supported,
        "response_types_supported": ["code"],
        "response_modes_supported": ["query"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": [
            "client_secret_post",
            "client_secret_basic",
            "none",
        ],
        "service_documentation": "https://docs.juspay.in",
    }
