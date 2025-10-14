# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from juspay_dashboard_mcp.api.utils import post, get_admin_host
import logging
import os
from datetime import datetime, timedelta

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
    
    
async def list_outages_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Returns a list of outages within a specified time range, optionally filtered by merchant ID.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/admin/outage/list (for admin users)
        https://portal.juspay.in/api/ec/v1/outage/list (for non-admin users)

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
    
    # Convert IST to UTC for the API request
    start_time_utc = ist_to_utc(start_time)
    end_time_utc = ist_to_utc(end_time)
    
    request_data = {
        "startTime": start_time_utc,
        "endTime": end_time_utc
    }
    
    
    host, isadmin = await get_admin_host(meta_info=meta_info)
    
    mid_from_meta = None
    if meta_info:
        token_response = meta_info.get("token_response", {})
        mid_from_meta = token_response.get("merchantId") or meta_info.get("merchantId")
    
    if not isadmin and payload.get("merchantId") and mid_from_meta and payload.get("merchantId") != mid_from_meta:
        raise ValueError("You are not authorized to view outages for this merchantId")
    
    if isadmin and payload.get("merchantId"):
        request_data["merchantId"] = payload["merchantId"]

    if isadmin:
        api_url = f"{host}/api/ec/v1/admin/outage/list"
    else:
        api_url = f"{host}/api/ec/v1/outage/list"
    
    response =await post(api_url,request_data, None, meta_info)
    
    if isinstance(response, list):
        for outage in response:
            if "outagePeriods" in outage and isinstance(outage["outagePeriods"], list):
                for period in outage["outagePeriods"]:
                    if "startTime" in period:
                        period["startTime"] = utc_to_ist(period["startTime"])
                    if "endTime" in period:
                        period["endTime"] = utc_to_ist(period["endTime"])
    
    return response
