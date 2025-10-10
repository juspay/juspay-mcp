# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import httpx
from juspay_mcp.config import ENDPOINTS
from juspay_mcp.api.utils import call, post

async def add_card_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Adds a new card to the Juspay system for a customer.

    This function sends an HTTP POST request to the Juspay Add Card endpoint.
    It stores the card details securely and returns a token for future use.

    Args:
        payload (dict): Must include:
            - merchant_id (str): Merchant identifier.
            - customer_id (str): Customer identifier.
            - customer_email (str): Customer's email address.
            - card_number (str): Complete card number.
            - card_exp_year (str): Card expiry year (e.g., '2025').
            - card_exp_month (str): Card expiry month (e.g., '07').
            - name_on_card (str): Name as printed on the card.
        May include:
            - nickname (str): Friendly name for the card.
            - routing_id (str): Custom routing identifier.
        meta_info (dict, optional): Authentication credentials override.

    Returns:
        dict: Parsed JSON response containing card_token, card_reference, and card_fingerprint.

    Raises:
        ValueError: If required fields are missing.
        Exception: If the API call fails.
    """
    required_fields = [
        "merchant_id", "customer_id", "customer_email", 
        "card_number", "card_exp_year", "card_exp_month", "name_on_card"
    ]
    
    for field in required_fields:
        if not payload.get(field):
            raise ValueError(f"The payload must include '{field}'")
            
    routing_id = payload.get("routing_id", payload.get("customer_id"))
    if "routing_id" in payload:
        payload.pop("routing_id")
        
    api_url = ENDPOINTS["card_add"]
    return await post(api_url, payload, routing_id, meta_info)

async def list_cards_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves all stored cards for a specific customer.

    This function sends an HTTP GET request to the Juspay Cards endpoint.
    It returns a list of all stored cards for the specified customer.

    Args:
        payload (dict): Must include:
            - customer_id (str): Customer identifier whose cards to retrieve.
        May include:
            - options.check_cvv_less_support (bool): Check if cards support CVV-less transactions.
            - routing_id (str): Custom routing identifier.
        meta_info (dict, optional): Authentication credentials override.

    Returns:
        dict: Parsed JSON response containing a list of cards with their details.

    Raises:
        ValueError: If customer_id is missing.
        Exception: If the API call fails.
    """
    customer_id = payload.get("customer_id")
    if not customer_id:
        raise ValueError("The payload must include 'customer_id'")
        
    routing_id = payload.get("routing_id", customer_id)
    
    api_url = f"{ENDPOINTS['cards']}?customer_id={customer_id}"
    
    if payload.get("options.check_cvv_less_support"):
        api_url += "&options.check_cvv_less_support=true"
    
    return await call(api_url, routing_id, meta_info=meta_info)

async def delete_card_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Deletes a saved card from the Juspay system.

    This function sends an HTTP POST request to the Juspay Card Delete endpoint.
    It removes the specified card based on its token.

    Args:
        payload (dict): Must include:
            - card_token (str): Unique token of the card to be deleted.
        May include:
            - routing_id (str): Custom routing identifier.
        meta_info (dict, optional): Authentication credentials override.

    Returns:
        dict: Parsed JSON response confirming deletion status.

    Raises:
        ValueError: If card_token is missing.
        Exception: If the API call fails.
    """
    card_token = payload.get("card_token")
    if not card_token:
        raise ValueError("The payload must include 'card_token'")
        
    routing_id = payload.get("routing_id")
    if "routing_id" in payload:
        payload.pop("routing_id")
        
    api_url = ENDPOINTS["card_delete"]
    return await post(api_url, payload, routing_id, meta_info)

async def update_card_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Updates details for a saved card.

    This function sends an HTTP POST request to the Juspay Card Update endpoint.
    It can be used to update card details such as nickname.

    Args:
        payload (dict): Must include:
            - card_token (str): Unique token of the card to be updated.
        May include:
            - nickname (str): New friendly name for the card.
            - customer_id (str): Customer identifier associated with the card.
            - routing_id (str): Custom routing identifier.
        meta_info (dict, optional): Authentication credentials override.

    Returns:
        dict: Parsed JSON response confirming update status.

    Raises:
        ValueError: If card_token is missing.
        Exception: If the API call fails.
    """
    card_token = payload.get("card_token")
    if not card_token:
        raise ValueError("The payload must include 'card_token'")
        
    routing_id = payload.get("routing_id")
    if "routing_id" in payload:
        payload.pop("routing_id")
        
    api_url = ENDPOINTS["card_update"]
    return await post(api_url, payload, routing_id, meta_info)

async def get_card_info_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves information about a specific card BIN (Bank Identification Number).

    This function sends an HTTP GET request to the Juspay Card BIN Info endpoint.
    It provides details about the card type, issuing bank, etc.

    Args:
        payload (dict): Must include:
            - bin (str): First 6-9 digits of the card number (BIN).
        May include:
            - routing_id (str): Custom routing identifier.
        meta_info (dict, optional): Authentication credentials override.

    Returns:
        dict: Parsed JSON response containing card BIN information.

    Raises:
        ValueError: If bin is missing.
        Exception: If the API call fails.
    """
    bin_number = payload.get("bin")
    if not bin_number:
        raise ValueError("The payload must include 'bin'")
        
    routing_id = payload.get("routing_id")
    
    api_url = f"{ENDPOINTS['card_info']}/{bin_number}"
    return await call(api_url, routing_id, meta_info=meta_info)

async def get_bin_list_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves a list of eligible BINs for a specific authentication type.

    This function sends an HTTP GET request to the Juspay BIN Eligibility endpoint.
    It returns a list of BINs that support the specified authentication type.

    Args:
        payload (dict): May include:
            - auth_type (str): Authentication type (e.g., 'OTP').
            - routing_id (str): Custom routing identifier.
        meta_info (dict, optional): Authentication credentials override.

    Returns:
        dict: Parsed JSON response containing a list of eligible BINs.

    Raises:
        Exception: If the API call fails.
    """
    auth_type = payload.get("auth_type", "OTP")
    routing_id = payload.get("routing_id")
    
    api_url = f"{ENDPOINTS['bin_list']}?auth_type={auth_type}"
    return await call(api_url, routing_id, meta_info=meta_info)
