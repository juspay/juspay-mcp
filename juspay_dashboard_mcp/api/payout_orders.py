# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from datetime import datetime, timezone
from juspay_dashboard_mcp.api.utils import call, get_juspay_host_from_api, ist_to_utc, make_payout_additional_headers, post
from urllib.parse import quote, urlencode
from juspay_dashboard_mcp.config import get_common_headers
from typing import Dict, Any
import os
import dotenv
import re
import logging

dotenv.load_dotenv()

COMMON_CREATE_PAYOUT_ORDER_FIELDS = {
    "orderId",
    "beneType",
    "amount",
    "customerId",
    "customerPhone",
    "customerEmail",
    "orderType",
    "preferredMethodList",
    "udf1",
    "udf2",
    "udf3",
    "udf4",
    "udf5",
    "scheduleTime",
    "fulfillmentCurrency",
    "sourceCurrency",
    "idempotencyKey",
    "tenant_id",
    "juspay_meta_info",
}

BENE_TYPE_FIELD_RULES = {
    "CARD": {
        "required": {"beneCardReference", "beneBankCode", "beneCardType", "beneBrand"},
        "allowed": {"beneName", "beneCardReference", "beneBankCode", "beneCardType", "beneBrand", "payeeAdditionalDetails"},
    },
    "PLAIN_CARD": {
        "required": {"beneBankCode", "beneCardType", "beneBrand"},
        "allowed": {"beneName", "beneBankCode", "beneCardType", "beneBrand", "last4ofCard", "payeeAdditionalDetails"},
    },
    "ACCOUNT_IFSC": {
        "required": {"beneAccount", "beneIfsc"},
        "allowed": {"beneName", "beneAccount", "beneIfsc", "beneLegalEntityIdentifier", "payeeAdditionalDetails"},
    },
    "UPI_ID": {
        "required": {"beneVpa"},
        "allowed": {"beneName", "beneVpa", "payeeAdditionalDetails"},
    },
    "WALLET": {
        "required": {"beneWalletBrand"},
        "allowed": {"beneWalletIdentifier", "beneWalletBrand", "beneWalletIdentifierType", "payeeAdditionalDetails"},
    },
    "BENE_ID": {
        "required": {"beneId"},
        "allowed": {"beneName", "beneId", "payeeAdditionalDetails"},
    },
    "PAYOUT_LINK": {
        "required": {"beneMobileNo"},
        "allowed": {"beneName", "beneMobileNo"},
    },
}


def make_payout_approval_url(host: str, merchant_order_id: str) -> str:
    """Build the Portal URL for approving a payout order."""
    if not host:
        raise ValueError("A resolved Juspay host is required.")
    if not merchant_order_id:
        raise ValueError("The payload must include 'merchantOrderId'.")
    return f"{host.rstrip('/')}/payout-maker-checker/{quote(str(merchant_order_id), safe='')}"


async def get_payout_approval_link(payload: dict, meta_info: dict = None) -> dict:
    """Returns the Portal link for approving a maker-checker payout order."""
    merchant_order_id = payload.get("merchantOrderId")
    host = await get_juspay_host_from_api(meta_info=meta_info)
    return {
        "merchantOrderId": merchant_order_id,
        "approvalUrl": make_payout_approval_url(host, merchant_order_id),
    }


def make_flat_payout_order_payload(payload: dict) -> dict:
    bene_type = payload.get("beneType")
    rules = BENE_TYPE_FIELD_RULES.get(bene_type)
    if not rules:
        raise ValueError(f"Unsupported beneType: {bene_type}")

    missing_fields = [field for field in rules["required"] if not payload.get(field)]
    if missing_fields:
        raise ValueError(f"Missing required fields for beneType {bene_type}: {missing_fields}")

    allowed_fields = COMMON_CREATE_PAYOUT_ORDER_FIELDS | rules["allowed"]
    request_payload = {
        key: value
        for key, value in payload.items()
        if key in allowed_fields and value is not None
    }
    request_payload["orderType"] = request_payload.get("orderType") or "APPROVE_AND_FULFILL_ONLY"
    return request_payload


async def create_payout_order(payload: dict, meta_info: dict = None) -> dict:
    """
    Creates a payout order from the dashboard MCP using the dashboard payout API.
    """
    required_fields = [
        "orderId",
        "beneType",
        "amount",
        "customerId",
        "customerPhone",
        "customerEmail",
    ]

    for field in required_fields:
        if not payload.get(field):
            raise ValueError(f"The payload must include '{field}'.")

    request_payload = make_flat_payout_order_payload(payload)

    host = await get_juspay_host_from_api(meta_info=meta_info)
    additional_headers = make_payout_additional_headers(meta_info)
    api_url = f"{host}/api/payout/batch/dashboard/v1/orders"
    response = await post(api_url, request_payload, additional_headers=additional_headers, meta_info=meta_info)
    merchant_order_id = response.get("merchantOrderId") or payload["orderId"]
    return {
        **response,
        "approvalUrl": make_payout_approval_url(host, merchant_order_id),
    }


async def list_payout_orders(payload: dict, meta_info: dict = None) -> dict:
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


async def get_payout_order_details(payload: dict, meta_info: dict) -> dict:
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
    1. Remove transaction suffix (-t\\d+) if present
    2. Remove fulfillment suffix (-f\\d+) if present
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
