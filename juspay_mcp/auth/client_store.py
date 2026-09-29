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
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ClientData:
    client_secret: str
    redirect_uris: list[str]
    client_name: str
    created_at: float


class ClientStore(Protocol):
    async def put_client(self, client_id: str, data: ClientData) -> None: ...
    async def get_client(self, client_id: str) -> ClientData | None: ...


class MemoryClientStore:
    def __init__(self) -> None:
        self._clients: dict[str, ClientData] = {}
        self._lock = asyncio.Lock()

    async def put_client(self, client_id: str, data: ClientData) -> None:
        async with self._lock:
            self._clients[client_id] = data

    async def get_client(self, client_id: str) -> ClientData | None:
        async with self._lock:
            return self._clients.get(client_id)
