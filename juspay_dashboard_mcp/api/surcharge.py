# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from juspay_dashboard_mcp.api.utils import post, get_admin_host,sanitize_merchant_id

async def list_surcharge_rules_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Returns a list of all configured surcharge rules, including their current status and rule definitions.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/rule/list (for non-admin users)
        https://portal.juspay.in/ec/v1/admin/rule/list (for admin users)

    The call uses no request body.

    Headers include:
        - x-tenant-id from environment variable
        - content-type: application/json

    Args:
        payload (dict): May include:
            - merchantId: Optional merchant ID (admin only).

    Returns:
        dict: The parsed JSON response from the Juspay List Surcharge Rules API.

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
        raise ValueError("You are not authorized to access surcharge rules for this merchantId")
    
    # Build request data
    request_data = {}
    if isadmin:
        merchant_id = sanitize_merchant_id(payload.get("merchantId"), mid_from_meta)
        if merchant_id:
            request_data["merchantId"] = merchant_id
    
    # Conditional URL based on admin status
    if isadmin:
        api_url = f"{host}/ec/v1/admin/rule/list"
    else:
        api_url = f"{host}/api/ec/v1/rule/list"
    
    return await post(api_url, request_data, None, meta_info)
