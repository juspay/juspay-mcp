# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from datetime import datetime, timezone
from juspay_dashboard_mcp.api.utils import call, get_juspay_host_from_api, call, ist_to_utc, make_payout_additional_headers
from urllib.parse import urlencode
from juspay_dashboard_mcp.config import get_common_headers
from typing import Dict, Any
import os
import dotenv
import re
import logging

dotenv.load_dotenv()


async def list_payout_orders_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Calls the Juspay Payout API to retrieve a list of payout orders within a specified time range.

    Args:
        payload (dict): A dictionary containing:
            - dateFrom: Start date/time in ISO format (e.g., '2025-03-28T14:16:00Z')
            - dateTo: End date/time in ISO format (e.g., '2025-03-28T15:16:00Z')
            - limit: Number of orders to retrieve (optional, default 100, max 100)
            - offset: Pagination offset (optional, default 0)

    Returns:
        dict: The parsed JSON response from the Payout Orders API containing:
            - List of payout orders with order details, fulfillments, and transactions
            - Pagination information
            - Order counts and status information

    Raises:
        ValueError: If required parameters are missing or date formats are invalid.
        Exception: If the API call fails.
    """
    date_from_str = payload.get("dateFrom")
    date_to_str = payload.get("dateTo")
    if not date_from_str or not date_to_str:
        raise ValueError("Both 'dateFrom' and 'dateTo' are required in the payload")

    # Convert IST to UTC if needed
    date_from_str = ist_to_utc(date_from_str)
    date_to_str = ist_to_utc(date_to_str)

    # Validate date formats
    try:
        datetime.fromisoformat(date_from_str.replace("Z", "+00:00"))
        datetime.fromisoformat(date_to_str.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(
            "Invalid ISO 8601 format for 'dateFrom' or 'dateTo'. Use format like 'YYYY-MM-DDTHH:MM:SSZ'"
        )

    # Build query parameters
    query_params = {
        "createdAt.gte": date_from_str,
        "createdAt.lte": date_to_str,
        "limit": payload.get("limit", 100),
        "offset": payload.get("offset", 0)
    }

    # Construct API URL with query parameters
    host = await get_juspay_host_from_api(meta_info=meta_info)
    api_url = f"{host}/api/payout/batch/dashboard/v1/orders"
    
    # Add query parameters to URL
    query_string = urlencode(query_params)
    full_url = f"{api_url}?{query_string}"

    logging.info(f"Calling payout orders API: {full_url}")
    
    # Make GET request (no body needed)
    additional_headers = make_payout_additional_headers(meta_info)
    return await call(full_url, additional_headers=additional_headers, meta_info=meta_info)


def extract_order_id_from_txn_id_or_fulfillment_id(txn_id: str) -> str:
    """
    Extract order_id from txn_id, fulfillment_id, or transaction_id by removing suffix patterns.

    Examples:
    - 5c8e3f9bff064048ac46b98e04ea75c2 → 5c8e3f9bff064048ac46b98e04ea75c2 (order ID, no change)
    - 5c8e3f9bff064048ac46b98e04ea75c2-f1 → 5c8e3f9bff064048ac46b98e04ea75c2
    - 5c8e3f9bff064048ac46b98e04ea75c2-f1-t1 → 5c8e3f9bff064048ac46b98e04ea75c2
    - 5c8e3f9bff064048ac46b98e04ea75c2-f1-t2 → 5c8e3f9bff064048ac46b98e04ea75c2
    """
    # Remove transaction suffix (-t\d+)
    input_id = re.sub(r"-t\d+$", "", txn_id)
    
    # Remove fulfillment suffix (-f\d+)
    input_id = re.sub(r"-f\d+$", "", input_id)
    
    return input_id


async def get_payout_order_details_juspay(payload: dict, meta_info: dict) -> dict:
    """
    Calls the Juspay Portal API to retrieve detailed information for a specific payout order.
    Note: The API returns the amount in major or primary currency unit (e.g., rupees, dollars).

    IMPORTANT: If you receive an error like "Could not find resource: Order abc", the provided ID might be a fulfillment ID or transaction ID instead of an order ID. In such cases, you should extract the order_id using these patterns:

    Supported ID patterns:
    - Order ID: 5c8e3f9bff064048ac46b98e04ea75c2 → 5c8e3f9bff064048ac46b98e04ea75c2 (no change)
    - Fulfillment ID: 5c8e3f9bff064048ac46b98e04ea75c2-f1 → 5c8e3f9bff064048ac46b98e04ea75c2
    - Transaction ID: 5c8e3f9bff064048ac46b98e04ea75c2-f1-t1 → 5c8e3f9bff064048ac46b98e04ea75c2
    - Transaction ID: 5c8e3f9bff064048ac46b98e04ea75c2-f1-t2 → 5c8e3f9bff064048ac46b98e04ea75c2

    Pattern extraction process:
    1. Remove transaction suffix (-t\d+) if present
    2. Remove fulfillment suffix (-f\d+) if present
    3. Return the base order ID

    If the first attempt fails with "Could not find resource" error, the function automatically extracts the order_id using the above patterns and retries the call.
    
    Args:
        payload (dict): A dictionary containing:
            - order_id: The unique order ID to retrieve details for (can also be a fulfillment_id or transaction_id that will be automatically processed if the first attempt fails)

    Returns:
        dict: The parsed JSON response containing comprehensive payout order details including:
            - Order-level information: status, amount, customer details, timestamps
            - Fulfillment details: status, methods, currency, beneficiary information
            - Transaction information: gateway references, status codes, response messages
            - Beneficiary details: account information, IFSC codes, beneficiary type

    Raises:
        ValueError: If 'order_id' is missing from the payload.
        Exception: If the API call fails.
    """
    order_id = payload.get("order_id")
    if not order_id:
        raise ValueError("'order_id' is required in the payload")

    host = await get_juspay_host_from_api(meta_info=meta_info)

    additional_headers = make_payout_additional_headers(meta_info)

    api_url = f"{host}/api/payout/batch/dashboard/v1/orders/{order_id}?expand=fulfillment"

    try:
        logging.info(f"Attempting to get order details for order_id: {order_id}")
        return await call(api_url, additional_headers=additional_headers, meta_info=meta_info)

    except Exception as e:
        error_str = str(e)
        logging.warning(f"First attempt failed: {error_str}")

        if "Could not find" in error_str:

            extracted_order_id = extract_order_id_from_txn_id_or_fulfillment_id(order_id)

            if extracted_order_id != order_id:
                logging.info(f"Retrying with extracted order_id: {extracted_order_id}")
                try:
                    retry_api_url = f"{host}/api/payout/batch/dashboard/v1/orders/{extracted_order_id}?expand=fulfillment"
                    result = await call(retry_api_url, additional_headers=additional_headers, meta_info=meta_info)
                    logging.info(
                        f"Success with extracted order_id: {extracted_order_id}"
                    )
                    return result
                except Exception as retry_error:
                    logging.error(f"Retry also failed: {str(retry_error)}")
                    raise e
            else:
                logging.info("Extracted order_id same as original, not retrying")
                raise e
        else:
            raise e
