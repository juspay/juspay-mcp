# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from juspay_dashboard_mcp.api.utils import post, get_juspay_host_from_api

async def get_conflict_settings_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves conflict settings configuration.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/conflict

    The call uses an empty request body.

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json

    Args:
        payload (dict): No specific parameters required.

    Returns:
        dict: The parsed JSON response containing conflict settings.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    api_url = f"{host}/api/ec/v1/conflict"
    return await post(api_url, {}, None, meta_info)

async def get_general_settings_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves general configuration settings.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/general

    The call uses an empty request body.

    Headers include:
        - x-tenant-id from payload     
        - content-type: application/json

    Args:
        payload (dict): No specific parameters required.

    Returns:
        dict: The parsed JSON response containing general merchant settings.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    api_url = f"{host}/api/ec/v1/general"
    return await post(api_url, {}, None, meta_info)

async def get_mandate_settings_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves mandate-related settings.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/mandate

    The call can include optional JSON data:
        - merchantId: Optional merchant ID

    Headers include:
        - x-tenant-id from payload       
        - content-type: application/json

    Args:
        payload (dict): May include:
            - merchantId: Optional merchant ID to retrieve mandate settings for.

    Returns:
        dict: The parsed JSON response containing mandate settings.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    api_url = f"{host}/api/ec/v1/mandate"
    
    request_data = {}
    if payload.get("merchantId"):
        request_data["merchantId"] = payload["merchantId"]
        
    return await post(api_url, request_data, None, meta_info)

async def get_priority_logic_settings_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Fetches a list of all configured priority logic rules, including their current 
    status and full logic definition. Returns only the latest 2 logics to avoid
    overwhelming the context.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/priorityLogic

    The call uses an empty request body.

    Headers include:
        - x-tenant-id from payload    
        - content-type: application/json

    Args:
        payload (dict): No specific parameters required.

    Returns:
        dict: The parsed JSON response from the Juspay Priority Logic Settings API
              with only the latest 2 logics included (or fewer if less than 2 exist).

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    api_url = f"{host}/api/ec/v1/priorityLogic"
    response = await post(api_url, {}, None, meta_info)
    
    if isinstance(response, dict) and "logics" in response and isinstance(response["logics"], list):
        sorted_logics = sorted(
            response["logics"], 
            key=lambda x: x.get("lastUpdated", ""), 
            reverse=True
        )
        response["logics"] = sorted_logics[:2]
    return response

async def get_routing_settings_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Provides details of success rate–based routing thresholds defined by the merchant, 
    including enablement status and downtime-based switching thresholds.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/routing

    The call uses an empty request body.

    Headers include:
        - x-tenant-id from payload        
        - content-type: application/json

    Args:
        payload (dict): No specific parameters required.

    Returns:
        dict: The parsed JSON response from the Juspay Routing Settings API.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    api_url = f"{host}/api/ec/v1/routing"
    return await post(api_url, {}, None, meta_info)

async def get_webhook_settings_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves webhook configuration settings.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/webhook

    The call uses an empty request body.

    Headers include:
        - x-tenant-id from payload     
        - content-type: application/json

    Args:
        payload (dict): No specific parameters required.

    Returns:
        dict: The parsed JSON response containing webhook settings.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    api_url = f"{host}/api/ec/v1/webhook"
    return await post(api_url, {}, None, meta_info)
