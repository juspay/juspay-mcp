# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt
"""OAuth 2.1 subsystem for juspay-mcp.

Implements the MCP 2025-06 authorization profile so Claude Code (and any other
OAuth-aware MCP client) can connect to mcp.juspay.in via the Juspay Portal
identity provider.

Layout:
    config.py        — env-driven configuration object
    context.py       — ContextVar holding the validated PortalUserInfo
    metadata.py      — RFC 9728 / RFC 8414 metadata document builders
    pkce.py          — PKCE S256 helpers
    portal_client.py — async wrapper around portal.juspay.in OAuth endpoints
    state_store.py   — TTL'd in-memory store for /authorize state + code rows
    middleware.py    — Bearer auth Starlette middleware
    routes.py        — Starlette Route list for /.well-known/* + /oauth/*
"""
