# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

"""
Juspay Docs MCP — v2 dynamic loader.

Discovers documentation sources at startup by parsing the root llms.txt at
juspay.io. On success, persists a snapshot. On hard failure, falls back to the
last persisted snapshot (or boots empty).

This module does not modify the existing static docs MCP in juspay_docs_mcp/tools.py.
It builds a parallel server (mounted separately by main.py) that reuses the same
create_server() and the hand-tuned `instructions` + `transcripts_map`.
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Optional

import httpx
from pydantic import Field

from juspay_docs_mcp.mcpdoc.main import DocSource, create_server

logger = logging.getLogger(__name__)


ROOT_LLMS_URL = os.getenv(
    "JUSPAY_DOCS_V2_ROOT_LLMS_URL",
    "https://juspay.io/in/docs/llms.txt",
)
SNAPSHOT_PATH = Path(
    os.getenv(
        "JUSPAY_DOCS_V2_SNAPSHOT_PATH",
        str(Path(__file__).parent / "snapshot.json"),
    )
)
HTTP_TIMEOUT = float(os.getenv("JUSPAY_DOCS_V2_TIMEOUT", "30"))
ROOT_FETCH_RETRIES = int(os.getenv("JUSPAY_DOCS_V2_RETRIES", "3"))
VALIDATION_CONCURRENCY = int(os.getenv("JUSPAY_DOCS_V2_VALIDATION_CONCURRENCY", "20"))

# Real product llms.txt files are several KB. Stub responses from the catch-all
# are ~100 bytes. 500 bytes is a safe floor.
REAL_LLMS_MIN_BYTES = 500
# Real titles end in "Documentation LLM Guidelines"; stubs end in " - LLM Guidelines".
REAL_TITLE_MARKER = "Documentation LLM Guidelines"


# ---- Parsing the root llms.txt -------------------------------------------------

_PRODUCT_HEADER_RE = re.compile(
    r"^- \*\*\[(?P<title>.+?)\]\((?P<url>https?://[^\)]+)\)\*\*\s*$"
)
_KV_RE = re.compile(
    r"^(?P<key>Description|ID|Sitemap|LLMS):\s*(?P<value>.+?)\s*$"
)
_CATEGORY_RE = re.compile(r"^### Category:\s*(?P<name>.+?)\s*$")


def parse_doc_sources(text: str) -> list[dict]:
    """Walk the root llms.txt and emit enriched source entries.

    Block layout:
        ### Category: <NAME>
        - **[<Title>](<product_url>)**
        Description: <one-line text>
        ID: <slug>
        Sitemap: <url>
        LLMS: <url>

    A given LLMS URL can appear multiple times — e.g. several entries under
    "Resources" share `resources/llms.txt` because each is a different topic
    inside that product (Error Codes, Refunds, Release Notes, etc.). We keep
    each block as its own entry so the LLM has rich topic-level discovery,
    even though the underlying `fetch_docs` target is the same product index.

    Each emitted entry is a superset of `DocSource`:
        {name, llms_txt, description, category, title}
    The `category` and `title` fields are dropped before the list is handed
    to `create_server`; they're retained for the v2-only `browse_doc_sources`
    tool.
    """
    sources: list[dict] = []
    current_category: Optional[str] = None
    current_block: dict = {}

    def flush() -> None:
        nonlocal current_block
        llms = current_block.get("llms_txt")
        title = current_block.get("title")
        if llms and title:
            description = current_block.get("description", "").strip() or (
                f"Official documentation for {title}."
            )
            sources.append(
                {
                    "name": f"Name: {title}\n\n{description}",
                    "llms_txt": llms,
                    "description": description,
                    "category": current_block.get("category"),
                    "title": title,
                }
            )
        current_block = {}

    for raw in text.splitlines():
        line = raw.rstrip()
        cat = _CATEGORY_RE.match(line)
        if cat:
            current_category = cat.group("name").strip()
            continue

        header = _PRODUCT_HEADER_RE.match(line)
        if header:
            flush()
            current_block = {
                "title": header.group("title").strip(),
                "category": current_category,
            }
            continue

        kv = _KV_RE.match(line)
        if kv and current_block:
            key = kv.group("key").lower()
            value = kv.group("value").strip()
            if key == "description":
                current_block["description"] = value
            elif key == "llms":
                current_block["llms_txt"] = value
            elif key == "id":
                current_block["id"] = value
            elif key == "sitemap":
                current_block["sitemap"] = value

    flush()
    return sources


# ---- HTTP fetch with retries ---------------------------------------------------

async def fetch_root_llms_txt(client: httpx.AsyncClient) -> str:
    """Fetch the root llms.txt with exponential backoff retries."""
    delay = 1.0
    last_exc: Optional[Exception] = None
    for attempt in range(1, ROOT_FETCH_RETRIES + 1):
        try:
            resp = await client.get(ROOT_LLMS_URL, timeout=HTTP_TIMEOUT)
            resp.raise_for_status()
            return resp.text
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            last_exc = e
            if attempt < ROOT_FETCH_RETRIES:
                logger.warning(
                    "Root llms.txt fetch attempt %d/%d failed: %s. Retrying in %.1fs",
                    attempt,
                    ROOT_FETCH_RETRIES,
                    e,
                    delay,
                )
                await asyncio.sleep(delay)
                delay *= 2
            else:
                logger.error(
                    "Root llms.txt fetch failed after %d attempts: %s", attempt, e
                )
    raise RuntimeError(f"Failed to fetch {ROOT_LLMS_URL}") from last_exc


# ---- Real-vs-stub validation ---------------------------------------------------

async def _validate_url(
    client: httpx.AsyncClient,
    url: str,
    semaphore: asyncio.Semaphore,
) -> bool:
    async with semaphore:
        try:
            resp = await client.get(url, timeout=HTTP_TIMEOUT)
            resp.raise_for_status()
            text = resp.text
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            logger.warning("Validation request failed for %s: %s", url, e)
            return False

        if len(text) < REAL_LLMS_MIN_BYTES:
            logger.info("Dropping stub (size=%d): %s", len(text), url)
            return False
        first_line = text.split("\n", 1)[0]
        if REAL_TITLE_MARKER not in first_line:
            logger.info("Dropping stub (title=%r): %s", first_line[:80], url)
            return False
        return True


async def filter_real_sources(
    client: httpx.AsyncClient, sources: list[dict]
) -> list[dict]:
    """Validate each unique LLMS URL once, then keep all entries whose URL is real."""
    unique_urls = {s["llms_txt"] for s in sources}
    semaphore = asyncio.Semaphore(VALIDATION_CONCURRENCY)
    tasks = {
        url: asyncio.create_task(_validate_url(client, url, semaphore))
        for url in unique_urls
    }
    results = {url: await task for url, task in tasks.items()}
    return [s for s in sources if results.get(s["llms_txt"], False)]


# ---- Snapshot persistence ------------------------------------------------------

def save_snapshot(sources: list[dict]) -> None:
    payload = {
        "fetched_at": datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "sources": sources,
    }
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = SNAPSHOT_PATH.with_suffix(SNAPSHOT_PATH.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2))
    os.replace(tmp, SNAPSHOT_PATH)
    logger.info(
        "Wrote snapshot with %d sources to %s", len(sources), SNAPSHOT_PATH
    )


def load_snapshot() -> list[dict]:
    if not SNAPSHOT_PATH.exists():
        return []
    try:
        payload = json.loads(SNAPSHOT_PATH.read_text())
        return payload.get("sources", [])
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Failed to load snapshot at %s: %s", SNAPSHOT_PATH, e)
        return []


# ---- Orchestrator --------------------------------------------------------------

async def _discover_async() -> list[dict]:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        text = await fetch_root_llms_txt(client)
        parsed = parse_doc_sources(text)
        logger.info(
            "Parsed %d candidate sources from %s", len(parsed), ROOT_LLMS_URL
        )
        validated = await filter_real_sources(client, parsed)
        logger.info(
            "Validated %d/%d sources as real", len(validated), len(parsed)
        )
        return validated


def load_dynamic_doc_sources() -> list[dict]:
    """Try live discovery; on hard failure fall back to the last snapshot.

    Never raises. Returns [] if both live discovery and snapshot loading fail.
    Each entry is the enriched form: {name, llms_txt, description, category, title}.
    """
    try:
        sources = asyncio.run(_discover_async())
        if not sources:
            raise RuntimeError("Live discovery returned 0 sources")
        save_snapshot(sources)
        return sources
    except Exception as e:
        logger.warning(
            "Dynamic discovery failed: %s. Falling back to snapshot.", e
        )
        snapshot = load_snapshot()
        if snapshot:
            logger.info(
                "Loaded %d sources from snapshot at %s",
                len(snapshot),
                SNAPSHOT_PATH,
            )
            return snapshot
        logger.error(
            "No snapshot available; v2 docs MCP will boot with empty source list"
        )
        return []


# ---- Server build --------------------------------------------------------------

_DOCSOURCE_KEYS = ("name", "llms_txt", "description")

# Appended to the static `instructions` from juspay_docs_mcp.tools when building
# the v2 server. This OVERRIDES the "STOP — gather merchant_id, integration_type,
# platform before using any documentation tool" directive from the static block,
# which is biased toward SDK-integration questions and pulls the LLM into the
# wrong flow for cross-cutting topics like outages, dashboard, refunds, etc.
V2_ROUTING_OVERRIDE = """

