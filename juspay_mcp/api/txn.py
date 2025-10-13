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


async def create_cash_txn_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Creates a CASH transaction for offline payments.
    
    This function sends an HTTP POST request to the Juspay Txns endpoint to create
    a CASH transaction, typically used for offline/cash-on-delivery payments.
    
    Args:
        payload (dict): A dictionary containing transaction details.
        Must include:
            - order_id (str): Unique identifier for the order.
        May include:
            - merchant_id (str): Your merchant ID. If not provided, taken from meta_info.
            - redirect_after_payment (bool): Whether to redirect after payment.
            - format (str): Response format, defaults to 'json'.
            - routing_id (str): Custom routing identifier.
        meta_info (dict, optional): Authentication credentials override. Should contain
            merchant_id if not provided in payload.
            
    Returns:
        dict: Parsed JSON response containing transaction details.
        
    Raises:
        ValueError: If required fields are missing.
        Exception: If the API call fails.
    """
    # Validate required fields
    if not payload.get("order_id"):
        raise ValueError("The payload must include 'order_id'.")
    
    # Get merchant_id from payload or meta_info
    merchant_id = payload.get("merchant_id")
    if not merchant_id and meta_info:
        merchant_id = meta_info.get("juspay_merchant_id")
    
    if not merchant_id:
        raise ValueError("merchant_id must be provided either in payload or meta_info.")
    
    # Hardcode CASH payment methods
    payload["payment_method_type"] = "CASH"
    payload["payment_method"] = "CASH"
    payload["merchant_id"] = merchant_id
    
    # Set default values if not specified
    if "redirect_after_payment" not in payload:
        payload["redirect_after_payment"] = True
    
    if "format" not in payload:
        payload["format"] = "json"
    
    # Extract routing_id if present
    routing_id = payload.get("routing_id")
    if "routing_id" in payload:
        payload.pop("routing_id")
    
    api_url = ENDPOINTS["create_txn"]
    return await post(api_url, payload, routing_id, meta_info)


async def create_card_txn_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Creates a CARD transaction using a saved card token.
    
    This function sends an HTTP POST request to the Juspay Txns endpoint to create
    a CARD transaction using a previously saved card token.
    
    Args:
        payload (dict): A dictionary containing transaction details.
        Must include:
            - order_id (str): Unique identifier for the order.
            - card_token (str): Card token for the saved card.
            - payment_method_type (str): Type of payment method (e.g., 'CARD', 'NB', 'UPI').
            - card_security_code (str): CVV of the card.
        May include:
            - merchant_id (str): Your merchant ID. If not provided, taken from meta_info.
            - payment_method (str): Specific payment method (e.g., 'VISA', 'MASTERCARD').
            - name_on_card (str): Card holder name.
            - save_to_locker (bool): Whether to save card in locker. Defaults to true.
            - tokenize (bool): Whether to tokenise the card. Defaults to true.
            - redirect_after_payment (bool): Whether to redirect after payment completion. Defaults to true.
            - format (str): Response format. Defaults to 'json'.
            - offers (str): Array of offer IDs to apply (e.g., '[3a8fc1dc-2ace-4f15-8bae-16b376785692]').
            - routing_id (str): Custom routing identifier.
        meta_info (dict, optional): Authentication credentials override. Should contain
            merchant_id if not provided in payload.
            
    Returns:
        dict: Parsed JSON response containing transaction details.
        
    Raises:
        ValueError: If required fields are missing.
        Exception: If the API call fails.
    """
    # Validate required fields - when using card_token, card details are not required
    required_fields = [
        "order_id", "card_token", "payment_method_type", "card_security_code"
    ]
    
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"The payload must include '{field}'.")
    
    # Get merchant_id from payload or meta_info
    merchant_id = payload.get("merchant_id")
    if not merchant_id and meta_info:
        merchant_id = meta_info.get("juspay_merchant_id")
    
    if not merchant_id:
        raise ValueError("merchant_id must be provided either in payload or meta_info.")
    
    # Set merchant_id
    payload["merchant_id"] = merchant_id
    
    # Extract gateway_id from meta_info if not in payload

    
    # Set default values for optional fields if not provided
    if "save_to_locker" not in payload:
        payload["save_to_locker"] = "true"
    elif isinstance(payload["save_to_locker"], bool):
        payload["save_to_locker"] = "true" if payload["save_to_locker"] else "false"
    
    if "tokenize" not in payload:
        payload["tokenize"] = "true"
    elif isinstance(payload["tokenize"], bool):
        payload["tokenize"] = "true" if payload["tokenize"] else "false"
    
    if "format" not in payload:
        payload["format"] = "json"
    
    if "redirect_after_payment" not in payload:
        payload["redirect_after_payment"] = "true"
    elif isinstance(payload["redirect_after_payment"], bool):
        payload["redirect_after_payment"] = "true" if payload["redirect_after_payment"] else "false"
    
    # Extract routing_id if present
    routing_id = payload.get("routing_id")
    if "routing_id" in payload:
        payload.pop("routing_id")
    
    api_url = ENDPOINTS["create_txn"]
    return await post(api_url, payload, routing_id, meta_info)
