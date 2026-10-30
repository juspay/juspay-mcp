# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt
"""
Guard for request-supplied routing hints.

`x-base-url` / `x-mcp-server-url` decide where credentials get sent, so when
`ALLOWED_BASE_URL_HOSTS` is set they are only honoured for listed hosts. When it
is unset the headers are trusted as before (the edge proxy is expected to own
them).
"""

from __future__ import annotations

import logging
import os
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def _allowed_hosts() -> list[str]:
    raw = os.getenv("ALLOWED_BASE_URL_HOSTS", "")
    return [h.strip().lower() for h in raw.split(",") if h.strip()]


def is_allowed_base_url(url: str) -> bool:
    """True when `url` may be used as an outbound or advertised base URL.

    Entries are exact hostnames (`dashboard.example.com`) or `*.example.com`,
    which matches subdomains but not the bare domain.
    """
    allowed = _allowed_hosts()
    if not allowed:
        return True
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https") or not host:
        return False
    if parsed.username or parsed.password:
        return False
    for entry in allowed:
        if entry.startswith("*."):
            if host.endswith(entry[1:]):
                return True
        elif host == entry:
            return True
    return False


def trusted_base_url(url: str | None, header: str) -> str | None:
    """Return `url` if it passes the allowlist, else None (and log)."""
    if not url:
        return None
    if is_allowed_base_url(url):
        return url
    logger.warning("Ignoring %s header: host is not in ALLOWED_BASE_URL_HOSTS", header)
    return None