================================================================================
## v2 ROUTING OVERRIDE — APPLIES TO THIS SERVER ONLY

This server exposes THREE tools, not two. Read this section carefully — it
modifies the "STOP — gather merchant_id, integration_type, platform" rule
stated earlier.

### Tools available
1. `list_doc_sources` — use when the user is integrating a specific Juspay SDK
   (Payment Page, Express Checkout / Headless, UPI TPAP, UPI Plugin) or a
   direct S2S API integration. Gates the catalog by integration_type and
   auth_type. Requires merchant_id, client_id, platform.
2. `browse_doc_sources` — use for cross-cutting feature, product, or
   operational questions that are NOT tied to one SDK integration. Takes no
   required arguments. An optional `category` filter is available.
3. `fetch_docs` — call AFTER picking a URL from one of the listing tools.

### Routing rule (apply BEFORE asking the user anything)

- The "gather merchant_id / integration_type / platform" preamble applies
  ONLY to SDK-integration questions. For feature / topic questions, those
  fields are irrelevant and you must NOT ask for them.

- If the question is about a specific SDK integration:
    → ask for merchant_id, integration_type, platform (and ec_flow /
      auth_type / issuing_psp as the integration_type requires).
    → call `list_doc_sources`.

- If the question is about a Juspay feature, product, or operational topic
  that is not anchored to a particular SDK:
    → call `browse_doc_sources` DIRECTLY. No preamble questions.
    → examples of feature/topic questions: outages, dashboard, refunds,
      payouts, EMI, payment links, split settlements, billing, mandates,
      gateway downtime, surcharge, smart converter, dynamic routing,
      tokenization, error codes, release notes, test resources.

