# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from juspay_dashboard_mcp.api.utils import post, get_juspay_host_from_api


async def create_api_key_juspay(payload: dict, meta_info: dict = None) -> dict:
    """Generate a new API key for the authenticated merchant.

    Accepts a `description` label that identifies the key in the merchant's
    API Keys listing. Returns the full creation response including the
    plaintext `apiKey` (shown only at creation), `maskedApiKey`, `id`,
    `status`, `scope`, `dateCreated`, `lastUpdated`, `merchantAccountId`,
    `version`, and `metadata`.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    request_payload = {"description": payload["description"]}
    api_url = f"{host}/api/ec/v1/apiKeys"
    return await post(api_url, request_payload, None, meta_info)
