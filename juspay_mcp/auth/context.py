# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt
"""Per-request OAuth context.

Mirrors the existing `juspay_request_credentials` ContextVar pattern used by
`juspay_mcp.tools` so tool handlers can read OAuth identity without threading
it through every call.
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class PortalUserInfo:
    merchant_id: str
    user_id: str
    email: str
    context: str  # MERCHANT | TENANT | RESELLER | JUSPAY
    username: str | None = None
    tenant_account_id: str | None = None
    valid_host: str | None = None


@dataclass(frozen=True)
class OAuthRequestContext:
    access_token: str
    user_info: PortalUserInfo


_current: ContextVar[OAuthRequestContext | None] = ContextVar(
    "juspay_mcp_oauth_context", default=None
)


def set_current(ctx: OAuthRequestContext | None) -> None:
    _current.set(ctx)


def get_current() -> OAuthRequestContext | None:
    return _current.get()


def clear_current() -> None:
    _current.set(None)
