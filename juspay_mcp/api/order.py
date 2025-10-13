# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import httpx
import secrets
import string
from juspay_mcp.config import ENDPOINTS 
from juspay_mcp.api.utils import call, post

async def order_status_api_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves the status of a specific Juspay order using the order_id.

    This function sends an HTTP GET request to the Juspay Order Status endpoint.
    The 'order_id' from the payload is appended to the URL. If 'customer_id'
    is present in the payload, it's used for the routing_id header.

    Args:
        payload (dict): Must include:
            - order_id (str): Unique identifier of the order to check.
        May include:
            - customer_id (str, optional): If provided, used for the x-routing-id header.

    Returns:
        dict: Parsed JSON response from the Juspay Order Status API, containing details
              about the order, such as its status.

    Raises:
        ValueError: If 'order_id' is missing in the payload.
        Exception: If the API call fails (e.g., HTTP error, network issue).
    """
    order_id = payload.get("order_id")
    if not order_id:
        raise ValueError("The payload must include 'order_id'.")

    customer_id = payload.get("customer_id")

    api_url = ENDPOINTS["order_status"].format(order_id=order_id)
    return await call(api_url, customer_id, meta_info=meta_info)

async def create_order_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Creates a new order in Juspay payment system.

    This function sends an HTTP POST request to the Juspay Orders endpoint.
    It includes order details like order_id, amount, currency, customer info, etc.
    If 'customer_id' is present in the payload, it's used for the routing_id header.

    Args:
        payload (dict): Must include required fields like:
            - order_id (str): Unique identifier for the order (max 21 alphanumeric chars).
            - amount (str): The order amount (e.g., '100.00').
            - currency (str): Currency code (e.g., 'INR').
            - customer_id (str): Merchant's identifier for the customer.
            - customer_email (str): Customer's email address.
            - customer_phone (str): Customer's phone number.
            - return_url (str): URL to redirect after payment.
        May include many optional fields like description, billing address, shipping address.
        
    Returns:
        dict: Parsed JSON response from the Juspay Create Order API, containing order details.

    Raises:
        ValueError: If any required field is missing.
        Exception: If the API call fails (e.g., HTTP error, network issue).
    """
    # Generate order_id if not provided
    if not payload.get("order_id"):
        # Generate alphanumeric string with max length 21
        payload["order_id"] = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
    
    # Get customer details from payload or meta_info
    if not payload.get("customer_id") and meta_info:
        payload["customer_id"] = meta_info.get("customer_id")
    
    if not payload.get("customer_email") and meta_info:
        payload["customer_email"] = meta_info.get("email")
    
    if not payload.get("customer_phone") and meta_info:
        payload["customer_phone"] = meta_info.get("phone_no")
        
    if not payload.get("return_url"):
         payload["return_url"] = "https://example.com/return"  
         
    # Extract gateway_id from meta_info if not in payload
  

    payload["gateway_id"] = meta_info.get("gateway_id")
    
    # Extract gateway_reference_id from meta_info and add to payload with full name
    payload["metadata.JUSPAY:gateway_reference_id"] = meta_info.get("gateway_reference_id")

    # Check required fields after auto-population
    required_fields = ["amount", "currency", "customer_id", "customer_email", "customer_phone", "return_url"]
    
    for field in required_fields:
        if not payload.get(field):
            if field in ["customer_id", "customer_email", "customer_phone"]:
                raise ValueError(f"The payload must include '{field}' or it must be provided in meta_info.")
            else:
                raise ValueError(f"The payload must include '{field}'.")
            
    # Process any boolean options
    if payload.get("get_client_auth_token"):
        payload["options.get_client_auth_token"] = "true"
        
    # Process any metadata fields
    for key, value in list(payload.items()):
        if key.startswith("metadata."):
            payload[key] = str(value)
            
    # Get routing ID if provided, otherwise use customer_id
    routing_id = payload.get("routing_id", payload.get("customer_id"))
    
    api_url = ENDPOINTS["create_order"]
    return await post(api_url, payload, routing_id, meta_info)

async def update_order_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Updates an existing order in Juspay.
    
    This function sends an HTTP POST request to the Juspay Update Order endpoint.
    The order_id is used in the URL path, and other fields are sent as form data.
    
    Args:
        payload (dict): Must include:
            - order_id (str): Juspay order ID to update.
        May include:
            - amount (str): Updated order amount.
            - currency (str): Updated currency code.
            - And other updateable fields.
            
    Returns:
        dict: Parsed JSON response containing the updated order details.
        
    Raises:
        ValueError: If order_id is missing.
        Exception: If the API call fails.
    """
    order_id = payload.get("order_id")
    if not order_id:
        raise ValueError("The payload must include 'order_id'.")
    
    # Remove order_id from payload as it's in the URL
    update_data = {k: v for k, v in payload.items() if k != "order_id"}
    
    if not update_data:
        raise ValueError("At least one field must be provided for update.")
    
    # Get routing ID if provided
    routing_id = payload.get("routing_id", payload.get("customer_id"))
    
    api_url = ENDPOINTS["update_order"].format(order_id=order_id)
    return await post(api_url, update_data, routing_id, meta_info)

async def order_fulfillment_sync(payload: dict, meta_info: dict = None) -> dict:
    """
    Updates the fulfillment status of an order.
    
    This function sends an HTTP POST request to the Juspay Order Fulfillment endpoint
    to synchronize the order's delivery/fulfillment status with Juspay.
    
    Args:
        payload (dict): Must include:
            - order_id (str): Unique identifier of the order to update.
            - fulfillment_status (str): Status of fulfillment (SUCCESS, FAILURE, PENDING).
            - fulfillment_command (str): Command for fulfillment (NO_ACTION, RELEASE_HOLD, HOLD).
            - fulfillment_time (str): Time of fulfillment in ISO format.
            - fulfillment_id (str): Unique identifier for this fulfillment action.
        May include:
            - fulfillment_data (str): Optional metadata for the fulfillment.
            - routing_id (str): Optional routing ID.
            
    Returns:
        dict: Parsed JSON response containing the fulfillment update status.
        
    Raises:
        ValueError: If required fields are missing.
        Exception: If the API call fails.
    """
    order_id = payload.pop("order_id")
    if not order_id:
        raise ValueError("The payload must include 'order_id'.")
    
    required_fields = ["fulfillment_status", "fulfillment_command", "fulfillment_time", "fulfillment_id"]
    for field in required_fields:
        if not payload.get(field):
            raise ValueError(f"The payload must include '{field}'.")
    
    routing_id = payload.get("routing_id")
    if "routing_id" in payload:
        payload.pop("routing_id")
    
    api_url = ENDPOINTS["order_fulfillment"].format(order_id=order_id)
    return await post(api_url, payload, routing_id, meta_info)
