# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt
"""OAuth runtime configuration sourced from environment variables.

`OAUTH_ENABLED` is the master switch: when false (the default for now) the
existing header-based JuspayHeaderAuthMiddleware path is retained so we can
ship this code without breaking current callers (juspay-genius, internal
consumers, etc.). Flip to `true` on the OAuth-protected deployment.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_list(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    if not raw:
        return list(default)
    return [item.strip() for item in raw.split(",") if item.strip()]


DEFAULT_SCOPES = [
    "analytics:read",
    "orders:read",
    "orders:write",
    "settings:read",
    "gateways:read",
    "reports:read",
    "users:read",
    "alerts:read",
]


@dataclass(frozen=True)
class OAuthConfig:
    enabled: bool
    mcp_server_url: str
    portal_base_url: str
    upstream_client_id: str
    upstream_client_secret: str
    scopes_supported: list[str]
    state_ttl_seconds: int
    validation_cache_ttl_seconds: int
    # Dev-only: when set, any incoming bearer equal to this value is treated as
    # an authenticated request bound to a synthetic PortalUserInfo. Lets us
    # smoke-test the middleware + tool dispatch path without burning a real
    # Portal token. NEVER set this in production.
    dev_test_token: str | None = None
    dev_test_merchant_id: str = "TEST_MERCHANT"
    # Optional: extra hostnames that should also be considered valid canonical
    # resource URIs (in case the deployment lives behind multiple DNS names).
    extra_resource_hostnames: list[str] = field(default_factory=list)


def load() -> OAuthConfig:
    cfg = OAuthConfig(
        enabled=_env_bool("OAUTH_ENABLED", False),
        mcp_server_url=os.getenv("MCP_SERVER_URL", "http://localhost:8080").rstrip("/"),
        portal_base_url=os.getenv("PORTAL_BASE_URL", "https://portal.juspay.in").rstrip("/"),
        upstream_client_id=os.getenv("OAUTH_CLIENT_ID", ""),
        upstream_client_secret=os.getenv("OAUTH_CLIENT_SECRET", ""),
        scopes_supported=_env_list("OAUTH_SCOPES_SUPPORTED", DEFAULT_SCOPES),
        state_ttl_seconds=int(os.getenv("OAUTH_STATE_TTL_SECONDS", "600")),
        validation_cache_ttl_seconds=int(
            os.getenv("OAUTH_VALIDATION_CACHE_TTL_SECONDS", "300")
        ),
        dev_test_token=os.getenv("OAUTH_DEV_TEST_TOKEN") or None,
        dev_test_merchant_id=os.getenv("OAUTH_DEV_TEST_MERCHANT_ID", "TEST_MERCHANT"),
        extra_resource_hostnames=_env_list("OAUTH_EXTRA_RESOURCE_HOSTNAMES", []),
    )

    if cfg.enabled:
        logger.info(
            "OAuth enabled — issuer=%s portal=%s scopes=%s dev_test_token=%s",
            cfg.mcp_server_url,
            cfg.portal_base_url,
            cfg.scopes_supported,
            "set" if cfg.dev_test_token else "unset",
        )
        if not cfg.upstream_client_id or not cfg.upstream_client_secret:
            logger.warning(
                "OAUTH_CLIENT_ID / OAUTH_CLIENT_SECRET not set — Portal token "
                "exchange will fail until they are configured."
            )
    else:
        logger.info("OAuth disabled — falling back to header-based auth path.")

    return cfg
