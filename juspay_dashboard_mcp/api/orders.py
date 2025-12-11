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

logger = logging.getLogger(__name__)

# Field aliases: {array_key: {original_field: alias_field}}
# Add new aliases here as needed to make field names more LLM-friendly
FIELD_ALIASES = {
    "webhooks": {"isWebHookNotified": "merchant_accepted_webhook"},
}


def _apply_aliases(data: Dict[str, Any]) -> Dict[str, Any]:
    """Apply configured field aliases to order response (replaces original field).
    
    This function iterates through the FIELD_ALIASES configuration and replaces
    original field names with their aliases in the API response. This makes
    field names more understandable for LLMs processing the response.
    
    Args:
        data: The API response dictionary to process
        
    Returns:
        The processed dictionary with field names replaced according to FIELD_ALIASES
    """
    if not data:
        return data
    for key, mappings in FIELD_ALIASES.items():
        if isinstance(data.get(key), list):
            for item in data[key]:
                if isinstance(item, dict):
                    for orig, alias in mappings.items():
                        if orig in item:
                            value = item.pop(orig)  # Remove original
                            item[alias] = value     # Add with new name
                            logger.info(f"[FIELD_ALIAS] Replaced: {key}.{orig} -> {alias} (value={value})")
    return data


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
    # Check if flatFilters are present and validate that find_orders_field_value_discovery was called
    if payload.get("flatFilters"):
        tool_calls = []
        if meta_info and meta_info.get("tool_calls"):
            tool_calls = meta_info.get("tool_calls", [])
        
        # Check if find_orders_field_value_discovery was called
        field_discovery_called = any(
            tool_call.get("tool_name") == "find_orders_field_value_discovery" 
            for tool_call in tool_calls
        )
        if not field_discovery_called:
            raise ValueError(
                "Please call the 'find_orders_field_value_discovery' tool first to validate the filter values" 
            )
    
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


def extract_order_id_candidates(input_id: str) -> list[str]:
    """
    Generate multiple candidate order IDs from an ambiguous input.
    Returns list of candidates in priority order to try.
    
    Handles various patterns:
    - Small retry counts (≤ 25): AMEX-123-5 → tries [123, AMEX-123]
    - Large numbers: AMEX-123-999999 → tries [123, AMEX-123, AMEX-123-999999]
    - Silent retries: AMEX-123-5-2 → tries [123, AMEX-123]
    - Known prefixes: zee5-UUID-1 → tries [UUID, zee5-UUID]
    
    Examples:
    - creditmantri-22087705-1 → [22087705, creditmantri-22087705]
    - paypal-juspay-JP_1752481545-1 → [JP_1752481545, paypal-juspay-JP_1752481545]
    - zee5-6a45de15-6edd-4463-9415-f638a6709ee8-1 → [6a45de15-6edd-4463-9415-f638a6709ee8, ...]
    - AMEX-225531469-2249390 → [225531469-2249390, AMEX-225531469, 225531469, ...]
    """
    candidates = []
    
    # Strategy 1: Remove small retry counts (≤ 25)
    # Pattern: something-123-5 where 5 ≤ 25
    match = re.search(r'-(\d+)$', input_id)
    if match and int(match.group(1)) <= 25:
        without_last = re.sub(r'-\d+$', '', input_id)
        
        # Try after removing merchant prefix
        parts = without_last.split('-')
        if len(parts) > 1:
            # Last segment after merchant prefix
            candidates.append(parts[-1])
            # Everything after first segment (merchant prefix)
            candidates.append('-'.join(parts[1:]))
    
    # Strategy 2: Remove TWO numeric suffixes (for silent retries)
    # Pattern: something-123-5-2 (remove both -5-2 or just -5-2)
    double_suffix = re.sub(r'-\d+-\d+$', '', input_id)
    if double_suffix != input_id:
        parts = double_suffix.split('-')
        if len(parts) > 1:
            candidates.append(parts[-1])
            candidates.append('-'.join(parts[1:]))
    
    # Strategy 3: Remove any numeric suffix regardless of size
    # For cases like AMEX-225531469-2249390 where 2249390 > 25
    without_any_suffix = re.sub(r'-\d+(?:-\d+)?$', '', input_id)
    if without_any_suffix != input_id:
        parts = without_any_suffix.split('-')
        if len(parts) > 1:
            # Full string without suffix
            candidates.append(without_any_suffix)
            # Last segment only
            candidates.append(parts[-1])
            # After first segment
            candidates.append('-'.join(parts[1:]))
    
    # Strategy 4: Handle known merchant prefixes specially
    known_prefixes = ['zee5-', 'AMEX-', '6E-', 'paypal-', 'creditmantri-']
    for prefix in known_prefixes:
        if input_id.lower().startswith(prefix.lower()):
            after_prefix = input_id[len(prefix):]
            # Remove any suffix from after_prefix
            clean = re.sub(r'-\d+(?:-\d+)?$', '', after_prefix)
            if clean:
                candidates.append(clean)
            break
    
    # Remove duplicates while preserving order
    seen = set()
    unique_candidates = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            unique_candidates.append(c)
    
    return unique_candidates


