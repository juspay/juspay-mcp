# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from juspay_dashboard_mcp.api.utils import post, get_admin_host, get_juspay_host_from_api, sanitize_merchant_id

async def get_conflict_settings_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves conflict settings configuration.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/conflict (for non-admin users)
        https://portal.juspay.in/ec/v1/admin/conflict (for admin users)

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json

    Args:
        payload (dict): May include:
            - merchantId: Optional merchant ID (admin only).

    Returns:
        dict: The parsed JSON response containing conflict settings.

    Raises:
        ValueError: If non-admin user tries to access another merchant's data.
        Exception: If the API call fails.
    """
    host, isadmin = await get_admin_host(meta_info=meta_info)
    
    # Get merchantId from meta_info for authorization check
    mid_from_meta = None
    if meta_info:
        token_response = meta_info.get("token_response", {})
        mid_from_meta = token_response.get("merchantId") or meta_info.get("merchantId")
    
    # Authorization check - non-admin can't query other merchants
    if not isadmin and payload.get("merchantId") and mid_from_meta and payload.get("merchantId") != mid_from_meta:
        raise ValueError("You are not authorized to access conflict settings for this merchantId")
    
    # Build request data
    request_data = {}
    if isadmin:
        merchant_id = sanitize_merchant_id(payload.get("merchantId"), mid_from_meta)
        if merchant_id:
            request_data["merchantId"] = merchant_id
    
    # Conditional URL based on admin status
    if isadmin:
        api_url = f"{host}/ec/v1/admin/conflict"
    else:
        api_url = f"{host}/api/ec/v1/conflict"
    
    return await post(api_url, request_data, None, meta_info)

async def get_general_settings_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves general configuration settings.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/general (for non-admin users)
        https://portal.juspay.in/ec/v1/admin/general (for admin users)

    Headers include:
        - x-tenant-id from payload     
        - content-type: application/json

    Args:
        payload (dict): May include:
            - merchantId: Optional merchant ID (admin only).

    Returns:
        dict: The parsed JSON response containing general merchant settings.

    Raises:
        ValueError: If non-admin user tries to access another merchant's data.
        Exception: If the API call fails.
    """
    host, isadmin = await get_admin_host(meta_info=meta_info)
    
    # Get merchantId from meta_info for authorization check
    mid_from_meta = None
    if meta_info:
        token_response = meta_info.get("token_response", {})
        mid_from_meta = token_response.get("merchantId") or meta_info.get("merchantId")
    
    # Authorization check - non-admin can't query other merchants
    if not isadmin and payload.get("merchantId") and mid_from_meta and payload.get("merchantId") != mid_from_meta:
        raise ValueError("You are not authorized to access general settings for this merchantId")
    
    # Build request data
    request_data = {}
    if isadmin:
        merchant_id = sanitize_merchant_id(payload.get("merchantId"), mid_from_meta)
        if merchant_id:
            request_data["merchantId"] = merchant_id
    
    # Conditional URL based on admin status
    if isadmin:
        api_url = f"{host}/ec/v1/admin/general"
    else:
        api_url = f"{host}/api/ec/v1/general"
    
    return await post(api_url, request_data, None, meta_info)

