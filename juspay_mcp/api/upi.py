# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import httpx
from juspay_mcp.config import ENDPOINTS
from juspay_mcp.api.utils import call, post

async def get_saved_payment_methods(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves a customer's saved payment methods.

    This function sends an HTTP POST request to the Juspay Customer Payment Methods endpoint.
    It returns information about the saved payment methods associated with the customer.

    Args:
        payload (dict): Must include:
            - customer_id (str): Unique identifier of the customer.
        May include:
            - payment_method (list): List of payment method types to retrieve (e.g., ["UPI_COLLECT"]).
            - routing_id (str): Custom routing identifier.
        meta_info (dict, optional): Authentication credentials override.

    Returns:
        dict: Parsed JSON response containing saved payment method details.

    Raises:
        ValueError: If customer_id is missing.
        Exception: If the API call fails.
    """
    
    customer_id=meta_info.get("customer_id")
    payload["customer_id"] = meta_info.get("customer_id")
        
    if not customer_id:
        raise ValueError("The payload must include 'customer_id'")
        
    routing_id = payload.get("routing_id", customer_id)
    payment_method =["UPI_COLLECT","CARD"]
    
    api_url = ENDPOINTS["saved_payment_methods"].format(customer_id=customer_id)
    # Always append the check_cvv_less_support query parameter
    api_url = f"{api_url}?options.check_cvv_less_support=true"
    
    body = {"payment_method": payment_method}
    return await post(api_url, body, routing_id, meta_info)

async def upi_collect(payload: dict, meta_info: dict = None) -> dict:
    """
    Creates a UPI Collect transaction.

    This function sends an HTTP POST request to initiate a UPI Collect transaction
    where the merchant requests money from the customer's UPI ID.

    Args:
        payload (dict): Must include:
            - order_id (str): Unique identifier for the order.
            - merchant_id (str): Merchant identifier.
            - upi_vpa (str): UPI Virtual Payment Address of the customer.
        May include:
            - redirect_after_payment (bool): Whether to redirect after payment.
            - routing_id (str): Custom routing identifier.
        meta_info (dict, optional): Authentication credentials override.

    Returns:
        dict: Parsed JSON response containing transaction details.

    Raises:
        ValueError: If required fields are missing.
        Exception: If the API call fails.
    """
    required_fields = ["order_id", "merchant_id", "upi_vpa"]
    
    for field in required_fields:
        if not payload.get(field):
            raise ValueError(f"The payload must include '{field}'")
            
    payload["payment_method_type"] = "UPI"
    payload["payment_method"] = "UPI_COLLECT"
    
    if "redirect_after_payment" not in payload:
        payload["redirect_after_payment"] = "true"
    if "format" not in payload:
        payload["format"] = "json"
    
    routing_id = payload.get("routing_id")
    if "routing_id" in payload:
        payload.pop("routing_id")
    
    api_url = ENDPOINTS["create_txn"]
    return await post(api_url, payload, routing_id, meta_info)

async def verify_vpa(payload: dict, meta_info: dict = None) -> dict:
    """
    Verifies if a UPI Virtual Payment Address (VPA) is valid.

    This function sends an HTTP POST request to check the validity of a UPI VPA
    and retrieve associated details like customer name and handle support.

    Args:
        payload (dict): Must include:
            - vpa (str): UPI Virtual Payment Address to verify.
            - merchant_id (str): Merchant identifier.
        May include:
            - routing_id (str): Custom routing identifier.
        meta_info (dict, optional): Authentication credentials override.

    Returns:
        dict: Parsed JSON response containing VPA verification status.

    Raises:
        ValueError: If required fields are missing.
        Exception: If the API call fails.
    """
    vpa = payload.get("vpa")
    merchant_id = payload.get("merchant_id")
    
    if not vpa:
        raise ValueError("The payload must include 'vpa'")
    if not merchant_id:
        raise ValueError("The payload must include 'merchant_id'")
    
    routing_id = payload.get("routing_id")
    if "routing_id" in payload:
        payload.pop("routing_id")
    
    api_url = ENDPOINTS["verify_vpa"]
    return await post(api_url, payload, routing_id, meta_info)

async def upi_intent(payload: dict, meta_info: dict = None) -> dict:
    """
    Creates a UPI Intent transaction.

    This function sends an HTTP POST request to initiate a UPI Intent transaction
    which allows the customer to pay using their preferred UPI app.

    Args:
        payload (dict): Must include:
            - order_id (str): Unique identifier for the order.
            - merchant_id (str): Merchant identifier.
        May include:
            - upi_app (str): Specific UPI app to open (e.g., "com.phonepe.app").
            - sdk_params (bool): Whether to include SDK parameters in the response.
            - redirect_after_payment (bool): Whether to redirect after payment.
            - routing_id (str): Custom routing identifier.
        meta_info (dict, optional): Authentication credentials override.

    Returns:
        dict: Parsed JSON response containing transaction details.

    Raises:
        ValueError: If required fields are missing.
        Exception: If the API call fails.
    """
    required_fields = ["order_id", "merchant_id"]
    
    for field in required_fields:
        if not payload.get(field):
            raise ValueError(f"The payload must include '{field}'")
    
    payload["payment_method_type"] = "UPI"
    payload["payment_method"] = "UPI_PAY"
    
    if "redirect_after_payment" not in payload:
        payload["redirect_after_payment"] = "true"
    if "format" not in payload:
        payload["format"] = "json"
    if "sdk_params" not in payload:
        payload["sdk_params"] = "true"
    
    routing_id = payload.get("routing_id")
    if "routing_id" in payload:
        payload.pop("routing_id")
    
    api_url = ENDPOINTS["create_txn"]
    return await post(api_url, payload, routing_id, meta_info)
