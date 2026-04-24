# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import logging
from difflib import SequenceMatcher

import httpx

from juspay_dashboard_mcp.config import JUSPAY_BASE_URL, get_common_headers
from juspay_dashboard_mcp.api.utils import get_juspay_credentials

logger = logging.getLogger(__name__)

DOMAIN_METRICS: dict[str, list[str]] = {
    "kvorders": [
        "total_amount", "success_volume", "success_rate", "avg_ticket_size",
        "conflict_txn_rate", "average_latency", "order_with_transactions",
        "order_with_transactions_gmv", "new_order", "new_order_rate",
        "tp_50_latency", "tp_90_latency", "tp_95_latency", "tp_99_latency", "tp_100_latency",
    ],
    "kvrefundtxns": [
        "total_volume", "success_rate", "pending_rate", "total_amount",
        "manual_review_rate", "manual_review_count", "refund_pending_5days",
        "success_volume", "mean_turn_around_time", "refund_arn_availability_volume",
        "refund_arn_availability_rate", "complete_refunds_volume",
    ],
    "kvoffers": [
        "total_volume", "total_amount", "success_volume", "success_rate", "avg_ticket_size",
    ],
    "mandateexecutionkv": [
        "total_volume", "success_volume", "success_rate",
        "merchant_calls_notification_api", "notification_sent_to_pg",
        "notification_successful", "merchant_calls_txns", "mandate_execute_sent_to_pg",
        "notification_retried_count", "notification_retried_success_count",
        "notification_retried_success_rate", "mandate_execute_retried_count",
        "mandate_execute_retried_success_count", "mandate_execute_retried_success_rate",
        "mandate_execute_retried_failure_count", "mandate_execute_retried_failure_rate",
    ],
    "fulfillmentorders": [
        "total_volume", "success_volume", "success_rate", "processed_amount",
        "first_attempt_success_volume", "first_attempt_success_rate",
        "average_txn_latency", "average_order_latency", "failure_volume",
        "reversed_volume", "reversed_rate",
        "fulfillment_txn_latency_metric", "fulfillment_order_latency_metric",
    ],
    "sdklogs": [
        "total_volume", "success_volume", "total_order_volume", "success_rate", "conversion_rate",
    ],
    "kvcustomer": [
        "total_customers", "success_customers", "success_amount", "success_rate",
        "first_attempt_success_rate", "total_orders",
    ],
    "kvmandates": [
        "total_mandates", "expired_mandates", "revoked_mandates",
    ],
    "unauthtxns": [
        "total_amount", "success_volume", "success_rate", "order_with_transactions",
        "avg_ticket_size", "conflict_txn_rate", "new_order", "new_order_rate",
    ],
    "kvtxns": [
        "total_volume", "total_amount", "success_volume", "success_rate", "avg_ticket_size",
        "conflict_txn_rate", "average_latency", "offer_availed_rate",
        "saved_mandate_txns_volume", "saved_mandate_txns_amount",
        "saved_txns_volume", "saved_txns_amount",
        "saved_txns_amount_gateway", "saved_txns_volume_gateway",
        "started_txns_rate", "juspay_declined_txns_rate",
    ],
    "apirequests": [
        "total_volume", "status_2xx_rate", "status_4xx_rate", "status_5xx_rate",
    ],
}

DOMAIN_TIMESTAMP_COLUMNS: dict[str, str] = {
    "kvorders":           "order_created_at",
    "kvtxns":             "txn_initiated",
    "kvrefundtxns":       "refund_date",
    "kvoffers":           "offer_date_created",
    "mandateexecutionkv": "notification_date_created",
    "fulfillmentorders":  "fulfillment_created_at",
    "sdklogs":            "process_sdk_at",
    "unauthtxns":         "txn_initiated",
    "default":            "order_created_at",
}

HIGH_CARDINALITY_DIMENSIONS: set[str] = {
    "merchant_id", "error_message",
    "udf1", "udf2", "udf3", "udf4", "udf5", "udf6", "udf7", "udf8", "udf9", "udf10",
    "card_exp_year", "card_exp_month", "card_bin", "card_last_four_digits",
    "txn_last_updated", "order_source_object_id", "juspay_bank_code", "product_id",
    "original_card_isin", "juspay_error_message", "juspay_error_code",
    "juspay_response_message", "network_error_code", "resp_message", "resp_code",
    "prev_gateway_resp_message", "prev_gateway_resp_code",
    "previous_gateway_resp_message", "previous_gateway_resp_code",
    "customer_id", "customer_email", "customer_phone", "order_amount",
    "order_created_at", "date_created", "amount", "txn_uuid", "pgr_rrn", "epg_txn_id",
    "id", "order_id", "agent_id", "lead_id", "created_at", "updated_at", "product_name",
    "euler_order_id", "metadata", "euler_client_id", "reference_id1", "reference_id2",
}


def _get_headers(meta_info: dict = None) -> dict:
    juspay_creds = get_juspay_credentials()
    return get_common_headers({}, meta_info, juspay_creds)


