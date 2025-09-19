# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from datetime import datetime, timezone
from juspay_dashboard_mcp.api.utils import post, get_juspay_host_from_api, call, ist_to_utc
from urllib.parse import urlencode
from juspay_dashboard_mcp.config import get_common_headers
from juspay_dashboard_mcp.api_schema.orders import FlatFilter, Clause
from typing import Dict, Any
import os
import dotenv
import re
import logging

dotenv.load_dotenv()


def flat_filter_to_tree(flat: FlatFilter) -> Dict[str, Any]:
    """
    Convert a FlatFilter (with .clauses: List[Clause], .logic: string like "(0 AND 1 AND 2)")
    into a nested AND/OR tree of plain dicts.
    """
    from pydantic import BaseModel

    def clause_to_dict(clause: Clause) -> Dict[str, Any]:
        val = clause.val
        if isinstance(val, BaseModel):
            val = val.model_dump(mode="json")

        field = clause.field
        if field.startswith("udf"):
            field = f"full_{field}"
        if field == "card_bin":
            field = "original_card_isin"

        return {
            "field": field,
            "condition": clause.condition,
            "val": val,
        }

    clauses = flat.clauses
    tokens = re.split(r"\s+(AND|OR)\s+", flat.logic)
    cleaned = [tok.strip("()") for tok in tokens if tok.strip("()") != ""]

    current = clause_to_dict(clauses[int(cleaned[0])])

    i = 1
    while i < len(cleaned):
        op = cleaned[i].lower()  
        idx = int(cleaned[i + 1])  
        right = clause_to_dict(clauses[idx])
        current = {op: {"left": current, "right": right}}
        i += 2

    return current


def determine_domain_from_filters(flat_filters: FlatFilter) -> str:
    """
    Determine the appropriate domain based on the flatFilters.
    If any filter field belongs to txnsELS domain, return 'txnsELS'.
    Otherwise, return 'ordersELS'.
    
    Args:
        flat_filters: FlatFilter object containing the filter clauses
        
    Returns:
        str: Either 'txnsELS' or 'ordersELS'
    """
    # Fields that belong to txnsELS domain
    txns_els_fields = {
        "payment_status",
        "order_amount", 
        "card_brand",
        "auth_type",
        "is_cvv_less_txn",
        "emi",
        "emi_bank",
        "emi_type",
        "emi_tenure",
        "payment_method_type",
        "source_object",
        "error_code",
        "error_message",
        "error_category",
        "gateway_reference_id",
        "payment_gateway",
        "bank",
        "date_created",
        "epg_txn_id",
        "card_exp_month",
        "card_exp_year",
        "card_issuer_country",
        "card_bin",
        "card_last_four_digits",
        "is_upicc",
        "resp_message",
        "mandate_frequency",
        "platform",
        "txn_uuid",
        "pgr_rrn"
    }
    
    # Check if any clause uses a txnsELS field
    for clause in flat_filters.clauses:
        if clause.field in txns_els_fields:
            return "txnsELS"
    
    # If no txnsELS fields found, use ordersELS
    return "ordersELS"


async def find_orders_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Calls the Juspay Portal API to retrieve a list of orders within a specified time range.

    Args:
        payload (dict): A dictionary containing:
            - dateFrom: Start date/time in ISO format (e.g., '2025-04-15T18:30:00Z')
            - dateTo: End date/time in ISO format (e.g., '2025-04-16T15:06:00Z')
            - offset: Pagination offset (optional, default 0)
            - domain: Domain for query. If 'findorders', will be automatically determined based on filters
            - paymentStatus: Optional filter for payment status
            - orderType: Optional filter for order type
            - flatFilters: Optional flat filter structure that gets converted to qFilters

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

    date_from_str = ist_to_utc(date_from_str)
    date_to_str = ist_to_utc(date_to_str)

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

    # Handle domain aliasing
    domain = payload.get("domain", "txnsELS")
    if domain == "findorders":
        if payload.get("flatFilters"):
            try:
                flat_filters = FlatFilter(**payload["flatFilters"])
                domain = determine_domain_from_filters(flat_filters)
                logging.info(f"Domain aliasing: 'findorders' resolved to '{domain}' based on filters")
            except Exception as e:
                logging.warning(f"Failed to parse flatFilters for domain resolution: {e}")
                domain = "txnsELS"  
        else:
            domain = "ordersELS"  
            logging.info("Domain aliasing: 'findorders' resolved to 'ordersELS' (no filters)")

    time_field = "order_created_at" if domain == "ordersELS" else "date_created"

    if payload.get("flatFilters"):
        try:
            enhanced_clauses = [
                Clause(
                    field=time_field,
                    condition="GreaterThanEqual",
                    val=str(date_from_ts),
                ),
                Clause(
                    field=time_field,
                    condition="LessThanEqual",
                    val=str(date_to_ts),
                ),
            ]

            original_clauses = payload["flatFilters"]["clauses"]
            enhanced_clauses.extend(original_clauses)

            original_logic = payload["flatFilters"]["logic"]

            def shift_indices(match):
                return str(int(match.group(0)) + 2)

            shifted_logic = re.sub(r"\d+", shift_indices, original_logic)
            enhanced_logic = f"0 AND 1 AND ({shifted_logic})"

            enhanced_flat_filter = FlatFilter(
                clauses=enhanced_clauses, logic=enhanced_logic
            )

            qFilters = flat_filter_to_tree(enhanced_flat_filter)

        except Exception as e:
            raise ValueError(f"Invalid flatFilters format: {str(e)}")
    else:
        if domain == "ordersELS":
            qFilters = {
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
            }
        else:
            qFilters = {
                "and": {
                    "right": {
                        "field": "date_created",
                        "condition": "LessThanEqual",
                        "val": str(date_to_ts),
                    },
                    "left": {
                        "field": "date_created",
                        "condition": "GreaterThanEqual",
                        "val": str(date_from_ts),
                    },
                }
            }

    request_data = {
        "offset": payload.get("offset", 0),
        "filters": {"dateCreated": {"lte": date_to_str, "gte": date_from_str}},
        "order": [["date_created", "DESC"]],
        "qFilters": qFilters,
        "domain": domain,  # Use the resolved domain
        "sortDimension": "order_created_at",
    }

    host = await get_juspay_host_from_api(meta_info=meta_info)
    api_url = f"{host}/ec/v4/orders"
    return await post(api_url, request_data, None, meta_info)


