# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import asyncio
import json
from pydantic import Field
import httpx
import logging
import os
from datetime import datetime

from juspay_dashboard_mcp.api_schema.qapi import (
    DimensionList,
    Filter,
    Interval,
    Metric,
    SortedOn,
    QApiResponse,
    QApiSuccessResponse,
    QApiErrorResponse,
    QApiPayload,
)
from juspay_dashboard_mcp.config import JUSPAY_BASE_URL, get_common_headers
from juspay_dashboard_mcp.api.utils import get_juspay_credentials
from juspay_dashboard_mcp.api.qapi_info import validate_schema_signature, get_domain_fields, DOMAIN_METRICS, DOMAIN_TIMESTAMP_COLUMNS
from juspay_mcp.log_safe import safe_exc, safe_url

logger = logging.getLogger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles datetime objects by converting them to ISO format strings.
    """

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%dT%H:%M:%SZ")
        return super().default(obj)


def json_dumps_with_datetime(obj):
    """
    Serialize obj to a JSON formatted string with datetime support.
    """
    return json.dumps(obj, cls=DateTimeEncoder)


async def call_query_api(payload: QApiPayload, meta_info: dict = None) -> dict:
    """
    Utility function to call the query API with the provided payload.
    Uses httpx.AsyncClient for async HTTP requests.
    Resolves credentials via context var first, then meta_info, then env var fallback.
    """
    serialized_payload = {}
    try:
        serialized_payload["domain"] = payload.domain
        serialized_payload["metric"] = payload.metric

        serialized_payload["interval"] = {
            "start": payload.interval.start,
            "end": payload.interval.end,
        }

        if payload.filters:
            serialized_payload["filters"] = payload.filters.model_dump(
                mode="json", by_alias=True
            )

        serialized_payload["dimensions"] = (
            payload.dimensions.model_dump(mode="json", by_alias=True)
            if payload.dimensions
            else []
        )

        if payload.sortedOn:
            serialized_payload["sortedOn"] = payload.sortedOn.model_dump(
                mode="json", by_alias=True
            )

        juspay_creds = get_juspay_credentials()
        headers = get_common_headers({}, meta_info, juspay_creds)
        headers["Content-Type"] = "application/json"

        api_url = f"{JUSPAY_BASE_URL}/api/q/query"
        logging.info(f"QAPI Call: url={safe_url(api_url)}")

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                api_url,
                content=json_dumps_with_datetime(serialized_payload),
                headers=headers,
            )
        logging.info(f"QAPI Response: status={response.status_code} bytes={len(response.content)}")
        response.raise_for_status()

        response_json = [json.loads(line) for line in response.text.splitlines()]
        validated_response = QApiSuccessResponse.model_validate(response_json)
        logging.info(f"QAPI Return: parsed {len(response_json)} response line(s)")
        return validated_response.dict()
    except Exception as e:
        logging.error(f"Error calling query API: {safe_exc(e)}")
        return QApiErrorResponse(
            error=f"Failed to execute query: {str(e)}",
            payload_attempted=serialized_payload or payload.model_dump(),
        ).dict()


# The six in the tool schema, plus Equals/NotEquals, which the query engine accepts
# (verified live) and which nested and/or filters have always been able to use.
_FILTER_CONDITIONS = {"In", "NotIn", "Greater", "GreaterThanEqual", "LessThanEqual", "Less", "Equals", "NotEquals"}
_MAX_FILTER_DEPTH = 10
_MAX_FILTER_CONDITIONS = 30
_MAX_FILTER_VALUES = 200
_MAX_DIMENSIONS = 10


def validate_query_structure(domain: str, filters, dimensions, sorted_on, allowed_dimensions: set, allowed_filter_fields: set) -> str | None:
    """Check a query's filter tree and dimensions against what qapi_info offered.

    `filters` / `dimensions` / `sorted_on` are the serialized (plain dict/list) forms.
    Returns an error message, or None if the query is acceptable. When qapi_info
    offered no field names at all, field-name checks are skipped (operator, size
    and shape checks still apply).
    """
    ts_col = DOMAIN_TIMESTAMP_COLUMNS.get(domain, DOMAIN_TIMESTAMP_COLUMNS["default"])
    metrics = set(DOMAIN_METRICS.get(domain, []))
    filterable = allowed_dimensions | allowed_filter_fields | metrics | {ts_col}
    groupable = allowed_dimensions | {ts_col}

    have_fields = bool(allowed_dimensions or allowed_filter_fields)
    count = 0

    def walk(node, depth):
        nonlocal count
        if depth > _MAX_FILTER_DEPTH:
            return f"Filter is nested too deeply (max {_MAX_FILTER_DEPTH} levels)."
        if not isinstance(node, dict):
            return "Each filter must be an object."
        if len(node) == 1 and next(iter(node)) in ("and", "or"):
            body = node[next(iter(node))]
            if not isinstance(body, dict) or set(body) != {"left", "right"}:
                return "'and'/'or' filters must have exactly 'left' and 'right'."
            return walk(body["left"], depth + 1) or walk(body["right"], depth + 1)
        if set(node) - {"field", "condition", "val"} or "field" not in node or "condition" not in node:
            return "A filter must have 'field', 'condition' and 'val' only."
        count += 1
        if count > _MAX_FILTER_CONDITIONS:
            return f"Too many filter conditions (max {_MAX_FILTER_CONDITIONS})."
        if node["condition"] not in _FILTER_CONDITIONS:
            return f"Unknown filter condition '{str(node['condition'])[:40]}'. Allowed: {sorted(_FILTER_CONDITIONS)}."
        if have_fields and node["field"] not in filterable:
            return f"Filter field '{str(node['field'])[:60]}' is not offered by qapi_info for domain '{domain}'."
        val = node.get("val")
        if isinstance(val, list) and len(val) > _MAX_FILTER_VALUES:
            return f"Too many filter values (max {_MAX_FILTER_VALUES})."
        return None

    if filters:
        err = walk(filters, 1)
        if err:
            return err

    dims = dimensions or []
    if len(dims) > _MAX_DIMENSIONS:
        return f"Too many dimensions (max {_MAX_DIMENSIONS})."
    for d in dims:
        if isinstance(d, str):
            name = d
        elif isinstance(d, dict) and isinstance(d.get("intervalCol"), str):
            name = d["intervalCol"]
        else:
            return "Each dimension must be a field name or a time-granularity object."
        if have_fields and name not in groupable:
            return f"Dimension '{name[:60]}' is not offered by qapi_info for domain '{domain}'."
    return None


async def q_api(payload: dict, meta_info: dict = None) -> QApiResponse:
    """
    Tool for querying data from the analytics API.
    Requires schema_signature from qapi_info.

    Args:
       payload dict which contains all the below fields in it:
        schema_signature: Signature from qapi_info (REQUIRED)
        domain: Analytics domain
        interval: Time interval for the query (UTC)
        metric: Metric to query
        dimensions: Dimensions to include
        filters: Filters to apply
        sortedOn: Sorting criteria

    Returns:
        QApiResponse with the query results
    """
    domain = payload.get("domain", "kvorders")
    schema_signature = payload.get("schema_signature")
    metric = payload.get("metric")
    interval = payload.get("interval")
    dimensions = payload.get("dimensions")
    filters = payload.get("filters")
    sortedOn = payload.get("sortedOn")

    # Validate schema_signature FIRST - this ensures qapi_info was called
    is_valid, error_msg = await validate_schema_signature(schema_signature, domain, meta_info)
    if not is_valid:
        return {
            "error": error_msg,
            "retry": True,
            "action_required": f"Call qapi_info(domain='{domain}') first, then pass the returned schema_signature to this tool.",
            "suggested_tool": "qapi_info",
            "suggested_params": {"domain": domain}
        }

    logging.info(
        "QAPI Tool Input: domain=%s metric=%s has_interval=%s has_dimensions=%s has_filters=%s has_sort=%s",
        str(domain)[:50], str(metric)[:50], bool(interval), bool(dimensions), bool(filters), bool(sortedOn),
    )
    # Construct the payload using the QApiPayload model with proper types
    q_api_payload = QApiPayload(
        domain=domain,
        metric=metric,
        interval=interval,
        filters=filters,
        dimensions=dimensions,
        sortedOn=sortedOn,
    )

    fields = await get_domain_fields(domain, meta_info)
    if fields is None:
        return {
            "error": f"Could not load the allowed fields for domain '{domain}'. Call qapi_info and retry.",
            "retry": True,
            "suggested_tool": "qapi_info",
            "suggested_params": {"domain": domain},
        }
    structure_error = validate_query_structure(
        domain,
        q_api_payload.filters.model_dump(mode="json", by_alias=True) if q_api_payload.filters else None,
        q_api_payload.dimensions.model_dump(mode="json", by_alias=True) if q_api_payload.dimensions else [],
        q_api_payload.sortedOn,
        fields[0],
        fields[1],
    )
    if structure_error:
        return {
            "error": f"INVALID_QUERY: {structure_error}",
            "retry": True,
            "action_required": f"Use only fields returned by qapi_info(domain='{domain}').",
            "suggested_tool": "qapi_info",
            "suggested_params": {"domain": domain},
        }

    return await call_query_api(q_api_payload, meta_info)
