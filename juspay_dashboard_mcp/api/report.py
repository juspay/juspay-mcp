# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from juspay_dashboard_mcp.api.utils import call, post, get_admin_host,sanitize_merchant_id

async def report_details_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Returns detailed information for a specific report ID, including data sources, 
    metrics, dimensions, and filters.

    The API endpoint is:
        https://portal.juspay.in/api/monitoring/task (for non-admin users)
        https://portal.juspay.in/monitoring/task (for admin users)

    The call uses URL parameters:
        - task_uid: Unique identifier for the report/task
        - user_name: Name of the user requesting the report

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json

    Args:
        payload (dict): A dictionary with the following required keys:
            - task_uid: Unique identifier for the report/task.
            - user_name: Name of the user requesting the report.
            - merchantId: Optional merchant ID (admin only).

    Returns:
        dict: The parsed JSON response from the Juspay Report Details API.

    Raises:
        ValueError: If required parameters are missing or non-admin tries to access another merchant's data.
        Exception: If the API call fails.
    """
    task_uid = payload.get("task_uid")
    user_name = payload.get("user_name")
    
    if not task_uid or not user_name:
        raise ValueError("The payload must include 'task_uid' and 'user_name'.")

    host, isadmin = await get_admin_host(meta_info=meta_info)
    
    # Get merchantId from meta_info for authorization check
    mid_from_meta = None
    if meta_info:
        token_response = meta_info.get("token_response", {})
        mid_from_meta = token_response.get("merchantId") or meta_info.get("merchantId")
    
    # Authorization check - non-admin can't query other merchants
    if not isadmin and payload.get("merchantId") and mid_from_meta and payload.get("merchantId") != mid_from_meta:
        raise ValueError("You are not authorized to access report details for this merchantId")
    
    # Build URL with query params
    url_params = f"task_uid={task_uid}&user_name={user_name}"
    if isadmin:
        merchant_id = sanitize_merchant_id(payload.get("merchantId"), mid_from_meta)
        if merchant_id:
            url_params += f"&merchantId={merchant_id}"
    
    # Conditional URL based on admin status
    if isadmin:
        api_url = f"{host}/monitoring/task?{url_params}"
    else:
        api_url = f"{host}/api/monitoring/task?{url_params}"
    
    # Empty body since parameters are in URL
    return await call(api_url, None, meta_info)

async def list_report_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Lists all reports configured by the merchant, along with their status, recipients, 
    thresholds, and monitoring intervals.

    The API endpoint is:
        https://portal.juspay.in/api/monitoring/task/list (for non-admin users)
        https://portal.juspay.in/monitoring/task/list (for admin users)

    The call uses JSON data containing:
        - merchantId: Merchant identifier
        - task_type: Set to 'report'
        - std_report: Optional boolean flag

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json

    Args:
        payload (dict): A dictionary containing:
            - merchantId: Merchant identifier.
            - task_type: Should be set to 'report'.
            - std_report: (Optional) Boolean flag.

    Returns:
        dict: The parsed JSON response from the Juspay List Report API.

    Raises:
        ValueError: If required parameters are missing or non-admin tries to access another merchant's data.
        Exception: If the API call fails.
    """
    if payload.get("task_type") != "report":
        raise ValueError("Payload must contain 'task_type' set to 'report'.")
    
    host, isadmin = await get_admin_host(meta_info=meta_info)
    
    # Get merchantId from meta_info for authorization check
    mid_from_meta = None
    if meta_info:
        token_response = meta_info.get("token_response", {})
        mid_from_meta = token_response.get("merchantId") or meta_info.get("merchantId")
    
    # Authorization check - non-admin can't query other merchants
    if not isadmin and payload.get("merchantId") and mid_from_meta and payload.get("merchantId") != mid_from_meta:
        raise ValueError("You are not authorized to access reports for this merchantId")
    
    # Build request data - use merchantId from payload or meta_info for admin
    merchant_id = sanitize_merchant_id(payload.get("merchantId"), mid_from_meta)
    if not merchant_id:
        raise ValueError("Payload must contain 'merchantId'.")
    
    request_data = {
        "merchantId": merchant_id,
        "task_type": payload.get("task_type")
    }
    
    # Conditional URL based on admin status
    if isadmin:
        api_url = f"{host}/monitoring/task/list"
    else:
        api_url = f"{host}/api/monitoring/task/list"
    
    return await post(api_url, request_data, None, meta_info)