def extract_order_id_from_txn_id(txn_id: str) -> str:
    """
    Extract order_id from txn_id by removing suffix patterns.

    Examples:
    - creditmantri-22087705-1 → 22087705
    - paypal-juspay-JP_1752481545-1 → JP_1752481545
    - zee5-6a45de15-6edd-4463-9415-f638a6709ee8-1 → 6a45de15-6edd-4463-9415-f638a6709ee8
    """
    pattern = r"-\d+(?:-\d+)?$"
    without_suffix = re.sub(pattern, "", txn_id)

   
    if without_suffix.startswith("zee5-"):
        return without_suffix[5:]  

    else :
        parts = without_suffix.split("-")
        without_suffix = parts[-1] if len(parts) > 1 else without_suffix
        
    return without_suffix


async def get_order_details_juspay(payload: dict, meta_info: dict) -> dict:
    """
    Calls the Juspay Portal API to retrieve detailed information for a specific order.
     Note: The api returns the amount in major or primary currency unit (e.g., rupees, dollars).

    IMPORTANT: If you receive an error like "Order with id = 'xyz' does not exist", the provided ID might be a transaction ID (txn_id) instead of an order ID. In such cases, you should extract the order_id from the txn_id using these patterns:

    Common txn_id to order_id patterns:
    - Standard pattern: merchant-orderID-retryCount → orderID
      Example: paypal-juspay-JP_1752481545-1 → JP_1752481545
    - Multiple hyphens in order ID: merchant-orderID-with-hyphens-retryCount → orderID-with-hyphens
      Example: zee5-6a45de15-6edd-4463-9415-f638a6709ee8-1 → 6a45de15-6edd-4463-9415-f638a6709ee8
    - Non-standard merchant prefix: prefix-orderID-retryCount → orderID
      Example: 6E-JFTWE26E7250714112817-1 → JFTWE26E7250714112817 (GoIndigo)
    - Silent retries: merchant-orderID-retryCount-silentRetryCount → orderID
      Example: merchant-ORDER123-1-1 → ORDER123

    Pattern recognition guide:
    1. Remove the last numeric suffix (e.g., -1, -2, etc.)
    2. If there's still a numeric suffix, remove it too (for silent retries)
    3. Take the part after the merchant prefix (usually after the first or second hyphen)
    4. Some merchants like zee5 have hyphens within their order IDs, so be careful to preserve the order ID structure

    If the first attempt fails with "does not exist" error, extract the order_id using the above patterns and retry the call.
    
    Args:
        payload (dict): A dictionary containing:
            - order_id: The unique order ID to retrieve details for (can also be a txn_id that will be automatically processed if the first attempt fails)

    Returns:
        dict: The parsed JSON response containing order details.

    Raises:
        Exception: If the API call fails.
    """
    order_id = payload.get("order_id")
    if not order_id:
        raise ValueError("'order_id' is required in the payload")

    host = await get_juspay_host_from_api(meta_info=meta_info)

    api_url = f"{host}/api/ec/v1/orders/{order_id}"

    try:
        logging.info(f"Attempting to get order details for order_id: {order_id}")
        return await post(api_url, {}, None, meta_info)

    except Exception as e:
        error_str = str(e)
        logging.warning(f"First attempt failed: {error_str}")

        if "does not exist" in error_str or "invalid_request_error" in error_str:

            extracted_order_id = extract_order_id_from_txn_id(order_id)

            if extracted_order_id != order_id:
                logging.info(f"Retrying with extracted order_id: {extracted_order_id}")
                try:
                    retry_api_url = f"{host}/api/ec/v1/orders/{extracted_order_id}"
                    result = await post(retry_api_url, {}, None, meta_info)
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
