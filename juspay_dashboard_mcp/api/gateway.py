# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from urllib.parse import quote
import logging
from juspay_dashboard_mcp.api.utils import post, get_juspay_host_from_api, resolve_merchant_id, paginate_response, paginate_dict_keys, mask_fields

logger = logging.getLogger(__name__)

# Substrings (matched case-insensitively against each key), see mask_fields.
# Gateway account details carry per-gateway credentials such as checkoutSecretKey,
# payuSalt, payuMerchantKey, authToken, accessToken, refreshToken, razorpaySecret,
# hashKey, phonepeKey1 and forwardingEntityPassword inside a JSON-encoded string.
GATEWAY_SECRET_KEYS = {
    "secret",
    "password",
    "salt",
    "token",
    "key",
    "certcontent",
    "accesscode",
}

async def list_configured_gateways(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves a list of all payment gateways (PGs) configured for a merchant,
    including high-level details such as gateway reference ID, creation/modification dates,
    and configured payment methods (PMs). Note: Payment Method Types (PMTs) are not included.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/gateway/list

    The call uses JSON data containing:
        - merchantId (e.g., "paypal")

    Headers include:
        - content-type: application/json

    Args:
        payload (dict): A dictionary with the following key:
            - merchantId: Merchant identifier (optional; must match the token's merchant).

    Returns:
        dict: The parsed JSON response from the Juspay List Configured Gateways API.

    Raises:
        ValueError: If a caller tries to access another merchant's data.
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    
    
    resolve_merchant_id(payload.get("merchantId"), "You are not authorized to access gateway list for this merchantId")
    
    # Build request data
    request_data = dict(payload)
    
    api_url = f"{host}/api/ec/v1/gateway/list"

    response = mask_fields(await post(api_url, request_data, None, meta_info), GATEWAY_SECRET_KEYS)
    return paginate_response(response, payload.get("limit", 20), payload.get("offset", 0))

async def get_gateway_scheme(payload: dict, meta_info: dict = None) -> dict:
    """
    Provides detailed configuration information for a gateway, including:
    1. Required and optional fields (with descriptions and data types).
    2. Supported payment methods and payment flows.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v2/gateway/scheme/{gateway}

    The call uses JSON data containing:
        - merchantId (optional, but recommended)

    Headers include:
        - content-type: application/json

    Args:
        payload (dict): A dictionary with the following required key:
            - gateway: Gateway code (e.g., "TATA_PA").
            - merchantId: Merchant identifier (optional).

    Returns:
        dict: The parsed JSON response from the Juspay Get Gateway Scheme API.

    Raises:
        ValueError: If a caller tries to access another merchant's data.
        Exception: If the API call fails.
    """
    gateway = payload.pop("gateway", None)
    if not gateway:
        raise ValueError("The payload must include 'gateway'.")

    host = await get_juspay_host_from_api(meta_info=meta_info)
    
    
    merchant_id = resolve_merchant_id(payload.get("merchantId"), "You are not authorized to access gateway scheme for this merchantId")
    
    if not merchant_id:
        raise ValueError("The payload must include 'merchantId'.")
    
    request_data = dict(payload)
    request_data["merchantId"] = merchant_id
    
    api_url = f"{host}/api/ec/v2/gateway/scheme/{quote(str(gateway), safe='')}"

    return mask_fields(await post(api_url, request_data, None, meta_info), GATEWAY_SECRET_KEYS)

async def get_gateway_details(payload: dict, meta_info: dict = None) -> dict:
    """
    Returns detailed information about a specific gateway configured by the merchant.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/gateway/{mga_id}

    The call uses JSON data containing:
        - merchantId (e.g., "paypal")

    Headers include:
        - content-type: application/json

    Args:
        payload (dict): A dictionary with the following required keys:
            - mga_id: MGA ID of the gateway.
            - merchantId: Merchant identifier (optional; must match the token's merchant).

    Returns:
        dict: The parsed JSON response from the Juspay Get Gateway Details API.

    Raises:
        ValueError: If a caller tries to access another merchant's data.
        Exception: If the API call fails.
    """
    
    host = await get_juspay_host_from_api(meta_info=meta_info)
    
    mga_id = payload.pop("mga_id", None)
    merchant_id_from_payload = payload.get("merchantId")
    
    
    merchant_id = resolve_merchant_id(merchant_id_from_payload, "You are not authorized to access gateway details for this merchantId")
    
        
    if not mga_id or not merchant_id:
        raise ValueError("The payload must include 'mga_id' and 'merchantId'.")
    
    # Build request data with merchantId
    request_data = {"merchantId": merchant_id}
    
    api_url = f"{host}/api/ec/v1/gateway/{quote(str(mga_id), safe='')}"
    

    return mask_fields(await post(api_url, request_data, None, meta_info), GATEWAY_SECRET_KEYS)

async def list_gateway_scheme(payload: dict, meta_info: dict = None) -> dict:
    """
    Provides a list of all available payment gateways that can be configured on PGCC.
    Useful for checking support for specific gateways (e.g., "Does Juspay support Gateway X?").

    The API endpoint is:
        https://portal.juspay.in/api/ec/v2/gateway/scheme/list

    Headers include:
        - content-type: application/json

    Args:
        payload (dict): May include:

    Returns:
        list: The parsed JSON response from the Juspay List Gateway Scheme API.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    
    # Build request data
    request_data = {}
    
    api_url = f"{host}/api/ec/v2/gateway/scheme/list"
    
    return mask_fields(await post(api_url, request_data, None, meta_info), GATEWAY_SECRET_KEYS)

async def get_merchant_gateways_pm_details(payload: dict, meta_info: dict = None) -> dict:
    """
    Fetches all gateways and their supported payment methods for the merchant.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/gateway/paymentMethods

    Args:
        payload (dict): May include:

    Returns:
        dict: The parsed JSON response from the Juspay Gateway Payment Methods API.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    
    # Build request data
    request_data = {}
    
    api_url = f"{host}/api/ec/v1/gateway/paymentMethods"

    response = await post(api_url, request_data, None, meta_info)
    return paginate_dict_keys(response, payload.get("limit", 20), payload.get("offset", 0))