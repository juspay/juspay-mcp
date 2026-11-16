# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from juspay_dashboard_mcp.api.utils import post, get_juspay_host_from_api, assert_merchant_access
import logging
    
    
async def list_outages(payload: dict, meta_info: dict = None) -> dict:
    """
    Returns a list of outages within a specified time range, optionally filtered by merchant ID.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/outage/list

    Args:
        payload (dict): A dictionary containing:
            - startTime: Start time in ISO format (e.g., '2025-05-22T18:30:00Z') - required
            - endTime: End time in ISO format (e.g., '2025-05-23T10:30:12Z') - required
            - merchantId: Merchant ID to filter outages (optional)

    Returns:
        dict: The parsed JSON response from the Juspay List Outages API containing:
            - issuerName: Name of the bank/issuer
            - status: Outage status (e.g., 'FLUCTUATE')
            - juspayBankCode: Juspay's internal bank code
            - merchantId: Merchant ID ('global' for global outages)
            - paymentMethodType: Type of payment method (e.g., 'UPI')
            - paymentMethod: Payment method (e.g., 'UPI')
            - outagePeriods: Array of outage periods with startTime, endTime, and duration (converted to IST)
            - stage: Stage information (for global outages)

    Raises:
        ValueError: If required parameters are missing.
        Exception: If the API call fails.
    """
    start_time = payload.get("startTime")
    end_time = payload.get("endTime")
    
    if not start_time or not end_time:
        raise ValueError("Both 'startTime' and 'endTime' are required in the payload")
    
    request_data = {
        "startTime": start_time,
        "endTime": end_time
    }
    
    
    host = await get_juspay_host_from_api(meta_info=meta_info)
    
    
    assert_merchant_access(payload.get("merchantId"), "You are not authorized to view outages for this merchantId")
    
    api_url = f"{host}/api/ec/v1/outage/list"
    
    return await post(api_url, request_data, None, meta_info)