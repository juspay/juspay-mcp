# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from juspay_dashboard_mcp.api.utils import post, call, get_juspay_host_from_api, get_admin_host, sanitize_merchant_id

async def get_user_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Fetches details for a specific user, identified by user ID.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/user (for non-admin users)
        https://portal.juspay.in/ec/v1/admin/user (for admin users)

    The call uses URL parameters:
        - userId: The unique identifier for the user

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json

    Args:
        payload (dict): A dictionary with the following required key:
            - userId: Unique identifier for the user.
            - merchantId: Optional merchant ID (admin only).

    Returns:
        dict: The parsed JSON response from the Juspay Get User API.

    Raises:
        ValueError: If the userId is missing or non-admin tries to access another merchant's data.
        Exception: If the API call fails.
    """
    if "userId" not in payload:
        raise ValueError("Payload must contain 'userId'.")

    host, isadmin = await get_admin_host(meta_info=meta_info)
    
    # Get merchantId from meta_info for authorization check
    mid_from_meta = None
    if meta_info:
        token_response = meta_info.get("token_response", {})
        mid_from_meta = token_response.get("merchantId") or meta_info.get("merchantId")
    
    # Authorization check - non-admin can't query other merchants
    if not isadmin and payload.get("merchantId") and mid_from_meta and payload.get("merchantId") != mid_from_meta:
        raise ValueError("You are not authorized to access user details for this merchantId")
    
    # Build URL with query params
    url_params = f"userId={payload['userId']}"
    if isadmin:
        merchant_id = sanitize_merchant_id(payload.get("merchantId"), mid_from_meta)
        if merchant_id:
            url_params += f"&merchantId={merchant_id}"
    
    # Conditional URL based on admin status
    if isadmin:
        api_url = f"{host}/ec/v1/admin/user?{url_params}"
    else:
        api_url = f"{host}/api/ec/v1/user?{url_params}"
    
    return await call(api_url, None, meta_info)

async def list_users_v2_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves a list of users associated with a merchant, with optional pagination.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v2/user/list (for non-admin users)
        https://portal.juspay.in/ec/v2/admin/user/list (for admin users)

    The call uses JSON data containing:
        - offset: Pagination offset (optional, default 0)

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json

    Args:
        payload (dict): A dictionary that may contain:
            - offset: Pagination offset (optional, default 0)
            - merchantId: Optional merchant ID (admin only).

    Returns:
        dict: The parsed JSON response containing a list of users.

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
        raise ValueError("You are not authorized to access users for this merchantId")
    
    request_data = {
        "offset": payload.get("offset", 0)
    }
    
    # For admin, add merchantId to request
    if isadmin:
        merchant_id = sanitize_merchant_id(payload.get("merchantId"), mid_from_meta)
        if merchant_id:
            request_data["merchantId"] = merchant_id
    
    # Conditional URL based on admin status
    if isadmin:
        api_url = f"{host}/ec/v2/admin/user/list"
    else:
        api_url = f"{host}/api/ec/v2/user/list"
    
    return await post(api_url, request_data, None, meta_info)
