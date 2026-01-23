# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import logging
from juspay_dashboard_mcp.api.utils import post, get_juspay_host_from_api, get_admin_host, sanitize_merchant_id

logger = logging.getLogger(__name__)

async def list_configured_gateways_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves a list of all payment gateways (PGs) configured for a merchant,
    including high-level details such as gateway reference ID, creation/modification dates,
    and configured payment methods (PMs). Note: Payment Method Types (PMTs) are not included.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/gateway/list (for non-admin users)
        https://portal.juspay.in/ec/v1/admin/gateway/list (for admin users)

    The call uses JSON data containing:
        - merchantId (e.g., "paypal")

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json

    Args:
        payload (dict): A dictionary with the following key:
            - merchantId: Merchant identifier (optional for non-admin, recommended for admin).

    Returns:
        dict: The parsed JSON response from the Juspay List Configured Gateways API.

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
        raise ValueError("You are not authorized to access gateway list for this merchantId")
    
    # Build request data
    request_data = dict(payload)
    if isadmin:
        merchant_id = sanitize_merchant_id(payload.get("merchantId"), mid_from_meta)
        if merchant_id:
            request_data["merchantId"] = merchant_id
    
    # Conditional URL based on admin status
    if isadmin:
        api_url = f"{host}/ec/v1/admin/gateway/list"
    else:
        api_url = f"{host}/api/ec/v1/gateway/list"
    
    return await post(api_url, request_data, None, meta_info)

async def get_gateway_scheme_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Provides detailed configuration information for a gateway, including:
    1. Required and optional fields (with descriptions and data types).
    2. Supported payment methods and payment flows.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v2/gateway/scheme/{gateway} (for non-admin users)
        https://portal.juspay.in/ec/v2/admin/gateway/scheme/{gateway} (for admin users)

    The call uses JSON data containing:
        - merchantId (optional, but recommended)

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json

    Args:
        payload (dict): A dictionary with the following required key:
            - gateway: Gateway code (e.g., "TATA_PA").
            - merchantId: Merchant identifier (optional).

    Returns:
        dict: The parsed JSON response from the Juspay Get Gateway Scheme API.

    Raises:
        ValueError: If non-admin user tries to access another merchant's data.
        Exception: If the API call fails.
    """
    gateway = payload.pop("gateway", None)
    if not gateway:
        raise ValueError("The payload must include 'gateway'.")

    host, isadmin = await get_admin_host(meta_info=meta_info)
    
    # Get merchantId from meta_info for authorization check
    mid_from_meta = None
    if meta_info:
        token_response = meta_info.get("token_response", {})
        mid_from_meta = token_response.get("merchantId") or meta_info.get("merchantId")
    
    # Authorization check - non-admin can't query other merchants
    if not isadmin and payload.get("merchantId") and mid_from_meta and payload.get("merchantId") != mid_from_meta:
        raise ValueError("You are not authorized to access gateway scheme for this merchantId")
    
    # Build request data - merchantId is required for both admin and non-admin
    merchant_id = sanitize_merchant_id(payload.get("merchantId"), mid_from_meta)
    if not merchant_id:
        raise ValueError("The payload must include 'merchantId'.")
    
    request_data = dict(payload)
    request_data["merchantId"] = merchant_id
    
    # Conditional URL based on admin status
    if isadmin:
        api_url = f"{host}/ec/v2/admin/gateway/scheme/{gateway}"
    else:
        api_url = f"{host}/api/ec/v2/gateway/scheme/{gateway}"

    return await post(api_url, request_data, None, meta_info)

async def get_gateway_details_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Returns detailed information about a specific gateway configured by the merchant.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/gateway/{mga_id} (for non-admin users)
        https://portal.juspay.in/ec/v1/admin/gateway/{mga_id} (for admin users)

    The call uses JSON data containing:
        - merchantId (e.g., "paypal")

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json

    Args:
        payload (dict): A dictionary with the following required keys:
            - mga_id: MGA ID of the gateway.
            - merchantId: Merchant identifier (required for admin, auto-detected for non-admin).

    Returns:
        dict: The parsed JSON response from the Juspay Get Gateway Details API.

    Raises:
        ValueError: If non-admin user tries to access another merchant's data.
        Exception: If the API call fails.
    """
    # DEBUG: Log incoming payload and meta_info
    logger.info(f"[DEBUG] get_gateway_details_juspay - Incoming payload: {payload}")
    logger.info(f"[DEBUG] get_gateway_details_juspay - Incoming meta_info: {meta_info}")
    
    host, isadmin = await get_admin_host(meta_info=meta_info)
    logger.info(f"[DEBUG] get_gateway_details_juspay - host: {host}, isadmin: {isadmin}")
    
    mga_id = payload.pop("mga_id", None)
    merchant_id_from_payload = payload.get("merchantId")
    logger.info(f"[DEBUG] get_gateway_details_juspay - merchantId from payload: {merchant_id_from_payload}")
    
    # Get merchantId from meta_info for authorization check
    mid_from_meta = None
    if meta_info:
        token_response = meta_info.get("token_response", {})
        mid_from_meta = token_response.get("merchantId") or meta_info.get("merchantId")
    logger.info(f"[DEBUG] get_gateway_details_juspay - merchantId from meta_info: {mid_from_meta}")
    logger.info(f"[DEBUG] get_gateway_details_juspay - token_response: {meta_info.get('token_response', {}) if meta_info else 'None'}")
    
    # Authorization check - non-admin can't query other merchants
    if not isadmin and merchant_id_from_payload and mid_from_meta and merchant_id_from_payload != mid_from_meta:
        raise ValueError("You are not authorized to access gateway details for this merchantId")
    
    # Use sanitize_merchant_id to filter out placeholder values
    merchant_id = sanitize_merchant_id(merchant_id_from_payload, mid_from_meta)
    logger.info(f"[DEBUG] get_gateway_details_juspay - Final merchantId: {merchant_id}")
        
    if not mga_id or not merchant_id:
        raise ValueError("The payload must include 'mga_id' and 'merchantId'.")
    
    # Build request data with merchantId
    request_data = {"merchantId": merchant_id}
    logger.info(f"[DEBUG] get_gateway_details_juspay - Final request_data: {request_data}")
    
    # Conditional URL based on admin status
    if isadmin:
        api_url = f"{host}/ec/v1/admin/gateway/{mga_id}"
    else:
        api_url = f"{host}/api/ec/v1/gateway/{mga_id}"
    
    logger.info(f"[DEBUG] get_gateway_details_juspay - Final api_url: {api_url}")

    return await post(api_url, request_data, None, meta_info)