- If you genuinely cannot classify the question, ask ONE clarifying
  question: "Is this about a specific SDK integration you're building, or
  about the feature in general?" Then branch.

### Worked examples
- "What are outages?"                → feature → `browse_doc_sources()`. Do not
                                       ask for merchant_id.
- "Tell me about the dashboard"      → feature → `browse_doc_sources(category="DASHBOARD")`.
- "How do refunds work?"             → feature → `browse_doc_sources()`.
- "How do I integrate Payment Page   → SDK    → ask for context → `list_doc_sources`.
   on Android?"
- "How do I trigger refunds in       → SDK    → ask for context → `list_doc_sources`.
   Express Checkout on iOS?"           (anchored to EC iOS)
- "What payment methods does Juspay  → unsure → ask one clarifying question.
   support?"

After the listing tool returns, pick the most relevant URL and call
`fetch_docs(url)`. The response is the product `llms.txt` index — follow the
`.md content link:` URLs inside it with further `fetch_docs` calls to read
specific pages.
================================================================================
"""


def _to_doc_source(entry: dict) -> DocSource:
    """Strip enrichment fields so the entry conforms to mcpdoc.main.DocSource."""
    return {k: entry[k] for k in _DOCSOURCE_KEYS if k in entry}  # type: ignore[return-value]


def _register_browse_tool(mcp, enriched_sources: list[dict]) -> None:
    """Attach `browse_doc_sources` to the v2 FastMCP server.

    Captures `enriched_sources` by closure so the tool sees category/title
    metadata that `create_server` doesn't know about.
    """
    categories = sorted(
        {s["category"] for s in enriched_sources if s.get("category")}
    )
    cat_hint = ", ".join(categories) if categories else "(none discovered)"

    @mcp.tool()
    def browse_doc_sources(
        category: Annotated[
            Optional[str],
            Field(
                description=(
                    "Optional category filter (case-insensitive). When omitted, "
                    "every doc source is returned. Available categories: "
                    f"{cat_hint}."
                ),
            ),
        ] = None,
    ) -> str:
        """
        Browse the full Juspay documentation catalog without requiring merchant
        context.

        Use this for cross-cutting topics that aren't tied to a specific SDK
        integration — outages, dashboard, refunds, payment links, EMI, payouts,
        billing, settlement, etc.

        Use `list_doc_sources` instead when the user is integrating a specific
        SDK (Payment Page, Express Checkout, UPI TPAP, UPI Plugin) — that tool
        gates the response by integration_type and auth_type, and is the right
        choice when merchant context (clientId, merchantId) is relevant.

        Args:
            category: Optional category filter. If provided, only entries whose
                category matches (case-insensitive) are returned. Valid values
                are surfaced in the parameter description.

        Returns:
            A formatted catalog. Each entry has Name, Category, URL, and a
            short Description on separate lines.
        """
        if category:
            cat_lower = category.lower()
            matched = [
                s
                for s in enriched_sources
                if (s.get("category") or "").lower() == cat_lower
            ]
            if not matched:
                return (
                    f"No doc sources match category {category!r}. "
                    f"Available categories: {cat_hint}."
                )
        else:
            matched = enriched_sources

        lines = [
            f"Available documentation sources ({len(matched)} entries):",
            "",
        ]
        for s in matched:
            cat = s.get("category") or "—"
            title = s.get("title") or s["name"].split("\n", 1)[0].replace(
                "Name: ", ""
            )
            lines.append(f"Name: {title}")
            lines.append(f"Category: {cat}")
            lines.append(f"URL: {s['llms_txt']}")
            desc = s.get("description")
            if desc:
                lines.append(f"Description: {desc}")
            lines.append("")
        return "\n".join(lines)


def build_app():
    """Build the v2 docs MCP server with dynamically-discovered sources.

    Returns the underlying mcp.server.Server (FastMCP._mcp_server) so it can be
    plugged into main.py's existing SSE / Streamable HTTP wiring.
    """
    # Imported here (not at module top) to avoid pulling in static doc_sources
    # parsing if `dynamic` is imported but build_app() is never called.
    from juspay_docs_mcp.tools import instructions as static_instructions
    from juspay_docs_mcp.tools import transcripts_map

    enriched = load_dynamic_doc_sources()
    doc_sources = [_to_doc_source(s) for s in enriched]

    # Static instructions are biased toward the v1 SDK flow. Append a v2
    # routing override so the LLM correctly chooses browse_doc_sources for
    # cross-cutting questions instead of demanding merchant context.
    server_instructions = "\n".join(static_instructions) + V2_ROUTING_OVERRIDE

    mcp = create_server(
        doc_sources,
        follow_redirects=True,
        timeout=30.0,
        transcripts_map=transcripts_map,
        server_instructions=server_instructions,
    )

    # v2-only addition: a no-args browse tool for catalog discovery.
    _register_browse_tool(mcp, enriched)

    return mcp._mcp_server


# ---- Set request credentials (for parity with juspay_docs_mcp.tools) ----------

# Reused by main.py's per-request middleware. We import-and-re-export rather
# than duplicating the ContextVar so v2 shares state with the existing docs MCP.
from juspay_docs_mcp.tools import set_juspay_request_credentials  # noqa: E402,F401


# ---- CLI smoke test ------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    discovered = load_dynamic_doc_sources()
    print(f"\nDiscovered {len(discovered)} sources:\n")
    cats: dict[str, int] = {}
    for s in discovered:
        cat = s.get("category") or "—"
        cats[cat] = cats.get(cat, 0) + 1
        title = s.get("title") or s["llms_txt"]
        print(f"  [{cat}] {title} -> {s['llms_txt']}")
    print("\nCategory breakdown:")
    for c, n in sorted(cats.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {n:>3}  {c}")
    print(f"\nSnapshot path: {SNAPSHOT_PATH}")
