# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

r"""Juspay Docs MCP - Genius assistant client.

Thin client over the public "Genius" docs assistant that powers the Juspay
documentation site (an Xyne-backed RAG). It takes a natural-language question
and returns a synthesized, source-cited answer drawn from the official docs.

The endpoint streams Server-Sent Events. Per the SSE spec, an event's data
fields (consecutive `data:` lines) join with "\n"; a blank line terminates the
event. Event types:
    u    -> a fragment of the answer text (fragments across events concatenate
            directly; newlines arrive as multi-line data within an event)
    cu   -> {"contextChunks": [...], "citationMap": {...}} ; the sources. The
            LAST cu event carries the full accumulated set.
    e    -> "end" (stop reading)
Other events (ct, s, rm) are start/metadata markers we ignore.

Public endpoint, no authentication. NOTE: observed to be intermittently flaky
(occasional 401s and empty 200s on identical input); resilience is a phase-2
TODO (see below).
"""

import json
import logging
import re
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

# Public docs assistant endpoint (no auth required).
GENIUS_CHAT_URL = "https://juspay.io/in/docs/api/xyne/chat"

# Docs knowledge-base scope, sent verbatim. NOTE: this value is intentionally
# double-URL-encoded (it mirrors the docs-site widget). Do NOT re-encode it.
DEFAULT_PATH = "Juspay%2520Integration%2520Docs%252Fjuspay_docs%252Fin"

# Used to rebuild citable public URLs from internal knowledge-base titles.
_PUBLIC_PREFIX = "https://juspay.io/in/docs/"
_KB_MARKER = "/juspay_docs/in/"

# Xyne emits inline citation markers like "K[21_8]" / "K[7_4]"; the sources are
# returned separately, so strip the markers from the prose.
_CITATION_RE = re.compile(r" ?K\[\d+(?:_\d+)?\]")

_TIMEOUT = httpx.Timeout(90.0, connect=10.0)
_HEADERS = {
    "Accept": "text/event-stream",
    "Referer": "https://juspay.io/in/docs/",
    "User-Agent": "juspay-docs-mcp",
}


def _public_url(title: str) -> str | None:
    """Rebuild a public docs URL from a context-chunk `title`.

    Context chunks carry an internal Xyne link (`/cl/<uuid>`) that isn't usable
    publicly; the `title` holds the real doc path, e.g.
    `Juspay Integration Docs_.../juspay_docs/in/hyper-checkout/.../handle-payment-response.md`
    -> `https://juspay.io/in/docs/hyper-checkout/.../handle-payment-response`.
    """
    idx = title.find(_KB_MARKER)
    if idx == -1:
        return None
    rel = title[idx + len(_KB_MARKER):].strip()
    if not rel:
        return None
    if rel.endswith(".md"):
        rel = rel[:-3]
    return _PUBLIC_PREFIX + rel


def _sources_from_chunks(chunks: list[dict]) -> list[dict]:
    """De-dupe context chunks into an ordered list of {title, url}."""
    seen: set[str] = set()
    sources: list[dict] = []
    for chunk in chunks:
        url = _public_url(chunk.get("title", ""))
        if url and url not in seen:
            seen.add(url)
            sources.append({"title": chunk.get("page_title") or url, "url": url})
    return sources


def _clean_answer(text: str) -> str:
    """Strip Xyne inline citation markers; return trimmed prose."""
    return _CITATION_RE.sub("", text).strip()


async def ask_genius(query: str, path: str = DEFAULT_PATH) -> dict:
    """Ask the Genius docs assistant; return {"answer": str, "sources": [...]}.

    Raises httpx.HTTPError on transport/HTTP failure - the caller is expected to
    handle it and degrade gracefully. (Retry/resilience is a phase-2 TODO above.)
    """
    # `query` is URL-encoded; `path` is already (double-)encoded and sent verbatim.
    url = f"{GENIUS_CHAT_URL}?query={quote(query, safe='')}&path={path}"

    answer_parts: list[str] = []
    chunks: list[dict] = []
    cur_event: str | None = None
    data_buf: list[str] = []

    def dispatch() -> None:
        """Finish the buffered SSE event: join its data fields and route them."""
        nonlocal chunks, cur_event, data_buf
        if cur_event is not None and data_buf:
            payload = "\n".join(data_buf)  # SSE: an event's data fields join with \n
            if cur_event == "u":
                answer_parts.append(payload)
            elif cur_event == "cu":
                try:
                    chunks = json.loads(payload).get("contextChunks", chunks)
                except json.JSONDecodeError:
                    pass
        cur_event = None
        data_buf = []

    async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
        async with client.stream("GET", url, headers=_HEADERS) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line == "":  # blank line terminates the current event
                    ending = cur_event == "e"
                    dispatch()
                    if ending:
                        break
                    continue
                if line.startswith("event:"):
                    cur_event = line[len("event:"):].strip()
                elif line.startswith("data:"):
                    value = line[len("data:"):]
                    if value.startswith(" "):  # SSE: strip one optional leading space
                        value = value[1:]
                    data_buf.append(value)
            dispatch()  # flush a trailing event with no terminating blank line

    return {
        "answer": _clean_answer("".join(answer_parts)),
        "sources": _sources_from_chunks(chunks),
    }