async def list_gateway_scheme_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Provides a list of all available payment gateways that can be configured on PGCC.
    Useful for checking support for specific gateways (e.g., "Does Juspay support Gateway X?").

    The API endpoint is:
        https://portal.juspay.in/api/ec/v2/gateway/scheme/list (for non-admin users)
        https://portal.juspay.in/ec/v2/admin/gateway/scheme/list (for admin users)

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json

    Args:
        payload (dict): May include:
            - merchantId: Optional merchant ID (admin only).

    Returns:
        list: The parsed JSON response from the Juspay List Gateway Scheme API.

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
        raise ValueError("You are not authorized to access gateway scheme list for this merchantId")
    
    # Build request data
    request_data = {}
    if isadmin:
        merchant_id = sanitize_merchant_id(payload.get("merchantId"), mid_from_meta)
        if merchant_id:
            request_data["merchantId"] = merchant_id
    
    # Conditional URL based on admin status
    if isadmin:
        api_url = f"{host}/ec/v2/admin/gateway/scheme/list"
    else:
        api_url = f"{host}/api/ec/v2/gateway/scheme/list"
    
    return await post(api_url, request_data, None, meta_info)

async def get_merchant_gateways_pm_details_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Fetches all gateways and their supported payment methods for the merchant.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/gateway/paymentMethods (for non-admin users)
        https://portal.juspay.in/ec/v1/admin/gateway/paymentMethods (for admin users)

    Args:
        payload (dict): May include:
            - merchantId: Optional merchant ID (admin only).

    Returns:
        dict: The parsed JSON response from the Juspay Gateway Payment Methods API.

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
        raise ValueError("You are not authorized to access gateway payment methods for this merchantId")
    
    # Build request data
    request_data = {}
    if isadmin:
        merchant_id = sanitize_merchant_id(payload.get("merchantId"), mid_from_meta)
        if merchant_id:
            request_data["merchantId"] = merchant_id
    
    # Conditional URL based on admin status
    if isadmin:
        api_url = f"{host}/ec/v1/admin/gateway/paymentMethods"
    else:
        api_url = f"{host}/api/ec/v1/gateway/paymentMethods"
    
    return await post(api_url, request_data, None, meta_info)
