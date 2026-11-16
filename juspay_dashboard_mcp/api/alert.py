# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from juspay_dashboard_mcp.api.utils import post, get_juspay_host_from_api, call, sanitize_merchant_id, assert_merchant_access

async def alert_details(payload: dict, meta_info: dict = None) -> dict:
    """
    Provides detailed information for a specific alert ID, including source, monitored metrics, and applied filters.

    The API endpoint is:
        https://portal.juspay.in/api/monitoring/task

    Args:
        payload (dict): Must contain 'task_uid' and 'user_name'.

    Returns:
        dict: The parsed JSON response from the Juspay Alert Details API.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    
    # Build URL with query params
    url_params = f"task_uid={payload['task_uid']}&user_name={payload['user_name']}"
    
    api_url = f"{host}/api/monitoring/task?{url_params}"
    
    return await call(api_url, {}, meta_info)

async def list_alerts(payload: dict, meta_info: dict = None) -> dict:
    """
    Calls the Juspay Monitoring API to retrieve a list of configured alerts.

    The API endpoint is:
        https://portal.juspay.in/api/monitoring/task/list

    Args:
        payload (dict): A dictionary containing:
            - merchant_id: Merchant ID to retrieve alerts for
            - task_type: Task type filter, should be 'alert'

    Returns:
        dict: The parsed JSON response containing alert configurations.

    Raises:
        ValueError: If a caller tries to access another merchant's data.
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    
    
    assert_merchant_access(payload.get("merchant_id"), "You are not authorized to access alerts for this merchantId")
    
    # Get merchant_id from payload or meta_info
    merchant_id = sanitize_merchant_id(payload.get("merchant_id"))
    if not merchant_id:
        raise ValueError("Payload must contain 'merchant_id'.")
    
    request_data = {
        "task_type": payload.get("task_type", "alert"),
        "merchantId": merchant_id
    }
    
    api_url = f"{host}/api/monitoring/task/list"
    
    return await post(api_url, request_data, None, meta_info)