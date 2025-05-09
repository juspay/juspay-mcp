# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from datetime import datetime, timezone
from juspay_dashboard_mcp.api.utils import post, get_juspay_host_from_api, call
from urllib.parse import urlencode
from juspay_dashboard_mcp.config import get_common_headers
import os
import dotenv

dotenv.load_dotenv()

async def list_orders_v4_juspay(payload: dict) -> dict:
    """
    Calls the Juspay Portal API to retrieve a list of orders within a specified time range.

    Args:
        payload (dict): A dictionary containing:
            - dateFrom: Start date/time in ISO format (e.g., '2025-04-15T18:30:00Z')
            - dateTo: End date/time in ISO format (e.g., '2025-04-16T15:06:00Z')
            - offset: Pagination offset (optional, default 0)
            - domain: Domain for query (optional, default 'ordersELS')
            - paymentStatus: Optional filter for payment status
            - orderType: Optional filter for order type

    Returns:
        dict: The parsed JSON response from the List Orders API.

    Raises:
        ValueError: If required parameters are missing or date formats are invalid.
        Exception: If the API call fails.
    """
    date_from_str = payload.get("dateFrom")
    date_to_str = payload.get("dateTo")
    if not date_from_str or not date_to_str:
        raise ValueError("Both 'dateFrom' and 'dateTo' are required in the payload")

    try:
        date_from_dt = datetime.fromisoformat(date_from_str.replace("Z", "+00:00"))
        date_to_dt = datetime.fromisoformat(date_to_str.replace("Z", "+00:00"))
        if date_from_dt.tzinfo is None:
            date_from_dt = date_from_dt.replace(tzinfo=timezone.utc)
        if date_to_dt.tzinfo is None:
            date_to_dt = date_to_dt.replace(tzinfo=timezone.utc)
    except ValueError:
        raise ValueError(
            "Invalid ISO 8601 format for 'dateFrom' or 'dateTo'. Use format like 'YYYY-MM-DDTHH:MM:SSZ'"
        )

    date_from_ts = int(date_from_dt.timestamp())
    date_to_ts = int(date_to_dt.timestamp())

    request_data = {
        "offset": payload.get("offset", 0),
        "filters": {
            "dateCreated": {
                "lte": date_to_str,
                "gte": date_from_str,
            }
        },
        "order": [["date_created", "DESC"]],
        "qFilters": {
            "and": {
                "right": {
                    "field": "order_created_at",
                    "condition": "LessThanEqual",
                    "val": str(date_to_ts),
                },
                "left": {
                    "field": "order_created_at",
                    "condition": "GreaterThanEqual",
                    "val": str(date_from_ts),
                },
            }
        },
        "domain": payload.get("domain", "ordersELS"),
        "sortDimension": "order_created_at",
    }

    if payload.get("paymentStatus"):
        request_data["qFilters"]["and"]["payment_status"] = payload["paymentStatus"]

    if payload.get("orderType"):
        request_data["qFilters"]["and"]["order_type"] = payload["orderType"]

    host = await get_juspay_host_from_api()
    api_url = f"{host}/ec/v4/orders"
    return await post(api_url, request_data)


async def get_order_details_juspay(payload: dict, meta_info: dict) -> dict:
    """
    Calls the Juspay Portal API to retrieve detailed information for a specific order.

    Args:
        payload (dict): A dictionary containing:
            - order_id: The unique order ID to retrieve details for

    Returns:
        dict: The parsed JSON response containing order details.

    Raises:
        Exception: If the API call fails.
    """
    order_id = payload.get("order_id")
    if not order_id:
        raise ValueError("'order_id' is required in the payload")

    host = await get_juspay_host_from_api()
    api_url = f"{host}/api/ec/v1/orders/{order_id}"
    return await post(api_url, {}, None, meta_info)
