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
    
    api_payload_obj = {
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
        api_payload_obj["filters"]["platform"] = [platform]
    
    api_payload = [api_payload_obj]
    
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
    
    host = await get_juspay_host_from_api(meta_info=meta_info)
    api_url = f"{host}/{integrationSuffix}/integration-monitoring/v1/xmerchant/metrics"

    return await post(api_url, api_payload, None, meta_info)


async def get_integration_platform_metrics_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves integration metrics grouped by platform for product integration analysis.
    
    This API is used for:
    - Platform dropdown population with available platforms (Android, IOS, Web, Backend)
    - Platform-specific content and completion percentage calculation
    
    Args:
        payload (dict): Contains merchant_id, start_time, end_time
        meta_info (dict): Optional metadata
        
    Returns:
        dict: Platform-grouped product integration data with queryString, queryData, and metaData
    """

    api_payload = [{
        "timeRange": {
            "startTime": payload["start_time"],
            "endTime": payload["end_time"]
        },
        "groupByNames": ["platform"],
        "filters": {
            "merchant_id": [payload["merchant_id"]]
        },
        "source": "REALTIME",
        "metrics": ["product"],
        "innerSelect": [
            "platform",
            "product_integrated", 
            "time_bucket"
        ],
        "secondInnerSelect": [
            "platform",
            "product_integrated",
            "time_bucket",
            "merchant_id"
        ]
    }]
    
    host = await get_juspay_host_from_api(meta_info=meta_info)
    api_url = f"{host}/{integrationSuffix}/integration-monitoring/v1/integrations/metrics"

    return await post(api_url, api_payload, None, meta_info)


async def get_integration_product_count_metrics_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves integration metrics grouped by product_integrated for product count analysis.
    
    This API is used for:
    - Product selection logic (product with max count becomes default)
    - Dynamic product array creation for product dropdown population
    - Integration health calculation and most actively used integration type identification
    
    Args:
        payload (dict): Contains merchant_id, platform, start_time, end_time
        meta_info (dict): Optional metadata
        
    Returns:
        dict: Product-grouped integration count data with queryString, queryData, and metaData
    """
    
    api_payload = [{
        "timeRange": {
            "startTime": payload["start_time"],
            "endTime": payload["end_time"]
        },
        "groupByNames": ["product_integrated"],
        "filters": {
            "merchant_id": [payload["merchant_id"]],
            "platform": [payload["platform"]]
        },
        "source": "REALTIME",
        "metrics": ["product_count"],
        "innerSelect": [
            "product_integrated",
            "time_bucket"
        ],
        "secondInnerSelect": [
            "product_integrated",
            "time_bucket",
            "merchant_id",
            "platform"
        ]
    }]
    
    host = await get_juspay_host_from_api(meta_info=meta_info)
    api_url = f"{host}/{integrationSuffix}/integration-monitoring/v1/integrations/metrics"
    return await post(api_url, api_payload, None, meta_info)
