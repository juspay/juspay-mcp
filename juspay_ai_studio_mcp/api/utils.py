# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import logging
from contextvars import ContextVar

import httpx

from juspay_ai_studio_mcp.config import PP_AI_STUDIO_BASE_URL, get_common_headers
from juspay_mcp.log_safe import safe_exc, safe_upstream_error, safe_url

logger = logging.getLogger(__name__)

ai_studio_credentials: ContextVar[dict | None] = ContextVar(
    "ai_studio_credentials",
    default=None,
)


def set_ai_studio_credentials(creds: dict | None):
    """Set Juspay credentials for the current AI Studio request context."""
    ai_studio_credentials.set(creds)


def get_ai_studio_credentials() -> dict | None:
    """Get Juspay credentials from the current AI Studio request context."""
    return ai_studio_credentials.get()


def _credentials_from_context(meta_info: dict | None = None) -> dict | None:
    juspay_creds = get_ai_studio_credentials()
    if not juspay_creds and meta_info:
        juspay_creds = meta_info.get("juspay_credentials")
    return juspay_creds


async def request(
    method: str,
    path: str,
    *,
    body: dict | None = None,
    query: dict | None = None,
    header_payload: dict | None = None,
    meta_info: dict | None = None,
    additional_headers: dict | None = None,
    base_url: str = PP_AI_STUDIO_BASE_URL,
) -> dict:
    """Make an authenticated PP Studio AI API request."""
    juspay_creds = _credentials_from_context(meta_info)
    headers = get_common_headers(dict(header_payload or {}), meta_info, juspay_creds)
    if additional_headers:
        headers.update(additional_headers)

    url = path if path.startswith(("http://", "https://")) else f"{base_url.rstrip('/')}{path}"
    method = method.upper()

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info(f"{method} {safe_url(url)}")
            response = await client.request(
                method,
                url,
                headers=headers,
                json=body,
                params=query,
            )
            response.raise_for_status()
            if not response.content:
                return {}
            try:
                return response.json()
            except ValueError:
                return {"text": response.text}
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response else "No response"
            logger.error(f"HTTP error: {status} calling {method} {safe_url(url)}")
            error_content = safe_upstream_error(e.response)
            raise Exception(
                f"PP Studio AI API HTTPError ({status}): {error_content}"
            ) from e
        except Exception as e:
            logger.error(f"Error during PP Studio AI API call: {safe_exc(e)}")
            raise Exception(f"Failed to call PP Studio AI API: {e}") from e
