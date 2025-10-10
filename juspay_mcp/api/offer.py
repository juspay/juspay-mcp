# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import httpx
from juspay_mcp.config import ENDPOINTS
from juspay_mcp.api.utils import call, post

async def list_offers_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Lists available offers for a given order with optional coupon code.
    
    This function sends an HTTP POST request to the Juspay Offers List endpoint.
    It provides information about eligible offers based on order amount,
    payment methods, and optional coupon code.
    
    Args:
        payload (dict): Must include:
            - order (dict): Order details including order_id, amount, and currency.
            - payment_method_info (list): List of payment method details.
        May include:
            - customer (dict): Customer details like id, email, and mobile.
            - offer_code (str): Specific coupon code to apply.
            - routing_id (str): Custom routing identifier.
        meta_info (dict, optional): Authentication credentials override.
    
    Returns:
        dict: Parsed JSON response containing available offers and their details.
    
    Raises:
        ValueError: If required fields are missing.
        Exception: If the API call fails.
    """
    if not payload.get("order"):
        raise ValueError("The payload must include 'order' object")
    
    payload["payment_method_info"] = [{
        "payment_method_type": "CASH",
        "payment_method": "CASH", 
        "payment_method_reference": "CASH_CASH_ref"
    }]
    
    routing_id = payload.get("routing_id")
    if "routing_id" in payload:
        payload.pop("routing_id")
    
    api_url = ENDPOINTS["offer_list"]
    return await post(api_url, payload, routing_id, meta_info)

async def get_offer_order_status_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves the status of an order with offer details.
    
    This function sends an HTTP GET request to the Juspay Order Status endpoint
    with the 'version' header to include offer information in the response.
    
    Args:
        payload (dict): Must include:
            - order_id (str): Unique identifier of the order to check.
        May include:
            - routing_id (str): Custom routing identifier.
        meta_info (dict, optional): Authentication credentials override.
    
    Returns:
        dict: Parsed JSON response containing order status with offer details.
    
    Raises:
        ValueError: If order_id is missing.
        Exception: If the API call fails.
    """
    order_id = payload.get("order_id")
    if not order_id:
        raise ValueError("The payload must include 'order_id'")
    
    routing_id = payload.get("routing_id")
    
    api_url = ENDPOINTS["offer_order_status"].format(order_id=order_id)
    
    headers = {
        "version": "2023-06-30"
    }
    
    return await call(api_url, routing_id, headers, meta_info=meta_info)
