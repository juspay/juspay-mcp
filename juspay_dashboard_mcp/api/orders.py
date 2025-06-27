# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from datetime import datetime, timezone
from juspay_dashboard_mcp.api.utils import post, get_juspay_host_from_api, call
from urllib.parse import urlencode
from juspay_dashboard_mcp.config import get_common_headers
from juspay_dashboard_mcp.api_schema.orders import FlatFilter, Clause
from typing import Dict, Any
import os
import dotenv
import re

dotenv.load_dotenv()


def flat_filter_to_tree(flat: FlatFilter) -> Dict[str, Any]:
    """
    Convert a FlatFilter (with .clauses: List[Clause], .logic: string like "(0 AND 1 AND 2)")
    into a nested AND/OR tree of plain dicts.
    """
    from pydantic import BaseModel

    def clause_to_dict(clause: Clause) -> Dict[str, Any]:
        val = clause.val
        # If it's a Pydantic model, dump it to primitives:
        if isinstance(val, BaseModel):
            val = val.model_dump(mode="json")
        return {
            "field": clause.field,
            "condition": clause.condition,
            "val": val,
        }

    clauses = flat.clauses
    # split on AND/OR, keep the operators
    tokens = re.split(r"\s+(AND|OR)\s+", flat.logic)
    # tokens might be e.g. ["(0", "AND", "1)", "OR", "2"]
    # strip parentheses from each token
    cleaned = [tok.strip("()") for tok in tokens if tok.strip("()") != ""]
    # cleaned = ["0", "AND", "1", "OR", "2"]

    # start with the first clause
    current = clause_to_dict(clauses[int(cleaned[0])])

    # fold left-associatively over the rest
    i = 1
    while i < len(cleaned):
        op = cleaned[i].lower()  # "and" or "or"
        idx = int(cleaned[i + 1])  # next clause index
        right = clause_to_dict(clauses[idx])
        current = {op: {"left": current, "right": right}}
        i += 2

    return current


async def list_orders_v4_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Calls the Juspay Portal API to retrieve a list of orders within a specified time range.

    Args:
        payload (dict): A dictionary containing:
            - dateFrom: Start date/time in ISO format (e.g., '2025-04-15T18:30:00Z')
            - dateTo: End date/time in ISO format (e.g., '2025-04-16T15:06:00Z')
            - offset: Pagination offset (optional, default 0)
            - domain: Domain for query (default 'txnsELS')
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

    time_field = (
        "order_created_at" if payload.get("domain") == "ordersELS" else "date_created"
    )

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
        if payload.get("domain") and payload["domain"] == "ordersELS":
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
        "filters": {
            "dateCreated": {
                "lte": date_to_str,
                "gte": date_from_str
            }
        },
        "order": [["date_created", "DESC"]],
        "qFilters": qFilters,
        "domain": payload.get("domain", "txnsELS"),
        "sortDimension": "order_created_at",
    }

    host = await get_juspay_host_from_api(meta_info=meta_info)
    api_url = f"{host}/ec/v4/orders"
    return await post(api_url, request_data, None, meta_info)


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

    host = await get_juspay_host_from_api(meta_info=meta_info)
    api_url = f"{host}/api/ec/v1/orders/{order_id}"
    return await post(api_url, {}, None, meta_info)
