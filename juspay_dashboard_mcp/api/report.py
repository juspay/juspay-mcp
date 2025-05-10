# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from juspay_dashboard_mcp.api.utils import post, get_juspay_host_from_api

async def report_details_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Returns detailed information for a specific report ID, including data sources, 
    metrics, dimensions, and filters.

    The API endpoint is:
        https://portal.juspay.in/api/monitoring/task

    The call uses URL parameters:
        - task_uid: Unique identifier for the report/task
        - user_name: Name of the user requesting the report

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json

    Args:
        payload (dict): A dictionary with the following required keys:
            - task_uid: Unique identifier for the report/task.
            - user_name: Name of the user requesting the report.

    Returns:
        dict: The parsed JSON response from the Juspay Report Details API.

    Raises:
        ValueError: If required parameters are missing.
        Exception: If the API call fails.
    """
    task_uid = payload.get("task_uid")
    user_name = payload.get("user_name")
    
    if not task_uid or not user_name:
        raise ValueError("The payload must include 'task_uid' and 'user_name'.")

    host = await get_juspay_host_from_api()
    api_url = f"{host}/api/monitoring/task?task_uid={task_uid}&user_name={user_name}"
    
    # Empty body since parameters are in URL
    return await post(api_url, {}, None, meta_info)

async def list_report_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Lists all reports configured by the merchant, along with their status, recipients, 
    thresholds, and monitoring intervals.

    The API endpoint is:
        https://portal.juspay.in/api/monitoring/task/list

    The call uses JSON data containing:
        - merchantId: Merchant identifier
        - task_type: Set to 'report'
        - std_report: Optional boolean flag

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json

    Args:
        payload (dict): A dictionary containing:
            - merchantId: Merchant identifier.
            - task_type: Should be set to 'report'.
            - std_report: (Optional) Boolean flag.

    Returns:
        dict: The parsed JSON response from the Juspay List Report API.

    Raises:
        ValueError: If required parameters are missing.
        Exception: If the API call fails.
    """
    if "merchantId" not in payload or payload.get("task_type") != "report":
        raise ValueError("Payload must contain 'merchantId' and 'task_type' must be 'report'.")
    
    host = await get_juspay_host_from_api()
    api_url = f"{host}/api/monitoring/task/list"
    
    return await post(api_url, payload, None, meta_info)