async def get_mandate_settings_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves mandate-related settings.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/mandate (for non-admin users)
        https://portal.juspay.in/ec/v1/admin/mandate (for admin users)

    The call can include optional JSON data:
        - merchantId: Optional merchant ID

    Headers include:
        - x-tenant-id from payload       
        - content-type: application/json

    Args:
        payload (dict): May include:
            - merchantId: Optional merchant ID to retrieve mandate settings for (admin only).

    Returns:
        dict: The parsed JSON response containing mandate settings.

    Raises:
        ValueError: If non-admin user tries to access another merchant's data.
        Exception: If the API call fails.
    """
    host, isadmin = await get_admin_host(meta_info=meta_info)
    
    # Get merchantId from meta_info for authorization check
    mid_from_meta = None
    if meta_info:
        token_response = meta_info.get("token_response", {})
        mid_from_meta = token_response.get("merchantId") or meta_info.get("merchantId")
    
    # Authorization check - non-admin can't query other merchants
    if not isadmin and payload.get("merchantId") and mid_from_meta and payload.get("merchantId") != mid_from_meta:
        raise ValueError("You are not authorized to access mandate settings for this merchantId")
    
    # Build request data
    request_data = {}
    if isadmin:
        merchant_id = sanitize_merchant_id(payload.get("merchantId"), mid_from_meta)
        if merchant_id:
            request_data["merchantId"] = merchant_id
    elif payload.get("merchantId"):
        request_data["merchantId"] = sanitize_merchant_id(payload.get("merchantId"), mid_from_meta)
    
    # Conditional URL based on admin status
    if isadmin:
        api_url = f"{host}/ec/v1/admin/mandate"
    else:
        api_url = f"{host}/api/ec/v1/mandate"
        
    return await post(api_url, request_data, None, meta_info)

async def get_priority_logic_settings_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Fetches a list of all configured priority logic rules, including their current 
    status and full logic definition. Returns only the latest 2 logics to avoid
    overwhelming the context.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/priorityLogic (for non-admin users)
        https://portal.juspay.in/ec/v1/admin/priorityLogic (for admin users)

    The call uses an empty request body.

    Headers include:
        - x-tenant-id from payload    
        - content-type: application/json

    Args:
        payload (dict): May include:
            - merchantId: Optional merchant ID (admin only).

    Returns:
        dict: The parsed JSON response from the Juspay Priority Logic Settings API
              with only the latest 2 logics included (or fewer if less than 2 exist).

    Raises:
        ValueError: If non-admin user tries to access another merchant's data.
        Exception: If the API call fails.
    """
    host, isadmin = await get_admin_host(meta_info=meta_info)
    
    # Get merchantId from meta_info for authorization check
    mid_from_meta = None
    if meta_info:
        token_response = meta_info.get("token_response", {})
        mid_from_meta = token_response.get("merchantId") or meta_info.get("merchantId")
    
    # Authorization check - non-admin can't query other merchants
    if not isadmin and payload.get("merchantId") and mid_from_meta and payload.get("merchantId") != mid_from_meta:
        raise ValueError("You are not authorized to access priority logic settings for this merchantId")
    
    # Build request data
    request_data = {}
    if isadmin:
        merchant_id = sanitize_merchant_id(payload.get("merchantId"), mid_from_meta)
        if merchant_id:
            request_data["merchantId"] = merchant_id
    
    # Conditional URL based on admin status
    if isadmin:
        api_url = f"{host}/ec/v1/admin/priorityLogic"
    else:
        api_url = f"{host}/api/ec/v1/priorityLogic"
    
    response = await post(api_url, request_data, None, meta_info)
    
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
        https://portal.juspay.in/api/ec/v1/routing (for non-admin users)
        https://portal.juspay.in/ec/v1/admin/routing (for admin users)

    Headers include:
        - x-tenant-id from payload        
        - content-type: application/json

    Args:
        payload (dict): May include:
            - merchantId: Optional merchant ID (admin only).

    Returns:
        dict: The parsed JSON response from the Juspay Routing Settings API.

    Raises:
        ValueError: If non-admin user tries to access another merchant's data.
        Exception: If the API call fails.
    """
    host, isadmin = await get_admin_host(meta_info=meta_info)
    
    # Get merchantId from meta_info for authorization check
    mid_from_meta = None
    if meta_info:
        token_response = meta_info.get("token_response", {})
        mid_from_meta = token_response.get("merchantId") or meta_info.get("merchantId")
    
    # Authorization check - non-admin can't query other merchants
    if not isadmin and payload.get("merchantId") and mid_from_meta and payload.get("merchantId") != mid_from_meta:
        raise ValueError("You are not authorized to access routing settings for this merchantId")
    
    # Build request data
    request_data = {}
    if isadmin:
        merchant_id = sanitize_merchant_id(payload.get("merchantId"), mid_from_meta)
        if merchant_id:
            request_data["merchantId"] = merchant_id
    
    # Conditional URL based on admin status
    if isadmin:
        api_url = f"{host}/ec/v1/admin/routing"
    else:
        api_url = f"{host}/api/ec/v1/routing"
    
    return await post(api_url, request_data, None, meta_info)

async def get_webhook_settings_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves webhook configuration settings.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/webhook (for non-admin users)
        https://portal.juspay.in/ec/v1/admin/webhook (for admin users)

    Headers include:
        - x-tenant-id from payload     
        - content-type: application/json

    Args:
        payload (dict): May include:
            - merchantId: Optional merchant ID (admin only).

    Returns:
        dict: The parsed JSON response containing webhook settings.

    Raises:
        ValueError: If non-admin user tries to access another merchant's data.
        Exception: If the API call fails.
    """
    host, isadmin = await get_admin_host(meta_info=meta_info)
    
    # Get merchantId from meta_info for authorization check
    mid_from_meta = None
    if meta_info:
        token_response = meta_info.get("token_response", {})
        mid_from_meta = token_response.get("merchantId") or meta_info.get("merchantId")
    
    # Authorization check - non-admin can't query other merchants
    if not isadmin and payload.get("merchantId") and mid_from_meta and payload.get("merchantId") != mid_from_meta:
        raise ValueError("You are not authorized to access webhook settings for this merchantId")
    
    # Build request data
    request_data = {}
    if isadmin:
        merchant_id = sanitize_merchant_id(payload.get("merchantId"), mid_from_meta)
        if merchant_id:
            request_data["merchantId"] = merchant_id
    
    # Conditional URL based on admin status
    if isadmin:
        api_url = f"{host}/ec/v1/admin/webhook"
    else:
        api_url = f"{host}/api/ec/v1/webhook"
    
    return await post(api_url, request_data, None, meta_info)
