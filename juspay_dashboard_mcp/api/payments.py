# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from juspay_dashboard_mcp.api.utils import post, get_juspay_host_from_api, ist_to_utc


async def list_payment_links_v1_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Calls the Juspay Portal API to retrieve a list of payment links within a specified time range.

    Args:
        payload (dict): Should contain 'qFilters', 'date_from', and 'date_to' as required by the API.
            - qFilters: Query filters for the API (dict)
            - date_from: Start date/time in ISO 8601 format (required)
            - date_to: End date/time in ISO 8601 format (required)
            - offset: Pagination offset (optional, default 0)

    Returns:
        dict: The parsed JSON response from the List Payment Links API.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    api_url = f"{host}/api/ec/v1/paymentLinks/list"

    request_payload = {}

    if "qFilters" in payload:
        request_payload["qFilters"] = payload["qFilters"]
    else:
        request_payload["qFilters"] = {
            "field": "order_source_object",
            "condition": "Equals",
            "val": "PAYMENT_LINK",
        }

    if "offset" in payload:
        request_payload["offset"] = payload["offset"]

    date_from_str = payload.get("date_from")
    date_to_str = payload.get("date_to")

    if not date_from_str or not date_to_str:
        raise ValueError("Both 'date_from' and 'date_to' are required in the payload")

    date_from_str = ist_to_utc(date_from_str)
    date_to_str = ist_to_utc(date_to_str)

    request_payload["filters"] = {
        "dateCreated": {"gte": date_from_str, "lte": date_to_str}
    }

    return await post(api_url, request_payload, None, meta_info)
