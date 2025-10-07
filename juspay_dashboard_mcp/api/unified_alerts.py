# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import os
import logging
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
        "full_info": True,
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
            "recovered_ts"
        ]
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
    alert_api_host = os.getenv("ALERT_API_HOST")
    api_url = F"{alert_api_host}/getExternalAlerts"
    
    logger.info(f"Making request to unified alerts API: {api_url}")
    logger.debug(f"Request payload: {request_data}")

    web_login_token = os.getenv("JUSPAY_WEB_LOGIN_TOKEN")
    # web_login_token = "80d05b637e14284aaf7f76c1260dc4"

    print(f"request_data :- {request_data}")
    resp = await post(api_url, 
        request_data, 
        additional_headers = dict(token = web_login_token), 
        meta_info = meta_info)

    # print(resp)

    return _transform_columnar_to_objects(resp)
    

def _transform_columnar_to_objects(columnar_data: Dict[str, List]) -> List[Dict[str, Any]]:
    """
    Transforms columnar data (dict of lists) into a list of objects.
    
    Args:
        columnar_data: Dictionary where each key maps to a list of values
        
    Returns:
        List of dictionaries, where each dict represents one alert with all fields
    """
    if not isinstance(columnar_data, dict):
        logger.warning("Response is not a dictionary, returning as-is")
        return columnar_data if isinstance(columnar_data, list) else [columnar_data]
    
    # Get the length of the first list to determine number of records
    if not columnar_data:
        return []
    
    first_key = next(iter(columnar_data))
    if not isinstance(columnar_data[first_key], list):
        logger.warning("Response values are not lists, returning as single object")
        return [columnar_data]
    
    num_records = len(columnar_data[first_key])
    
    # Transform to list of objects
    alerts = []
    for i in range(num_records):
        alert = {}
        for key, values in columnar_data.items():
            if isinstance(values, list) and i < len(values):
                alert[key] = values[i]
            else:
                alert[key] = None
        alerts.append(alert)
    
    return alerts
