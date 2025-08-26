# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from juspay_dashboard_mcp.api.utils import post, get_juspay_host_from_api

async def list_surcharge_rules_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Returns a list of all configured surcharge rules, including their current status and rule definitions.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/rule/list

    The call uses no request body.

    Headers include:
        - x-tenant-id from environment variable
        - content-type: application/json

    Returns:
        dict: The parsed JSON response from the Juspay List Surcharge Rules API.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    api_url = f"{host}/api/ec/v1/rule/list"
    return await post(api_url, {}, None, meta_info)
