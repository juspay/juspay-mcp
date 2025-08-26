# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from juspay_dashboard_mcp.api.utils import post, get_juspay_host_from_api

async def list_configured_gateways_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves a list of all payment gateways (PGs) configured for a merchant,
    including high-level details such as gateway reference ID, creation/modification dates,
    and configured payment methods (PMs). Note: Payment Method Types (PMTs) are not included.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/gateway/list

    The call uses JSON data containing:
        - merchantId (e.g., "paypal")

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json

    Args:
        payload (dict): A dictionary with the following required key:
            - merchantId: Merchant identifier.

    Returns:
        dict: The parsed JSON response from the Juspay List Configured Gateways API.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    api_url = f"{host}/api/ec/v1/gateway/list"
    return await post(api_url, payload, None, meta_info)

async def get_gateway_scheme_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Provides detailed configuration information for a gateway, including:
    1. Required and optional fields (with descriptions and data types).
    2. Supported payment methods and payment flows.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v2/gateway/scheme/{gateway}

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
        Exception: If the API call fails.
    """
    gateway = payload.pop("gateway", None)
    if not gateway:
        raise ValueError("The payload must include 'gateway'.")

    host = await get_juspay_host_from_api(meta_info=meta_info)
    api_url = f"{host}/api/ec/v2/gateway/scheme/{gateway}"

    return await post(api_url, payload, None, meta_info)

async def get_gateway_details_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Returns detailed information about a specific gateway configured by the merchant.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/gateway/{mga_id}

    The call uses JSON data containing:
        - merchantId (e.g., "paypal")

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json

    Args:
        payload (dict): A dictionary with the following required keys:
            - mga_id: MGA ID of the gateway.
            - merchantId: Merchant identifier.

    Returns:
        dict: The parsed JSON response from the Juspay Get Gateway Details API.

    Raises:
        Exception: If the API call fails.
    """
    mga_id = payload.pop("mga_id", None)
    merchant_id = payload.get("merchant_id")

    if not mga_id or not merchant_id:
        raise ValueError("The payload must include 'mga_id' and 'merchantId'.")

    host = await get_juspay_host_from_api(meta_info=meta_info)
    api_url = f"{host}/api/ec/v1/gateway/{mga_id}"

    return await post(api_url, payload, None, meta_info)

async def list_gateway_scheme_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Provides a list of all available payment gateways that can be configured on PGCC.
    Useful for checking support for specific gateways (e.g., "Does Juspay support Gateway X?").

    The API endpoint is:
        https://portal.juspay.in/api/ec/v2/gateway/scheme/list

    The call uses no request body.

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json

    Returns:
        list: The parsed JSON response from the Juspay List Gateway Scheme API.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    api_url = f"{host}/api/ec/v2/gateway/scheme/list"
    return await post(api_url, {}, None, meta_info)

async def get_merchant_gateways_pm_details_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Fetches all gateways and their supported payment methods for the merchant.

    Args:
        payload (dict): Not required for this API.

    Returns:
        dict: The parsed JSON response from the Juspay Gateway Payment Methods API.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    api_url = f"{host}/api/ec/v1/gateway/paymentMethods"
    return await post(api_url, {}, None, meta_info)