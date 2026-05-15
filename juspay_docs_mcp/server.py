# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

"""Juspay Docs MCP - server with three tools backed by dynamic discovery.

Tools:
  - list_products(category?)  Browse the discovered product catalog.
  - explore_product(product)  Fetch one product's llms.txt by slug.
  - doc_fetch_tool(url)       Fetch any allowed Juspay docs URL as markdown.

Discovery runs once at module import; results are persisted to snapshot.json.
"""

import json
import logging
import os
import re
from contextvars import ContextVar
from typing import Annotated, Optional
from urllib.parse import urljoin, urlparse

import httpx
from markdownify import markdownify
from mcp.server.fastmcp import FastMCP
from pydantic import Field

from juspay_docs_mcp.discovery import load_dynamic_doc_sources
from juspay_docs_mcp.instructions import INSTRUCTIONS

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------------
# Per-request credentials (ContextVar populated by middleware in juspay_mcp.main)
# ----------------------------------------------------------------------------

juspay_request_credentials: ContextVar[Optional[dict]] = ContextVar(
    "juspay_request_credentials", default=None
)


def set_juspay_request_credentials(credentials):
    """Set Juspay credentials for the current request context."""
    juspay_request_credentials.set(credentials)


def get_juspay_request_credentials():
    """Get Juspay credentials from current request context."""
    return juspay_request_credentials.get()


# ----------------------------------------------------------------------------
# Transcripts (curated commentary appended to specific URLs in doc_fetch_tool)
# ----------------------------------------------------------------------------

def _load_transcripts() -> dict:
    path = os.path.join(os.path.dirname(__file__), "transcripts.json")
    try:
        with open(path, "r") as f:
            return {str(k): str(v) for k, v in json.load(f).items()}
    except FileNotFoundError:
        logger.info("No transcripts.json at %s; running without transcripts", path)
        return {}
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse transcripts.json: %s", e)
        return {}


_TRANSCRIPTS_MAP = _load_transcripts()


# ----------------------------------------------------------------------------
# Catalog (loaded once at module import via discovery)
# ----------------------------------------------------------------------------

_ENRICHED_SOURCES: list[dict] = load_dynamic_doc_sources()


def _slug_for(entry: dict) -> Optional[str]:
    """Return the canonical slug for a catalog entry.

    Prefers the parsed `id` field from the root llms.txt. Falls back to
    URL-path parsing for older snapshots that pre-date the `id` capture.
    """
    if entry.get("id"):
        return entry["id"]
    parsed = urlparse(entry["llms_txt"])
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) >= 2 and parts[-1] == "llms.txt":
        return parts[-2]
    return None


_SLUG_INDEX: dict[str, dict] = {}
for _entry in _ENRICHED_SOURCES:
    _slug = _slug_for(_entry)
    if _slug:
        _SLUG_INDEX[_slug] = _entry

_DOMAINS: set[str] = set()
for _entry in _ENRICHED_SOURCES:
    _parsed = urlparse(_entry["llms_txt"])
    if _parsed.scheme and _parsed.netloc:
        _DOMAINS.add(f"{_parsed.scheme}://{_parsed.netloc}/")

_CATEGORIES: list[str] = sorted({
    s["category"] for s in _ENRICHED_SOURCES if s.get("category")
})
_CAT_HINT: str = ", ".join(_CATEGORIES) if _CATEGORIES else "(none discovered)"

logger.info(
    "Docs MCP initialized: %d products across %d categories, %d allowed domains",
    len(_ENRICHED_SOURCES),
    len(_CATEGORIES),
    len(_DOMAINS),
)


# ----------------------------------------------------------------------------
# HTTP client (shared across tools)
# ----------------------------------------------------------------------------

_HTTPX = httpx.AsyncClient(
    follow_redirects=True,
    timeout=30.0,
    headers={"User-Agent": "juspay-docs-mcp"},
)


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

_META_REFRESH_RE = re.compile(
    r'<meta http-equiv="refresh" content="[^;]+;\s*url=([^"]+)"',
    re.IGNORECASE,
)


def _url_allowed(url: str) -> bool:
    return any(url.startswith(d) for d in _DOMAINS)


