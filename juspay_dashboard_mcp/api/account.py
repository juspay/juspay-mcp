# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import logging
import os

import httpx

from juspay_dashboard_mcp.api.utils import get_juspay_credentials
from juspay_dashboard_mcp.config import JUSPAY_BASE_URL

logger = logging.getLogger(__name__)

# Portal requires this byte-exact resource query string (literal `{` `}` and
# `%20` for spaces) — same form used by the OAuth validation path.
_AUTHORIZE_QUERY = "resource={%22COMMON%22%20%3A%20%22R%22}"


async def get_merchant_details_juspay(payload: dict = None, meta_info: dict = None) -> dict:
    """Return merchant + user session details for the authenticated caller.

    Calls Portal's authorize endpoint and surfaces the full response so the
    LLM gets merchantId, userId, email, context (MERCHANT/TENANT/RESELLER/
    JUSPAY), username, tenantAccountId, validHost, and any other fields
    Portal exposes for the current session.
    """
    juspay_creds = get_juspay_credentials()
    token = juspay_creds.get("dashboard_token") if juspay_creds else None
    if not token and meta_info:
        token = meta_info.get("x-web-logintoken")
    if not token:
        token = os.environ.get("JUSPAY_WEB_LOGIN_TOKEN")
    if not token:
        raise Exception("Juspay token not provided.")

    url = f"{JUSPAY_BASE_URL}/ec/v2/authorize?{_AUTHORIZE_QUERY}"
    headers = {"Authorization": token}

    async with httpx.AsyncClient(timeout=10.0) as client:
        logger.info(f"GET {url}")
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()
