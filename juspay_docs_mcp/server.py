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

import logging
import time
from typing import Annotated, Any, Literal, Optional
from urllib.parse import urlparse

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import Field

from juspay_mcp.analytics import record_stage_status, record_tool_call
from juspay_docs_mcp.discovery import load_dynamic_doc_sources
from juspay_docs_mcp.genius import ask_genius
from juspay_docs_mcp.instructions import INSTRUCTIONS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Static domain allowlist
# ---------------------------------------------------------------------------

_ALLOWED_SUFFIXES = (".juspay.io", ".juspay.in")
_ALLOWED_EXACT = frozenset({"juspay.io", "juspay.in", "dth95m2xtyv8v.cloudfront.net"})
_ALLOWED_SCHEMES = frozenset({"http", "https"})
_ALLOWED_DOMAINS_DISPLAY = "*.juspay.io, *.juspay.in, dth95m2xtyv8v.cloudfront.net"


def _url_allowed(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        return False
    # hostname is lowercased and strips the port.
    host = parsed.hostname or ""
    if host in _ALLOWED_EXACT:
        return True
    return any(host.endswith(s) for s in _ALLOWED_SUFFIXES)


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
    "Docs MCP initialized: %d products across %d categories (allowed: %s)",
    len(_ENRICHED_SOURCES),
    len(_CATEGORIES),
    _ALLOWED_DOMAINS_DISPLAY,
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




async def _fetch(url: str) -> str:
    """Fetch URL and return the raw response text."""
    try:
        response = await _HTTPX.get(url)
        response.raise_for_status()
        return response.text
    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        return f"Encountered an HTTP error: {e}"


# ----------------------------------------------------------------------------
# MCP server + tools
# ----------------------------------------------------------------------------

mcp = FastMCP(name="juspay-docs", instructions=INSTRUCTIONS)


async def _safe_record_tool_call(
    *,
    tool: str,
    status: str,
    started_at: float,
    arguments: dict[str, Any],
    error: str | None = None,
) -> None:
    try:
        await record_tool_call(
            tool=tool,
            status=status,
            started_at=started_at,
            arguments=arguments,
            error=error,
        )
    except Exception:
        logger.exception("Failed to emit docs analytics event for %s", tool)


@mcp.tool()
async def juspay_track_integration_stage(
    phase: Annotated[
        Literal["setup", "prd", "architecture", "backend", "frontend", "validation", "live"],
        Field(
            description=(
                "Integration funnel phase being reported. Use this as the final "
                "action when a phase is completed or otherwise resolved."
            )
        ),
    ],
    status: Annotated[
        Literal["started", "completed", "failed", "skipped"],
        Field(description="Status of the integration phase."),
    ],
    product: Annotated[
        Optional[str],
        Field(description="Selected Juspay product, if known."),
    ] = None,
    platform: Annotated[
        Optional[str],
        Field(description="Selected platform such as web, react-native, android, or ios."),
    ] = None,
    framework: Annotated[
        Optional[str],
        Field(description="Selected application framework, if known."),
    ] = None,
    metadata: Annotated[
        Optional[dict[str, Any]],
        Field(description="Small JSON object with non-sensitive stage metadata."),
    ] = None,
) -> str:
    """Record a merchant integration funnel milestone for analytics.

    This tool is intentionally unauthenticated so docs-only integration journeys
    can still emit milestones. The server joins events to MID later when a
    dashboard-authenticated request appears with the same install id.
    """
    try:
        await record_stage_status(
            phase=phase,
            status=status,
            product=product,
            platform=platform,
            framework=framework,
            metadata=metadata,
        )
    except Exception:
        logger.exception("Failed to record integration stage analytics")
        return "Stage status accepted; analytics write failed."
    return "Stage status recorded."


@mcp.tool()
async def juspay_genius_docs(
    query: Annotated[
        str,
        Field(
            description=(
                "A natural-language question about Juspay (any "
                "product or platform). E.g. 'How do I handle the user pressing "
                "back during a HyperCheckout payment on React Native?'"
            ),
        ),
    ],
) -> str:
    """Ask Juspay Genius - the AI assistant behind the Juspay docs - a
    natural-language question and get a synthesized answer drawn from the
    official documentation.

    Returns the answer plus the source doc URLs it used; any of those can be
    read in full with doc_fetch_tool(url). Genius is the public docs assistant
    (distinct from the dashboard's rag_tool_juspay).
    """
    started_at = time.perf_counter()
    status = "success"
    error = None
    try:
        try:
            result = await ask_genius(query)
        except httpx.TimeoutException as e:
            status = "timeout"
            error = str(e) or "Genius docs request timed out"
            logger.warning("Genius docs call timed out: %s", e)
            return (
                "The Genius docs assistant timed out. "
                "Use list_products / explore_product / doc_fetch_tool to navigate "
                "the docs directly, or retry shortly."
            )
        except httpx.HTTPError as e:
            status = "error"
            error = str(e)
            logger.warning("Genius docs call failed: %s", e)
            return (
                "The Genius docs assistant is unavailable right now. "
                "Use list_products / explore_product / doc_fetch_tool to navigate "
                "the docs directly, or retry shortly."
            )

        answer = result["answer"] or "(no answer returned)"
        sources = result["sources"]
        if sources:
            listed = "\n".join(f"- {s['title']}: {s['url']}" for s in sources)
            return f"{answer}\n\nSources:\n{listed}"
        return answer
    except Exception as e:
        status = "error"
        error = str(e)
        raise
    finally:
        await _safe_record_tool_call(
            tool="juspay_genius_docs",
            status=status,
            started_at=started_at,
            arguments={"query": query},
            error=error,
        )


def _list_products(category: Optional[str] = None) -> str:
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
async def list_products(
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
    started_at = time.perf_counter()
    status = "success"
    error = None
    try:
        return _list_products(category)
    except Exception as e:
        status = "error"
        error = str(e)
        raise
    finally:
        await _safe_record_tool_call(
            tool="list_products",
            status=status,
            started_at=started_at,
            arguments={"category": category},
            error=error,
        )


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

    Looks up the product slug in the catalog and returns the raw llms.txt
    content. The index contains .md content links readable via doc_fetch_tool(url).

    Returns an error if the slug isn't in the catalog — call list_products()
    to see valid slugs.
    """
    started_at = time.perf_counter()
    status = "success"
    error = None
    try:
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
        return await _fetch(entry["llms_txt"])
    except Exception as e:
        status = "error"
        error = str(e)
        raise
    finally:
        await _safe_record_tool_call(
            tool="explore_product",
            status=status,
            started_at=started_at,
            arguments={"product": product},
            error=error,
        )


@mcp.tool()
async def doc_fetch_tool(
    url: Annotated[
        str,
        Field(
            description=(
                f"URL to fetch. Must be on an allowed domain: {_ALLOWED_DOMAINS_DISPLAY}."
            ),
        ),
    ],
) -> str:
    """Fetch any allowed Juspay docs URL and return its raw text content.

    Use this after explore_product() to read specific pages by URL.
    Returns markdown mirror of the URL.
    Returns an error if the URL is on a disallowed domain.
    """
    started_at = time.perf_counter()
    status = "success"
    error = None
    try:
        url = url.strip()
        if not _url_allowed(url):
            return (
                f"Error: URL not on an allowed domain. "
                f"Allowed: {_ALLOWED_DOMAINS_DISPLAY}"
            )
        return await _fetch(url)
    except Exception as e:
        status = "error"
        error = str(e)
        raise
    finally:
        await _safe_record_tool_call(
            tool="doc_fetch_tool",
            status=status,
            started_at=started_at,
            arguments={"url": url},
            error=error,
        )


# Export the underlying low-level Server for main.py / stdio.py
app = mcp._mcp_server
