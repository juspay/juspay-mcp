# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import logging
import os

import httpx

from juspay_ai_studio_mcp.api.utils import get_ai_studio_credentials
from juspay_ai_studio_mcp.config import JUSPAY_BASE_URL

logger = logging.getLogger(__name__)

_AUTHORIZE_QUERY = "resource={%22COMMON%22%20%3A%20%22R%22}"


def _token_from_credentials(juspay_creds: dict | None) -> str | None:
    if not juspay_creds:
        return None
    return (
        juspay_creds.get("ai_studio_token")
        or juspay_creds.get("dashboard_token")
        or juspay_creds.get("api_key")
    )


async def get_merchant_details_ai_studio(payload: dict = None, meta_info: dict = None) -> dict:
    """Return merchant and user session details for the authenticated AI Studio caller."""
    juspay_creds = get_ai_studio_credentials()
    token = _token_from_credentials(juspay_creds)
    if not token and meta_info:
        token = meta_info.get("x-web-logintoken") or meta_info.get("ai_studio_token")
    if not token:
        token = os.environ.get("JUSPAY_AI_STUDIO_TOKEN") or os.environ.get("JUSPAY_WEB_LOGIN_TOKEN")
    if not token:
        raise Exception("Juspay AI Studio token not provided.")

    url = f"{JUSPAY_BASE_URL}/ec/v2/authorize?{_AUTHORIZE_QUERY}"
    headers = {"Authorization": token}

    async with httpx.AsyncClient(timeout=10.0) as client:
        logger.info(f"GET {url}")
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()

