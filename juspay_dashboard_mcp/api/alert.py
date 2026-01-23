# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from juspay_dashboard_mcp.api.utils import post, get_admin_host, call , sanitize_merchant_id

async def alert_details_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Provides detailed information for a specific alert ID, including source, monitored metrics, and applied filters.

    The API endpoint is:
        https://portal.juspay.in/api/monitoring/task (for non-admin users)
        https://portal.juspay.in/monitoring/task (for admin users)

    Args:
        payload (dict): Must contain 'task_uid' and 'user_name'.
            - merchantId: Optional merchant ID (admin only).

    Returns:
        dict: The parsed JSON response from the Juspay Alert Details API.

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
        raise ValueError("You are not authorized to access alert details for this merchantId")
    
    # Build URL with query params
    url_params = f"task_uid={payload['task_uid']}&user_name={payload['user_name']}"
    if isadmin:
        merchant_id = sanitize_merchant_id(payload.get("merchantId"), mid_from_meta)
        if merchant_id:
            url_params += f"&merchantId={merchant_id}"
    
    # Conditional URL based on admin status
    if isadmin:
        api_url = f"{host}/monitoring/task?{url_params}"
    else:
        api_url = f"{host}/api/monitoring/task?{url_params}"
    
    return await call(api_url, {}, meta_info)

async def list_alerts_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Calls the Juspay Monitoring API to retrieve a list of configured alerts.

    The API endpoint is:
        https://portal.juspay.in/api/monitoring/task/list (for non-admin users)
        https://portal.juspay.in/monitoring/task/list (for admin users)

    Args:
        payload (dict): A dictionary containing:
            - merchant_id: Merchant ID to retrieve alerts for
            - task_type: Task type filter, should be 'alert'

    Returns:
        dict: The parsed JSON response containing alert configurations.

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
    if not isadmin and payload.get("merchant_id") and mid_from_meta and payload.get("merchant_id") != mid_from_meta:
        raise ValueError("You are not authorized to access alerts for this merchantId")
    
    # Get merchant_id from payload or meta_info
    merchant_id = payload.get("merchant_id") or mid_from_meta
    if not merchant_id:
        raise ValueError("Payload must contain 'merchant_id'.")
    
    request_data = {
        "task_type": payload.get("task_type", "alert"),
        "merchantId": merchant_id
    }
    
    # Conditional URL based on admin status
    if isadmin:
        api_url = f"{host}/monitoring/task/list"
    else:
        api_url = f"{host}/api/monitoring/task/list"
    
    return await post(api_url, request_data, None, meta_info)
