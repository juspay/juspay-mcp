# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import os
import logging
import json
from typing import Dict, List, Any
from juspay_dashboard_mcp.api.utils import post
import requests


logger = logging.getLogger(__name__)

JUSPAY_WEB_LOGIN_TOKEN = os.getenv("JUSPAY_WEB_LOGIN_TOKEN")


async def list_unified_alerts_juspay(payload: dict, meta_info: dict = None) -> List[Dict[str, Any]]:
    """
    Retrieves unified alerts from the alerts API with flexible filtering options.
    
    This function calls the external alerts API and transforms the columnar response
    into a list of alert objects for easier consumption.

    Args:
        payload (dict): A dictionary containing:
            - merchantId: Merchant ID to filter alerts (required).
            - startTime: Start time in 'YYYY-MM-DD HH:MM:SS' format (required).
            - endTime: End time in 'YYYY-MM-DD HH:MM:SS' format (required).
            - name: Optional alert name/type to filter by (e.g., 'Api Availability Drop').
            - dimensions: Optional dictionary to filter for alerts triggered on a specific subset of dimensions. For example, `{'api': 'TRANSACTION'}` would return alerts where the 'api' dimension was 'TRANSACTION'.

    Returns:
        List[Dict[str, Any]]: A list of alert objects, each containing all alert fields.

    Raises:
        Exception: If the API call fails.
    """
    
    # Build the request payload for the backend API
    request_data = {
        "is_visible": True,
        "with_config": True, 
        "merchant_id" : payload["merchantId"], 
        "select_columns":[
            "name",
            "dimensions",
            "merchant_id",
            "current_metric",
            "expected_metric",
            "start_time",
            "metadata_alert_details",
            "metadata_info",
            "recovered_ts", 
            "category"
        ], 
        "format" : "raw"
    }
    
    # Add dimensions if provided
    if payload.get("dimensions"):
        request_data["dimensions"] = payload["dimensions"]
    
    # Add name to dimensions if provided
    if payload.get("name"):
        request_data["name"] = payload["name"]

    if payload.get("startTime") :
        if payload.get("endTime") :
            request_data["ts_alert"] = {
                "start" : payload["startTime"], 
                "end" : payload["endTime"]
            }
        else :
            request_data["ts_alert"] = {
                "start" : payload["startTime"]
            }
    else :
        if payload.get("endTime") :
            request_data["ts_alert"] = {
                "end" : payload["endTime"]
            }
    
    # Make the API call
    alert_api_host = "https://alerts-api.internal.svc.k8s.cha.mum.juspay.net"
    api_url = f"{alert_api_host}/getExternalAlerts"
    
    logger.info(f"Making request to unified alerts API: {api_url}")
    logger.debug(f"Request payload: {request_data}")

    if meta_info:
        web_login_token = meta_info.get("x-web-logintoken", JUSPAY_WEB_LOGIN_TOKEN)
    else:
        web_login_token = JUSPAY_WEB_LOGIN_TOKEN

    print(f"request_data :- {request_data}")
    resp = await post(api_url, 
        request_data, 
        additional_headers = dict(token = web_login_token), 
        meta_info = meta_info)

    return _parse_alerts_response(resp)
    

def _parse_alerts_response(response_data) -> List[Dict[str, Any]]:
    """
    Parses the alerts API response from string to list of dictionaries.
    
    Args:
        response_data: Response from the alerts API (could be string, list, or dict)
        
    Returns:
        List of dictionaries
    """
    # If response is a string, parse it as JSON
    if isinstance(response_data, str):
        try:
            parsed_data = json.loads(response_data)
            if isinstance(parsed_data, list):
                return parsed_data
            elif isinstance(parsed_data, dict):
                return [parsed_data]
            else:
                logger.warning(f"Unexpected parsed data type: {type(parsed_data)}")
                return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return []
    
    # If response is already a list of dictionaries, return as-is
    if isinstance(response_data, list):
        return response_data
    
    # For any other format, wrap in list
    return [response_data] if response_data else []


