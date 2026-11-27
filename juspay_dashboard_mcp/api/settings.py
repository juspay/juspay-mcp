# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from juspay_dashboard_mcp.api.utils import post, get_juspay_host_from_api, resolve_merchant_id, mask_fields, paginate_response

# Substrings (matched case-insensitively against each key), see mask_fields.
GENERAL_SETTINGS_SECRET_KEYS = {
    "password",
    "secret",
    "token",
    "apikey",
    "api_key",
    "hashkey",
    "encodingkey",
    "signaturekey",
    "privatekey",
    "webhookusername",
    "authorization",
}

async def get_conflict_settings(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves conflict settings configuration.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/conflict

    Headers include:
        - content-type: application/json

    Args:
        payload (dict): May include:

    Returns:
        dict: The parsed JSON response containing conflict settings.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    
    # Build request data
    request_data = {}
    
    api_url = f"{host}/api/ec/v1/conflict"
    
    return await post(api_url, request_data, None, meta_info)

async def get_general_settings(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves general configuration settings.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/general

    Headers include:
        - content-type: application/json

    Args:
        payload (dict): May include:

    Returns:
        dict: The parsed JSON response containing general merchant settings.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    
    # Build request data
    request_data = {}
    
    api_url = f"{host}/api/ec/v1/general"
    
    response = await post(api_url, request_data, None, meta_info)
    return mask_fields(response, GENERAL_SETTINGS_SECRET_KEYS)

async def get_mandate_settings(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves mandate-related settings.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/mandate

    The call can include optional JSON data:
        - merchantId: Optional merchant ID

    Headers include:
        - content-type: application/json

    Args:
        payload (dict): May include:

    Returns:
        dict: The parsed JSON response containing mandate settings.

    Raises:
        ValueError: If a caller tries to access another merchant's data.
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    
    
    merchant_id = resolve_merchant_id(payload.get("merchantId"), "You are not authorized to access mandate settings for this merchantId")
    
    # Build request data
    request_data = {}
    if payload.get("merchantId"):
        request_data["merchantId"] = merchant_id
    
    api_url = f"{host}/api/ec/v1/mandate"
        
    return await post(api_url, request_data, None, meta_info)

async def get_priority_logic_settings(payload: dict, meta_info: dict = None) -> dict:
    """
    Fetches a list of all configured priority logic rules, including their current 
    status and full logic definition. Returns only the latest 2 logics to avoid
    overwhelming the context.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/priorityLogic

    The call uses an empty request body.

    Headers include:
        - content-type: application/json

    Args:
        payload (dict): May include:

    Returns:
        dict: The parsed JSON response from the Juspay Priority Logic Settings API
              with only the latest 2 logics included (or fewer if less than 2 exist).

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    
    # Build request data
    request_data = {}
    
    api_url = f"{host}/api/ec/v1/priorityLogic"
    
    response = await post(api_url, request_data, None, meta_info)

    if isinstance(response, dict) and "logics" in response and isinstance(response["logics"], list):
        response["logics"] = sorted(
            response["logics"],
            key=lambda x: x.get("lastUpdated", ""),
            reverse=True
        )

    if isinstance(response, dict):
        if not payload.get("include_gateways"):
            response.pop("gateways", None)
        response = paginate_response(response, payload.get("limit", 5), payload.get("offset", 0))
    return response

async def get_routing_settings(payload: dict, meta_info: dict = None) -> dict:
    """
    Provides details of success rate–based routing thresholds defined by the merchant, 
    including enablement status and downtime-based switching thresholds.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/routing

    Headers include:
        - content-type: application/json

    Args:
        payload (dict): May include:

    Returns:
        dict: The parsed JSON response from the Juspay Routing Settings API.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    
    # Build request data
    request_data = {}
    
    api_url = f"{host}/api/ec/v1/routing"
    
    return await post(api_url, request_data, None, meta_info)

async def get_webhook_settings(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves webhook configuration settings.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/webhook

    Headers include:
        - content-type: application/json

    Args:
        payload (dict): May include:

    Returns:
        dict: The parsed JSON response containing webhook settings.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    
    # Build request data
    request_data = {}
    
    api_url = f"{host}/api/ec/v1/webhook"

    response = await post(api_url, request_data, None, meta_info)
    return mask_fields(response, GENERAL_SETTINGS_SECRET_KEYS)
