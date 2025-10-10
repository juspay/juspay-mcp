# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import httpx
from juspay_mcp.config import ENDPOINTS 
from juspay_mcp.api.utils import call, post

async def create_refund_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Initiates a refund for a previously successful Juspay order.

    This function sends an HTTP POST request (form URL-encoded) to the Juspay Refund endpoint.
    The 'order_id' is part of the URL. 'unique_request_id' and 'amount' are sent as form data.
    If 'customer_id' is present in the payload, it's used for the routing_id header.

    Args:
        payload (dict): Must include:
            - order_id (str): Unique identifier of the order to be refunded.
            - unique_request_id (str): A unique identifier for this refund attempt.
            - amount (str): The amount to be refunded (e.g., "50.00").
        May include:
            - routing_id (str, optional): If provided, used for the x-routing-id header.
        meta_info (dict, optional): Authentication credentials override.

    Returns:
        dict: Parsed JSON response from the Juspay Refund API, indicating the status
              of the refund request.

    Raises:
        ValueError: If 'order_id', 'unique_request_id', or 'amount' are missing.
        Exception: If the API call fails (e.g., HTTP error, network issue).
    """
    order_id = payload.get("order_id")
    unique_request_id = payload.get("unique_request_id")
    amount = payload.get("amount")

    if not order_id:
        raise ValueError("The payload must include 'order_id'.")
    if not unique_request_id:
        raise ValueError("The payload must include 'unique_request_id'.")
    if not amount:
         raise ValueError("The payload must include 'amount'.")
    
    routing_id = payload.get("routing_id")

    api_url = ENDPOINTS["refund"].format(order_id=order_id)
    
    refund_data = {
        "unique_request_id": unique_request_id,
        "amount": amount,
    }
    return await post(api_url, refund_data, routing_id, meta_info)

async def create_txn_refund_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Initiates a transaction-based refund using the transaction ID instead of order ID.
    
    This function sends an HTTP POST request to the Juspay Transaction Refund endpoint.
    It requires txn_id rather than order_id for refunds.
    
    Args:
        payload (dict): Must include:
            - txn_id (str): Transaction identifier to be refunded.
            - unique_request_id (str): A unique identifier for this refund attempt.
            - amount (str): The amount to be refunded (e.g., "50.00").
        May include:
            - routing_id (str, optional): If provided, used for the x-routing-id header.
        meta_info (dict, optional): Authentication credentials override.
            
    Returns:
        dict: Parsed JSON response from the Juspay Txn Refund API.
        
    Raises:
        ValueError: If required fields are missing.
        Exception: If the API call fails.
    """
    txn_id = payload.get("txn_id")
    unique_request_id = payload.get("unique_request_id")
    amount = payload.get("amount")
    
    if not txn_id:
        raise ValueError("The payload must include 'txn_id'.")
    if not unique_request_id:
        raise ValueError("The payload must include 'unique_request_id'.")
    if not amount:
        raise ValueError("The payload must include 'amount'.")
    
    routing_id = payload.get("routing_id")
    
    refund_data = {
        "txn_id": txn_id,
        "unique_request_id": unique_request_id,
        "amount": amount
    }
    
    api_url = ENDPOINTS["txn_refund"]
    return await post(api_url, refund_data, routing_id, meta_info)
