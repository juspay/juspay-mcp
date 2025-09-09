# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt
import os
import dotenv
from juspay_dashboard_mcp.api.utils import post, get_juspay_host_from_api

dotenv.load_dotenv()

JUSPAY_ENV = os.getenv("JUSPAY_ENV", "production").lower() 
integrationSuffix = "ic-api" if JUSPAY_ENV == "production" else "ic"
    
async def get_integration_monitoring_status_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves integration monitoring status for specified platform and product.
    
    Automatically routes to:
    - agnostic API for Backend platform (excludes platform from request)
    - nonagnostic API for Web/Android/iOS platforms (includes platform in request)
    
    Args:
        payload (dict): Contains platform, product_integrated, merchant_id, start_time, end_time
        meta_info (dict): Optional metadata
        
    Returns:
        dict: Integration monitoring status data
    """
    platform = payload.get("platform")
    
    # Determine API endpoint based on platform
    api_payload = {
        "timeRange": {
            "startTime": payload["start_time"],
            "endTime": payload["end_time"]
        },
        "groupByNames": ["stage"],
        "filters": {
            "merchant_id": [payload["merchant_id"]],
            "product_integrated": [payload["product_integrated"]]
        },
        "source": "REALTIME",
        "metrics": ["status"],
        "innerSelect": ["stage", "success_total", "total", "min_hits", "no_of_states"],
        "secondInnerSelect": ["stage", "success_total", "total", "time_bucket", "merchant_id", "product_integrated", "platform"]
    }
    
    if platform != "Backend":
        api_payload["filters"]["platform"] = [platform]
    
    # Get the host and make the API call
    host = await get_juspay_host_from_api(meta_info=meta_info)
    domain = "agnostic" if platform == "Backend" else "nonagnostic"
    api_url = f"{host}/{integrationSuffix}/integration-monitoring/v1/{domain}/status"
    
    return await post(api_url, api_payload, None, meta_info)


async def get_x_mid_monitoring_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves X-Mid monitoring metrics to check if x_merchant_id is being passed to API calls.
    
    This API provides insights on whether x_merchant_id is being properly passed to various
    API endpoints, helping identify integration issues related to merchant ID validation.
    
    Args:
        payload (dict): Contains merchant_id, start_time and end_time for the query range
        meta_info (dict): Optional metadata
        
    Returns:
        dict: Contains validation status for each API endpoint
    """
    # Construct the API payload matching the curl request structure
    api_payload = [{
        "timeRange": {
            "startTime": payload["start_time"],
            "endTime": payload["end_time"]
        },
        "groupByNames": ["api_shortcode"],
        "filters": {
            "merchant_id": [payload["merchant_id"]],
            "status_code": [200]
        },
        "source": "REALTIME",
        "metrics": ["validate_xmid"]
    }]
    
    # Get the host and make the API call
    host = await get_juspay_host_from_api(meta_info=meta_info)
    api_url = f"{host}/{integrationSuffix}/integration-monitoring/v1/xmerchant/metrics"
    
    # Add the required header for this specific API
    additional_headers = {"x-feature": "canary_i"}
    
    return await post(api_url, api_payload, additional_headers, meta_info)
