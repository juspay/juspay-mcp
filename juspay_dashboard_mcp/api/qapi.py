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
from juspay_dashboard_mcp.api.qapi_info import validate_schema_signature

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
        logging.info(f"QAPI Call: url={api_url} payload={serialized_payload}")

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                api_url,
                content=json_dumps_with_datetime(serialized_payload),
                headers=headers,
            )
        logging.info(f"QAPI Response Raw: {response.text}")
        response.raise_for_status()

        response_json = [json.loads(line) for line in response.text.splitlines()]
        validated_response = QApiSuccessResponse.model_validate(response_json)
        logging.info(f"QAPI Return: Parsed response: {validated_response}")
        return validated_response.dict()
    except Exception as e:
        logging.error(f"Error calling query API: {str(e)}")
        return QApiErrorResponse(
            error=f"Failed to execute query: {str(e)}",
            payload_attempted=serialized_payload or payload.model_dump(),
        ).dict()


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
    is_valid, error_msg = validate_schema_signature(schema_signature, domain)
    if not is_valid:
        return {
            "error": error_msg,
            "retry": True,
            "action_required": f"Call qapi_info(domain='{domain}') first, then pass the returned schema_signature to this tool.",
            "suggested_tool": "qapi_info",
            "suggested_params": {"domain": domain}
        }

    logging.info(
        f"QAPI Tool Input: Domain={domain}, Interval={interval}, Metric={metric}, Dimensions={dimensions}, Filters={filters}, SortedOn={sortedOn}"
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

    # Log the payload for debugging
    logging.debug(f"QAPI Tool: Creating payload: {json.dumps(q_api_payload.model_dump())}")

    return await call_query_api(q_api_payload, meta_info)