async def qapi_info(payload: dict, meta_info: dict = None) -> dict:
    """
    Returns available dimensions, filters, and metrics for a given analytics domain.
    The Q-API info endpoint uses singular keys ("dimension", "filter") in its response;
    this handler normalises them to plural in the output.
    """
    domain = payload.get("domain", "kvorders")
    headers = _get_headers(meta_info)
    url = f"{JUSPAY_BASE_URL}/api/q/query?api=info&domain={domain}"

    dimensions: list = []
    filters: list = []
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            raw = resp.json()
            dimensions = raw.get("dimension", [])
            filters = raw.get("filter", [])
    except Exception as e:
        logger.error(f"qapi_info: API call failed for domain={domain}: {e}")

    return {
        "domain": domain,
        "dimensions": dimensions,
        "filters": filters,
        "metrics": DOMAIN_METRICS.get(domain, []),
    }


def _fuzzy_score(query: str, candidate) -> float:
    return SequenceMatcher(None, query.lower(), str(candidate).lower()).ratio()


async def qapi_field_value_discovery(payload: dict, meta_info: dict = None) -> dict:
    """
    Fuzzy field-value lookup for dimensions in a given analytics domain.
    For each requested dimension, fetches candidate values from Q-API and ranks them
    against the provided queries using SequenceMatcher similarity.
    """
    domain = payload.get("domain", "kvorders")
    requests_list = payload.get("requests", [])
    default_limit = payload.get("default_limit", 10)

    if default_limit > 50:
        return {"error": "default_limit cannot be greater than 50.", "results": []}

    headers = _get_headers(meta_info)

    # Fetch domain info to validate dimensions
    info_url = f"{JUSPAY_BASE_URL}/api/q/query?api=info&domain={domain}"
    info_dimensions: set[str] = set()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(info_url, headers=headers)
            resp.raise_for_status()
            raw = resp.json()
            info_dimensions = set(raw.get("dimension", []))
    except Exception as e:
        logger.error(f"qapi_field_value_discovery: failed to fetch info for domain={domain}: {e}")

    valid_metrics = set(DOMAIN_METRICS.get(domain, []))
    ts_col = DOMAIN_TIMESTAMP_COLUMNS.get(domain, DOMAIN_TIMESTAMP_COLUMNS["default"])
    supported_dimensions = info_dimensions - HIGH_CARDINALITY_DIMENSIONS

    results = []
    for req in requests_list:
        if isinstance(req, dict):
            dimension = req.get("dimension", "")
            queries = req.get("queries", [])
            max_res = req.get("max_results") or default_limit
        else:
            dimension = req.dimension
            queries = req.queries
            max_res = req.max_results or default_limit

        if dimension in valid_metrics:
            results.append({
                "dimension": dimension,
                "results": [],
                "unsupported_message": (
                    f"'{dimension}' is a metric, not a dimension. "
                    f"Use metric_filters in q_api to filter on metrics."
                ),
            })
            continue

        if dimension == ts_col:
            results.append({
                "dimension": dimension,
                "results": [],
                "unsupported_message": (
                    f"'{dimension}' is a timestamp column. "
                    f"Use a DimensionObject with granularity for time-based grouping."
                ),
            })
            continue

        if dimension not in supported_dimensions:
            if dimension in HIGH_CARDINALITY_DIMENSIONS:
                msg = (
                    f"'{dimension}' is a high-cardinality dimension not supported by "
                    f"field_value_discovery. Use the value directly in filters without validation."
                )
            else:
                sample = ", ".join(sorted(supported_dimensions)[:5])
                msg = (
                    f"'{dimension}' is not supported by field_value_discovery. "
                    f"Use the value directly in filters without validation. "
                    f"Sample supported dimensions: {sample}..."
                )
            results.append({"dimension": dimension, "results": [], "unsupported_message": msg})
            continue

        # Fetch candidate values from Q-API
        candidates: list = []
        try:
            fv_url = f"{JUSPAY_BASE_URL}/api/q/query?api=filters&domain={domain}&field={dimension}"
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(fv_url, headers=headers)
                resp.raise_for_status()
                raw_values = resp.json()
                candidates = [
                    c for c in (raw_values or [])
                    if isinstance(c, bool) or (isinstance(c, str) and c.strip())
                ]
        except Exception as e:
            logger.error(f"qapi_field_value_discovery: failed to fetch values for {dimension}: {e}")

        if not candidates:
            dim_results = [[] for _ in (queries or [None])]
        elif queries:
            dim_results = []
            for q in queries:
                ranked = sorted(candidates, key=lambda c: _fuzzy_score(q, c), reverse=True)
                dim_results.append(ranked[:max_res])
        else:
            dim_results = [candidates[:max_res]]

        # entire_payment_flow stores list-encoded strings — flatten them
        if dimension == "entire_payment_flow" and dim_results:
            flat: list = []
            seen: set = set()
            for lst in dim_results:
                for val in lst:
                    if isinstance(val, str) and val.startswith("[") and val.endswith("]"):
                        try:
                            parsed = eval(val)  # safe: known Q-API list format
                            items = parsed if isinstance(parsed, list) else [val]
                        except Exception:
                            items = [val]
                    else:
                        items = [val]
                    for item in items:
                        if item not in seen:
                            flat.append(item)
                            seen.add(item)
            dim_results = [flat]

        results.append({"dimension": dimension, "results": dim_results})

    return {"results": results}