async def get_order_details_juspay(payload: dict, meta_info: dict) -> dict:
    """
    Calls the Juspay Portal API to retrieve detailed information for a specific order.
    Note: The api returns the amount in major or primary currency unit (e.g., rupees, dollars).

    This function accepts ANY ID format (order_id, txn_id, or ambiguous IDs) and has built-in 
    intelligent retry logic that automatically tries multiple extraction patterns if the initial 
    attempt fails.

    Args:
        payload (dict): A dictionary containing:
            - order_id: The unique order ID to retrieve details for. Can be:
                * Pure order ID (e.g., "22087705", "JP_1752481545")
                * Transaction ID (e.g., "creditmantri-22087705-1", "AMEX-225531469-2249390")
                * Any ambiguous ID format - the tool will try multiple patterns

    Returns:
        dict: The parsed JSON response containing order details.

    Raises:
        Exception: If the API call fails for all attempted patterns.
    """
    order_id = payload.get("order_id")
    if not order_id:
        raise ValueError("'order_id' is required in the payload")

    host = await get_juspay_host_from_api(meta_info=meta_info)
    
    # Attempt 1: Try original ID as-is
    api_url = f"{host}/api/ec/v1/orders/{order_id}"
    try:
        logging.info(f"[Attempt 1] Trying original ID: {order_id}")
        result = await post(api_url, {}, None, meta_info)
        return _apply_aliases(result)
    
    except Exception as e:
        error_str = str(e)
        logging.warning(f"[Attempt 1] Failed with original ID: {error_str}")
        
        # Only retry if it's a "not found" type error
        if "does not exist" in error_str or "invalid_request_error" in error_str:
            
            # Generate all candidate order IDs
            candidates = extract_order_id_candidates(order_id)
            
            if not candidates:
                logging.info("No extraction candidates generated, re-raising original error")
                raise e
            
            logging.info(f"Generated {len(candidates)} extraction candidates: {candidates}")
            
            # Try each candidate
            for idx, candidate in enumerate(candidates, start=2):
                try:
                    logging.info(f"[Attempt {idx}] Trying candidate: '{candidate}'")
                    retry_url = f"{host}/api/ec/v1/orders/{candidate}"
                    result = await post(retry_url, {}, None, meta_info)
                    logging.info(f"✓ SUCCESS with candidate: '{candidate}' (extracted from '{order_id}')")
                    return _apply_aliases(result)
                
                except Exception as retry_error:
                    retry_error_str = str(retry_error)
                    logging.debug(f"[Attempt {idx}] Candidate '{candidate}' failed: {retry_error_str}")
                    continue
            
            # All extraction attempts failed
            logging.error(f"All {len(candidates) + 1} attempts failed for ID: {order_id}")
            logging.error(f"Tried: ['{order_id}'] + {candidates}")
            raise e  # Re-raise original error
        
        else:
            # Different type of error, don't retry
            raise e
