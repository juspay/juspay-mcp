# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from juspay_dashboard_mcp.api.utils import post, call, get_juspay_host_from_api

async def get_offer_details_juspay(payload: dict, meta_info: dict = None) -> dict:
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
        - x-tenant-id from payload
        - content-type: application/json
        - x-web-logintoken from config

    Args:
        payload (dict): A dictionary with the following required key:
            - offerId: The unique offer ID to retrieve details for.
            - merchantId: Merchant ID for the offer.

    Returns:
        dict: The parsed JSON response containing offer details.

    Raises:
        ValueError: If merchantId is missing.
        Exception: If the API call fails.
    """
    merchant_id = payload.get("merchant_id")
    if not merchant_id:
        raise ValueError("'merchantId' is required in the payload")

    host = await get_juspay_host_from_api()
    api_url = f"{host}/api/offers/dashboard/detail?merchant_id={merchant_id}"
    
    return await post(api_url, payload, None, meta_info)

async def list_offers_juspay(payload: dict, meta_info: dict = None) -> dict:
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
        - x-tenant-id from payload
        - content-type: application/json

    Args:
        payload (dict): A dictionary containing:
            - merchant_id: Merchant identifier.
            - start_time: Start time for filtering offers.
            - end_time: End time for filtering offers.

    Returns:
        dict: The parsed JSON response from the Juspay List Offers API.

    Raises:
        ValueError: If required parameters are missing.
        Exception: If the API call fails.
    """
    if "merchant_id" not in payload or "start_time" not in payload or "end_time" not in payload:
        raise ValueError("Payload must contain 'merchant_id', 'start_time', and 'end_time'.")

    merchant_id = payload.get("merchant_id")
    host = await get_juspay_host_from_api()
    api_url = f"{host}/api/offers/dashboard/dashboard-list?merchant_id={merchant_id}"
    
    return await post(api_url, payload, None, meta_info)
