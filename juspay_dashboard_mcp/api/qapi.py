# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import asyncio
import json
from pydantic import Field
import requests
import logging
import os
from datetime import datetime, timedelta

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

def ist_to_utc(ist_time_string, format="%Y-%m-%dT%H:%M:%SZ"):
    """Convert IST time to UTC time.

    Args:
        ist_time_string: Can be either a string in format "%Y-%m-%dT%H:%M:%SZ" or a datetime object
        format: Output format for the returned timestamp

    Returns:
        A string in the specified format
    """
    try:
        # Handle both string and datetime inputs
        if isinstance(ist_time_string, datetime):
            ist_time = ist_time_string
        else:
            ist_time = datetime.strptime(ist_time_string, "%Y-%m-%dT%H:%M:%SZ")

        ist_offset = timedelta(hours=5, minutes=30)
        utc_time = ist_time - ist_offset

        # Check if the UTC time is exactly 18:29:00 and adjust if necessary
        if utc_time.time() == datetime.strptime("18:29:00", "%H:%M:%S").time():
            utc_time += timedelta(seconds=59)

        return utc_time.strftime(format)
    except Exception as e:
        logging.error(f"Error converting ist to utc: {str(e)}")
        # If it's already a datetime, try to return a formatted string
        if isinstance(ist_time_string, datetime):
            return ist_time_string.strftime(format)
        return str(ist_time_string)

def utc_to_ist(utc_time_string: str) -> str:
    try:
        # Try parsing with T separator first
        try:
            utc_time = datetime.strptime(utc_time_string, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            # If that fails, try parsing with space separator
            utc_time = datetime.strptime(utc_time_string, "%Y-%m-%d %H:%M:%S")

        ist_offset = timedelta(hours=5, minutes=30)
        ist_time = utc_time + ist_offset
        return ist_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception as e:
        logging.error(f"Error converting utc to ist: {str(e)}")
        return utc_time_string


def convert_utc_to_ist_in_qapi_response(
    response_json: list, time_field: str = "order_created_at_time"
) -> list:
    """
    Convert UTC timestamps to IST in JSON response objects.

    Args:
        response_json: List of JSON objects
        time_field: The field name containing the UTC timestamp to convert

    Returns:
        List of JSON objects with converted timestamps
    """
    try:
        for row in response_json:
            if time_field in row:
                row[time_field] = utc_to_ist(row[time_field])
                logging.info(
                    f"Converted {time_field} from utc to ist: {row[time_field]}"
                )
        return response_json
    except Exception as e:
        logging.error(f"Error converting {time_field} in JSON response: {str(e)}")
        return response_json


def call_query_api(payload: QApiPayload) -> dict:
    """
    Utility function to call the query API with the provided payload.

    Args:
        payload: The payload to send to the query API (QApiPayload model)

    Returns:
        The parsed response from the API as QApiResponse (either QApiSuccessResponse or QApiErrorResponse)
    """
    try:
        # Create a serialized copy of the payload for the API
        serialized_payload = {}

        # Add domain and metric
        serialized_payload["domain"] = payload.domain
        serialized_payload["metric"] = payload.metric

        # Process interval - ensure we convert datetimes to strings
        logging.info(
            f"QAPI Input: Original interval (IST expected): Start={payload.interval.start}, End={payload.interval.end}"
        )
        interval_dict = {}
        interval_dict["start"] = ist_to_utc(payload.interval.start)
        interval_dict["end"] = ist_to_utc(payload.interval.end)
        logging.info(
            f"QAPI Call: Converted interval (UTC): Start={interval_dict['start']}, End={interval_dict['end']}"
        )
        serialized_payload["interval"] = interval_dict

        # Process filters if present
        if payload.filters:
            serialized_payload["filters"] = payload.filters.model_dump(
                mode="json", by_alias=True
            )

        # Process dimensions
        serialized_payload["dimensions"] = (
            payload.dimensions.model_dump(mode="json", by_alias=True)
            if payload.dimensions
            else []
        )

        # Process sortedOn if present
        if payload.sortedOn:
            serialized_payload["sortedOn"] = payload.sortedOn.model_dump(
                mode="json", by_alias=True
            )

        # Call the internal analytics API
        logging.debug(f"QAPI Call: Sending payload: {serialized_payload}")
        web_login_token = os.getenv("JUSPAY_WEB_LOGIN_TOKEN")
        response = requests.post(
            "https://portal.juspay.in/api/q/query",
            data=json_dumps_with_datetime(serialized_payload),
            headers={
                "X-Web-LoginToken": web_login_token,
                "Content-Type": "application/json",
            },
        )
        logging.info(f"QAPI Response Raw (IST expected): {response.text}")
        response.raise_for_status()  # Raise exception for HTTP errors

        # Parse JSONL response
        response_json = [json.loads(line) for line in response.text.splitlines()]
        validated_response = QApiSuccessResponse.model_validate(response_json)
        logging.info(
            f"QAPI Return: Parsed response (IST expected): {validated_response}"
        )
        return validated_response.dict()
    except Exception as e:
        logging.error(f"Error calling query API: {str(e)}")
        return QApiErrorResponse(
            error=f"Failed to execute query: {str(e)}",
            payload_attempted=(
                serialized_payload
                if "serialized_payload" in locals()
                else payload.model_dump()
            ),
        ).dict()


async def q_api(payload: dict) -> QApiResponse:
    """
    Tool for querying data from the analytics API.

    Args:
       payload dict whcih contains all the below fields in it:
        wrapper: Context wrapper containing auth token
        interval: Time interval for the query (Expected IST)
        metric: Metric to query
        dimensions: Dimensions to include
        filters: Filters to apply
        sortedOn: Sorting criteria

    Returns:
        QApiResponse with the query results (Timestamps should be IST)
    """
    metric = payload.get("metric")
    interval = payload.get("interval")
    dimensions = payload.get("dimensions")
    filters = payload.get("filters")
    sortedOn = payload.get("sortedOn")

    logging.info(
        f"QAPI Tool Input: Interval={interval}, Metric={metric}, Dimensions={dimensions}, Filters={filters}, SortedOn={sortedOn}"
    )
    # Construct the payload using the QApiPayload model with proper types
    q_api_payload = QApiPayload(
        domain="kvorders",
        metric=metric,
        interval=interval,
        filters=filters,
        dimensions=dimensions,
        sortedOn=sortedOn,
    )

    # Log the payload for debugging
    logging.debug(f"QAPI Tool: Creating payload: {json.dumps(q_api_payload.model_dump())}")

    return await asyncio.to_thread(call_query_api, q_api_payload)
