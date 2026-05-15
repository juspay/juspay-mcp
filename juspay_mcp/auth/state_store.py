# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt
"""TTL'd in-memory store for OAuth `state` and authorization `code` rows.

This is good enough for single-process deployments and dev. Swap in a Redis
backend later by implementing the same interface (`StateStore`).
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Protocol


@dataclass
class StateData:
    redirect_uri: str
    client_id: str | None
    scope: str | None
    resource: str | None
    code_challenge: str | None
    code_challenge_method: str | None
    created_at: float


class StateStore(Protocol):
    async def put_state(self, state: str, data: StateData) -> None: ...
    async def get_state(self, state: str) -> StateData | None: ...
    async def delete_state(self, state: str) -> None: ...
    async def bind_code(self, code: str, state: str) -> None: ...
    async def lookup_state_by_code(self, code: str) -> str | None: ...
    async def delete_code(self, code: str) -> None: ...


class MemoryStateStore:
    def __init__(self, ttl_seconds: int = 600) -> None:
        self._ttl = ttl_seconds
        self._states: dict[str, StateData] = {}
        self._code_to_state: dict[str, str] = {}
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
                await asyncio.sleep(60)
                await self._sweep()
            except asyncio.CancelledError:
                raise
            except Exception:
                continue

    async def _sweep(self) -> None:
        now = time.time()
        async with self._lock:
            expired = [s for s, d in self._states.items() if now - d.created_at > self._ttl]
            for s in expired:
                self._states.pop(s, None)
            orphan_codes = [c for c, s in self._code_to_state.items() if s not in self._states]
            for c in orphan_codes:
                self._code_to_state.pop(c, None)

    async def put_state(self, state: str, data: StateData) -> None:
        async with self._lock:
            self._states[state] = data

    async def get_state(self, state: str) -> StateData | None:
        async with self._lock:
            data = self._states.get(state)
            if data is None:
                return None
            if time.time() - data.created_at > self._ttl:
                self._states.pop(state, None)
                return None
            return data

    async def delete_state(self, state: str) -> None:
        async with self._lock:
            self._states.pop(state, None)

    async def bind_code(self, code: str, state: str) -> None:
        async with self._lock:
            self._code_to_state[code] = state

    async def lookup_state_by_code(self, code: str) -> str | None:
        async with self._lock:
            return self._code_to_state.get(code)

    async def delete_code(self, code: str) -> None:
        async with self._lock:
            self._code_to_state.pop(code, None)