async def _fetch_with_processing(url: str) -> str:
    """Fetch URL, follow meta-refresh once, inject transcript, markdownify."""
    try:
        response = await _HTTPX.get(url)
        response.raise_for_status()
        content = response.text

        m = _META_REFRESH_RE.search(content)
        if m:
            new_url = urljoin(str(response.url), m.group(1))
            if not _url_allowed(new_url):
                return (
                    f"Error: redirect URL not allowed. "
                    f"Allowed domains: {', '.join(sorted(_DOMAINS))}"
                )
            response = await _HTTPX.get(new_url)
            response.raise_for_status()
            content = response.text

        if url in _TRANSCRIPTS_MAP:
            content = content + "\n\n---\n\n" + _TRANSCRIPTS_MAP[url]

        return markdownify(content)
    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        return f"Encountered an HTTP error: {e}"


# ----------------------------------------------------------------------------
# MCP server + tools
# ----------------------------------------------------------------------------

mcp = FastMCP(name="juspay-docs", instructions=INSTRUCTIONS)


@mcp.tool()
def list_products(
    category: Annotated[
        Optional[str],
        Field(
            description=(
                "Optional category filter (case-insensitive). When omitted, "
                f"all {len(_ENRICHED_SOURCES)} products are returned. "
                f"Available categories: {_CAT_HINT}."
            ),
        ),
    ] = None,
) -> str:
    """Browse the Juspay product catalog.

    Use this first to discover which Juspay product is relevant to the
    user's question. Returns title, slug, category, URL, and a short
    description for each product. Optionally filter by category (e.g.
    'CHECKOUT', 'BILLING', 'DASHBOARD').

    After choosing a product, call explore_product(slug) to fetch its
    llms.txt index.
    """
    if category:
        cat_lower = category.lower()
        matched = [
            s for s in _ENRICHED_SOURCES
            if (s.get("category") or "").lower() == cat_lower
        ]
        if not matched:
            return (
                f"No products match category {category!r}. "
                f"Available categories: {_CAT_HINT}."
            )
    else:
        matched = _ENRICHED_SOURCES

    if not matched:
        return (
            "No products available - catalog is empty. This usually means "
            "discovery failed at startup and no snapshot was on disk. "
            "Check server logs."
        )

    lines = [
        f"Available products ({len(matched)} of {len(_ENRICHED_SOURCES)}):",
        "",
    ]
    for s in matched:
        slug = _slug_for(s) or "-"
        cat = s.get("category") or "-"
        title = s.get("title") or s["name"].split("\n", 1)[0].replace("Name: ", "")
        lines.append(f"Slug: {slug}")
        lines.append(f"Title: {title}")
        lines.append(f"Category: {cat}")
        lines.append(f"URL: {s['llms_txt']}")
        desc = s.get("description")
        if desc:
            lines.append(f"Description: {desc}")
        lines.append("")
    return "\n".join(lines)


@mcp.tool()
async def explore_product(
    product: Annotated[
        str,
        Field(
            description=(
                "Product slug (e.g. 'hyper-checkout', 'ec-headless'). "
                "Use list_products() to see available slugs."
            ),
        ),
    ],
) -> str:
    """Fetch the llms.txt index for a specific Juspay product.

    Looks up the product slug in the discovered catalog and returns its
    documentation index as markdown. The index contains .md content links
    that you can read via doc_fetch_tool(url).

    Returns an error if the slug isn't in the catalog - call list_products()
    to see valid slugs.
    """
    entry = _SLUG_INDEX.get(product)
    if entry is None:
        sample = ", ".join(sorted(_SLUG_INDEX.keys())[:10])
        more = (
            f" (and {len(_SLUG_INDEX) - 10} more)"
            if len(_SLUG_INDEX) > 10 else ""
        )
        return (
            f"Product slug {product!r} not found in catalog. "
            f"Call list_products() to see all slugs. "
            f"Examples: {sample}{more}."
        )
    return await _fetch_with_processing(entry["llms_txt"])


@mcp.tool()
async def doc_fetch_tool(
    url: Annotated[
        str,
        Field(
            description=(
                "URL to fetch. Must be on an allowed domain (auto-derived "
                "from the discovered product catalog, typically juspay.io)."
            ),
        ),
    ],
) -> str:
    """Fetch any allowed Juspay docs URL as markdown.

    Use this after explore_product() to read specific pages by URL.
    Follows meta-refresh redirects once. Returns markdown-converted
    content. Returns an error if the URL is on a disallowed domain.
    """
    url = url.strip()
    if not _url_allowed(url):
        return (
            f"Error: URL not allowed. Must start with one of: "
            f"{', '.join(sorted(_DOMAINS))}"
        )
    return await _fetch_with_processing(url)


# Export the underlying low-level Server for main.py / stdio.py
app = mcp._mcp_server
