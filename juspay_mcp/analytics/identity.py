from __future__ import annotations

import logging
import time

import httpx

logger = logging.getLogger(__name__)

_AUTHORIZE_QUERY = "resource={%22COMMON%22%20%3A%20%22R%22}"
_CACHE_TTL_SECONDS = 300
_mid_cache: dict[str, tuple[str | None, float]] = {}


def _normalize_mid(value: object) -> str | None:
    if value is None:
        return None
    mid = str(value).strip()
    return mid or None


def extract_mid(value: object) -> str | None:
    if not isinstance(value, dict):
        return None

    for key in ("merchantId", "merchant_id", "mid"):
        mid = _normalize_mid(value.get(key))
        if mid:
            return mid

    for key in ("merchant", "data", "user", "session"):
        nested = value.get(key)
        if isinstance(nested, dict):
            mid = extract_mid(nested)
            if mid:
                return mid
    return None


async def resolve_mid_from_dashboard_token(
    *,
    token: str | None,
    portal_base_url: str,
) -> str | None:
    if not token:
        return None

    now = time.time()
    cached = _mid_cache.get(token)
    if cached is not None:
        mid, expires_at = cached
        if expires_at > now:
            return mid
        _mid_cache.pop(token, None)

    url = f"{portal_base_url.rstrip('/')}/ec/v2/authorize?{_AUTHORIZE_QUERY}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, headers={"Authorization": token})
            resp.raise_for_status()
            mid = extract_mid(resp.json())
    except Exception as exc:
        logger.warning("Analytics MID resolution failed: %s", exc)
        mid = None

    _mid_cache[token] = (mid, now + _CACHE_TTL_SECONDS)
    return mid
