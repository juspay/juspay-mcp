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
    integrationSuffix = "ic-api" if JUSPAY_ENV == "production" else "ic"
    domain = "agnostic" if platform == "Backend" else "nonagnostic"
    api_url = f"{host}/{integrationSuffix}/integration-monitoring/v1/{domain}/status"
    
    return await post(api_url, api_payload, None, meta_info)
