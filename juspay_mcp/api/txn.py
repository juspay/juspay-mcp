# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import httpx
from juspay_mcp.config import ENDPOINTS 
from juspay_mcp.api.utils import call, post

async def create_txn_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Creates an order and processes payment in a single API call.
    
    This function sends an HTTP POST request to the Juspay Txns endpoint to create
    an order and initiate payment processing simultaneously.
    
    Args:
        payload (dict): A dictionary containing order and payment details.
        Must include:
            - order.order_id (str): Unique identifier for the order.
            - order.amount (str): The order amount.
            - order.currency (str): Currency code.
            - order.customer_id (str): Customer identifier.
            - order.return_url (str): URL to redirect after payment.
            - merchant_id (str): Your merchant ID.
            - payment_method_type (str): Type of payment method (CARD, NB, etc.).
        For CARD payments, must also include:
            - card_number, card_exp_month, card_exp_year, etc.
        meta_info (dict, optional): Authentication credentials override.
            
    Returns:
        dict: Parsed JSON response containing transaction details.
        
    Raises:
        ValueError: If required fields are missing.
        Exception: If the API call fails.
    """
    required_fields = ["order.order_id", "order.amount", "order.currency", 
                      "order.customer_id", "payment_method_type", 
                      "order.return_url", "merchant_id"]
    
    for field in required_fields:
        if not payload.get(field):
            raise ValueError(f"The payload must include '{field}'.")
    
    # Set format to json if not specified
    if "format" not in payload:
        payload["format"] = "json"
    
    # Extract routing_id if present, otherwise use order.customer_id
    routing_id = payload.get("routing_id", payload.get("order.customer_id"))
    if "routing_id" in payload:
        payload.pop("routing_id")
    
    api_url = ENDPOINTS["create_txn"]
    return await post(api_url, payload, routing_id, meta_info)

async def create_moto_txn_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Creates an order with MOTO (Mail Order/Telephone Order) payment.
    
    Similar to create_txn_juspay but specifically for MOTO transactions which
    bypass the standard 3D Secure authentication.
    
    Args:
        payload (dict): A dictionary containing order and payment details.
        Must include:
            - The same fields as create_txn_juspay
            - auth_type (str): Must be "MOTO"
        May include:
            - tavv (str): Transaction Authentication Verification Value
        meta_info (dict, optional): Authentication credentials override.
            
    Returns:
        dict: Parsed JSON response containing transaction details.
        
    Raises:
        ValueError: If required fields are missing or auth_type is not "MOTO".
        Exception: If the API call fails.
    """
    if payload.get("auth_type") != "MOTO":
        raise ValueError("For MOTO transactions, 'auth_type' must be 'MOTO'.")
    
    # Use the standard txn creation function with additional MOTO parameters
    return await create_txn_juspay(payload, meta_info)
