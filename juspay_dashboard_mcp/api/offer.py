# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from juspay_dashboard_mcp.api.utils import (
    post,
    call,
    get_juspay_host_from_api,
    sanitize_merchant_id,
    assert_merchant_access
)


async def get_offer_details(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves detailed information for a specific offer.

    The API endpoint is:
        https://portal.juspay.in/api/offers/dashboard/detail 

    The call uses URL parameters:
        - merchant_id: Merchant identifier

    And JSON body containing:
        - offer_ids: Array containing the offer ID
        - merchant_id: Merchant identifier

    Headers include:
        - content-type: application/json
        - x-web-logintoken from config

    Args:
        payload (dict): A dictionary with the following required key:
            - offerId: The unique offer ID to retrieve details for.
            - merchant_id: Merchant ID for the offer.

    Returns:
        dict: The parsed JSON response containing offer details.

    Raises:
        ValueError: If merchant_id is missing or a caller tries to access another merchant's data.
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    
    
    assert_merchant_access(payload.get("merchant_id"), "You are not authorized to access offer details for this merchantId")
    
    
    # Get merchant_id from payload or meta_info
    merchant_id = sanitize_merchant_id(payload.get("merchant_id"))
    if not merchant_id:
        raise ValueError("'merchant_id' is required in the payload")

    api_url = f"{host}/api/offers/dashboard/detail?merchant_id={merchant_id}"
    
    return await post(api_url, payload, None, meta_info)

async def list_offers(payload: dict, meta_info: dict = None) -> dict:
    """
    Lists all offers configured by the merchant, along with key details such as 
    status, PMT, offer code, start/end times, and benefit types.

    The API endpoint is:
        https://portal.juspay.in/api/offers/dashboard/dashboard-list

    The call uses URL parameters:
        - merchant_id: Merchant identifier

    And JSON body containing:
        - merchant_id: Merchant identifier
        - start_time: Start time for filtering offers
        - end_time: End time for filtering offers

    Headers include:
        - content-type: application/json

    Args:
        payload (dict): A dictionary containing:
            - merchant_id: Merchant identifier.
            - start_time: Start time for filtering offers.
            - end_time: End time for filtering offers.

    Returns:
        dict: The parsed JSON response from the Juspay List Offers API.

    Raises:
        ValueError: If required parameters are missing or a caller tries to access another merchant's data.
        Exception: If the API call fails.
    """
    if "start_time" not in payload or "end_time" not in payload:
        raise ValueError("Payload must contain 'start_time' and 'end_time'.")

    host = await get_juspay_host_from_api(meta_info=meta_info)
    
    
    assert_merchant_access(payload.get("merchant_id"), "You are not authorized to access offers for this merchantId")
    
    
    # Get merchant_id from payload or meta_info
    merchant_id = sanitize_merchant_id(payload.get("merchant_id"))
    if not merchant_id:
        raise ValueError("Payload must contain 'merchant_id'.")

    start_time = payload.get("start_time")
    end_time = payload.get("end_time")

    created_at = {"gte": start_time, "lte": end_time}

    payload_updated = {
        **payload,
        "merchant_id": merchant_id,
        "start_time": start_time,
        "end_time": end_time,
        "created_at": created_at,
        "sort_offers": payload.get("sort_offers") or {"field": "CREATED_AT", "order": "DESCENDING"},
    }

    api_url = f"{host}/api/offers/dashboard/dashboard-list?merchant_id={merchant_id}"

    return await post(api_url, payload_updated, None, meta_info)