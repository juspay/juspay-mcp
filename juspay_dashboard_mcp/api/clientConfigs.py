# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import logging
from juspay_dashboard_mcp.api.utils import call, get_admin_host, sanitize_merchant_id

logger = logging.getLogger(__name__)

# Per-platform fields to extract from android/ios/web objects
PLATFORM_FIELDS = {
    "creditSubscription",   # Credit Subscription
    "paymentSubscription",  # Payment Subscription
    "paymentFeatures",      # Payment Features
    "status",               # Status
}


def _filter_client_config(item: dict) -> dict:
    """Flatten a single client config item to match the screen layout."""
    filtered = {"clientId": item.get("clientId"), "updatedAt": item.get("updatedAt")}
    for platform in ("android", "ios", "web"):
        platform_data = item.get(platform, {})
        for field in PLATFORM_FIELDS:
            key = f"{platform}_{field}"  # e.g. android_creditSubscription
            filtered[key] = platform_data.get(field)
    return filtered


async def get_client_config_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves client configuration for a specific merchant.

    The API endpoint is:
        https://portal.juspay.in/ec/v1/clientConfiguration/merchant/{merchant_id}?detailed=true  (non-admin)
        {host}/ec/v1/admin/clientConfiguration/merchant/{merchant_id}?detailed=true              (admin)

    Headers include:
        - x-tenant-id from payload (optional)
        - x-web-logintoken from credentials

    Args:
        payload (dict): A dictionary with the following key:
            - merchantId: The merchant ID to fetch client config for.

    Returns:
        dict: Filtered response containing only the fields shown in the Client Config screen:
            clientId, androidCreditSubscription, androidPaymentFeatures,
            androidPaymentSubscription, androidStatus, iosCreditSubscription,
            iosPaymentFeatures, iosPaymentSubscription, iosStatus,
            webCreditSubscription, webPaymentFeatures, webPaymentSubscription,
            webStatus, lastUpdatedBy.

    Raises:
        ValueError: If merchantId cannot be resolved.
        Exception: If the API call fails.
    """
    host, isadmin = await get_admin_host(meta_info=meta_info)

    # Resolve merchantId from payload or meta_info
    mid_from_meta = None
    if meta_info:
        token_response = meta_info.get("token_response", {})
        mid_from_meta = token_response.get("merchantId") or meta_info.get("merchantId")

    # Authorization check - non-admin can't query other merchants
    if not isadmin and payload.get("merchantId") and mid_from_meta and payload.get("merchantId") != mid_from_meta:
        raise ValueError("You are not authorized to access client config for this merchantId")

    if isadmin:
        merchant_id = sanitize_merchant_id(payload.get("merchantId"), mid_from_meta)
    else:
        merchant_id = payload.get("merchantId") or mid_from_meta

    if not merchant_id:
        raise ValueError("The payload must include 'merchantId'.")

    if isadmin:
        api_url = f"{host}/ec/v1/admin/clientConfiguration/merchant/{merchant_id}?detailed=true"
    else:
        api_url = f"{host}/ec/v1/clientConfiguration/merchant/{merchant_id}?detailed=true"

    logger.info(f"Fetching client config for merchant_id={merchant_id}, url={api_url}")

    response = await call(api_url, None, meta_info)

    # API returns a list of client config objects
    if isinstance(response, list):
        filtered = [_filter_client_config(item) for item in response]
        logger.info(f"Filtered client config response: {filtered}")
        return filtered

    # Fallback: single object
    if isinstance(response, dict):
        return _filter_client_config(response)

    return response
