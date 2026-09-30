# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt
"""In-memory store for RFC 7591 dynamically-registered OAuth clients.

Each registered MCP client (Cursor, Claude Desktop, ...) gets its own
randomly generated `client_id`/`client_secret` pair plus the `redirect_uris`
it declared at registration time. This is what `/oauth/authorize` and
`/oauth/token` check against, instead of trusting whatever the caller claims.

Same shape/limitations as `state_store.MemoryStateStore`: single-process,
in-memory, good enough for one deployment. Swap in a Redis/DB-backed
implementation later by matching this interface.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ClientData:
    client_secret: str | None
    redirect_uris: list[str]
    client_name: str
    created_at: float
    last_used_at: float


class ClientStore(Protocol):
    async def put_client(self, client_id: str, data: ClientData) -> None: ...
    async def get_client(self, client_id: str) -> ClientData | None: ...
    async def touch_client(self, client_id: str) -> None: ...


class MemoryClientStore:
    """In-memory registered-client store with inactivity-based expiry.

    Unlike MemoryStateStore's short-lived state (minutes), a client
    registration is a persistent identity reused for weeks/months. Evicting
    by creation time would log out active sessions just because they're old,
    so entries expire only after `ttl_seconds` of no successful use — an
    actively-used client never expires; only abandoned/spam registrations do.
    """

    def __init__(self, ttl_seconds: int = 60 * 60 * 24 * 90) -> None:
        self._ttl = ttl_seconds
        self._clients: dict[str, ClientData] = {}
        self._lock = asyncio.Lock()
        self._sweeper_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self._sweeper_task is None:
            self._sweeper_task = asyncio.create_task(self._sweep_loop())

    async def stop(self) -> None:
        if self._sweeper_task is not None:
            self._sweeper_task.cancel()
            try:
                await self._sweeper_task
            except (asyncio.CancelledError, Exception):
                pass
            self._sweeper_task = None

    async def _sweep_loop(self) -> None:
        while True:
            try:
                await asyncio.sleep(3600)
                await self._sweep()
            except asyncio.CancelledError:
                raise
            except Exception:
                continue

    async def _sweep(self) -> None:
        now = time.time()
        async with self._lock:
            expired = [
                cid for cid, d in self._clients.items() if now - d.last_used_at > self._ttl
            ]
            for cid in expired:
                self._clients.pop(cid, None)

    async def put_client(self, client_id: str, data: ClientData) -> None:
        async with self._lock:
            self._clients[client_id] = data

    async def get_client(self, client_id: str) -> ClientData | None:
        async with self._lock:
            data = self._clients.get(client_id)
            if data is None:
                return None
            if time.time() - data.last_used_at > self._ttl:
                self._clients.pop(client_id, None)
                return None
            return data

    async def touch_client(self, client_id: str) -> None:
        async with self._lock:
            data = self._clients.get(client_id)
            if data is not None:
                data.last_used_at = time.time()
