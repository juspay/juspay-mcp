# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

"""Juspay Docs MCP - dynamic source discovery.

Discovers documentation sources at startup by parsing the root llms.txt at
juspay.io. On success, persists a snapshot. On hard failure, falls back to the
last persisted snapshot (or boots empty).

The shipped snapshot.json acts as a committed default - if discovery fails on
first boot, the server still has a usable catalog. Every successful boot
overwrites the snapshot with fresh data.
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


ROOT_LLMS_URL = os.getenv(
    "JUSPAY_DOCS_ROOT_LLMS_URL",
    "https://juspay.io/in/docs/llms.txt",
)
SNAPSHOT_PATH = Path(
    os.getenv(
        "JUSPAY_DOCS_SNAPSHOT_PATH",
        str(Path(__file__).parent / "snapshot.json"),
    )
)
HTTP_TIMEOUT = float(os.getenv("JUSPAY_DOCS_TIMEOUT", "30"))
ROOT_FETCH_RETRIES = int(os.getenv("JUSPAY_DOCS_RETRIES", "3"))
VALIDATION_CONCURRENCY = int(os.getenv("JUSPAY_DOCS_VALIDATION_CONCURRENCY", "20"))

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

    Each emitted entry:
        {name, llms_txt, description, category, title, id}
    The `id` is the canonical product slug used by server.py for
    explore_product lookups.
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
            entry = {
                "name": f"Name: {title}\n\n{description}",
                "llms_txt": llms,
                "description": description,
                "category": current_block.get("category"),
                "title": title,
            }
            if current_block.get("id"):
                entry["id"] = current_block["id"]
            sources.append(entry)
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
    async with httpx.AsyncClient(
        follow_redirects=True,
        headers={"User-Agent": "juspay-docs-mcp"},
    ) as client:
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
    Each entry: {name, llms_txt, description, category, title, id}.
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
            "No snapshot available; docs MCP will boot with empty source list"
        )
        return []


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
        cat = s.get("category") or "-"
        cats[cat] = cats.get(cat, 0) + 1
        slug = s.get("id") or "-"
        title = s.get("title") or s["llms_txt"]
        print(f"  [{cat}] {slug}: {title} -> {s['llms_txt']}")
    print("\nCategory breakdown:")
    for c, n in sorted(cats.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {n:>3}  {c}")
    print(f"\nSnapshot path: {SNAPSHOT_PATH}")
