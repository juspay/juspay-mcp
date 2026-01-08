# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from juspay_dashboard_mcp.api.utils import call, get_juspay_host_from_api, make_payout_additional_headers, post
import logging
import base64
import random
import string
from datetime import datetime

async def list_beneficiaries_per_customerId_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves a list of all beneficiaries associated with a specific customer ID.
    This API returns beneficiary details including account information, verification
    status, and configuration details for all beneficiaries linked to the provided
    customer for payout operations.

    This endpoint provides comprehensive information about beneficiaries registered
    under a particular customer, enabling merchants to view and manage beneficiary
    relationships for payout disbursements.

    The API endpoint is:
        https://portal.juspay.in/api/payout/batch/dashboard/v2/benedetails/{customerId}

    Args:
        payload (dict): A dictionary with the following required key:
            - customerId: Unique identifier for the customer whose beneficiaries are to be retrieved.

    Returns:
        dict: The parsed JSON response containing a list of beneficiaries associated
              with the customer, including account details and verification status.

    Raises:
        ValueError: If required 'customerId' parameter is missing.
        Exception: If the API call fails.
    """

    customerId = payload.pop("customerId", None)
    if not customerId:
        raise ValueError("The payload must include 'customerId'.")

    host = await get_juspay_host_from_api(meta_info=meta_info)
    additional_headers = make_payout_additional_headers(meta_info)
    api_url = f"{host}/api/payout/batch/dashboard/v2/benedetails/{customerId}"

    return await call(api_url, additional_headers=additional_headers, meta_info=meta_info)

async def get_beneficiary_details_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves detailed information for a specific beneficiary identified by customer ID
    and beneficiary ID. This API returns comprehensive beneficiary details including
    account information, verification status, configuration parameters, and operational
    settings for the specified beneficiary.

    This endpoint provides detailed view of a particular beneficiary's information,
    enabling merchants to access specific beneficiary data for payout operations
    and account management purposes.

    The API endpoint is:
        https://portal.juspay.in/api/payout/batch/dashboard/v2/benedetails/{customerId}/{beneId}

    Args:
        payload (dict): A dictionary with the following required keys:
            - customerId: Unique identifier for the customer.
            - beneId: Unique identifier for the beneficiary.

    Returns:
        dict: The parsed JSON response containing detailed beneficiary information
              including account details, verification status, and configuration parameters.

    Raises:
        ValueError: If required 'customerId' or 'beneId' parameters are missing.
        Exception: If the API call fails.
    """

    customerId = payload.pop("customerId", None)
    beneId = payload.pop("beneId", None)
    if not customerId or not beneId:
        raise ValueError("The payload must include 'customerId' and 'beneId'.")

    host = await get_juspay_host_from_api(meta_info=meta_info)
    additional_headers = make_payout_additional_headers(meta_info)
    api_url = f"{host}/api/payout/batch/dashboard/v2/benedetails/{customerId}/{beneId}"
    return await call(api_url, additional_headers=additional_headers, meta_info=meta_info)


async def create_or_validate_beneficiary_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Creates or validates a beneficiary bank account for payout operations.
    
    This API allows merchants to:
    - CREATE: Register a new beneficiary with bank account details
    - VALIDATE: Verify existing beneficiary details before initiating payouts
    
    Accepts simple flat values (name, ifsc, account) - nested payload is constructed automatically.

    The API endpoint is:
        https://sandbox.juspay.in/payout/merchant/v2/benedetails

    Args:
        payload (dict): A dictionary containing:
            - command: Command for the operation - 'CREATE' or 'VALIDATE' (required)
            - name: Beneficiary's name as per bank account (required)
            - ifsc: IFSC code of the beneficiary's bank branch (required)
            - account: Bank account number of the beneficiary (required)
            - beneId: Unique reference ID for the beneficiary (optional - auto-generated if not provided)
            - customerId: Merchant's unique customer identifier (optional - taken from meta_info.customer_id)
            - email: Email address of the beneficiary (optional - taken from meta_info.email)
            - phone: Phone number of the beneficiary (optional - taken from meta_info.phone_no)

    Returns:
        dict: The parsed JSON response containing the result including:
            - Beneficiary creation/verification status
            - Account details
            - Error information if operation fails

    Raises:
        ValueError: If required parameters are missing.
        Exception: If the API call fails.
    """
    # Get values from meta_info as fallback
    meta_info = meta_info or {}
    
    # Get customer details from meta_info if not provided in payload
    customer_id = payload.get("customerId")
    if not customer_id and meta_info:
        customer_id = meta_info.get("customer_id")
    
    email = payload.get("email")
    if not email and meta_info:
        email = meta_info.get("email")
    
    phone = payload.get("phone")
    if not phone and meta_info:
        phone = meta_info.get("phone_no")
    
    # Get or auto-generate beneId
    bene_id = payload.get("beneId")
    if not bene_id:
        # Auto-generate beneId: numeric string with timestamp and random digits
        timestamp = datetime.now().strftime("%y%m%d%H%M%S")
        random_suffix = ''.join(random.choices(string.digits, k=6))
        bene_id = f"{timestamp}{random_suffix}"
        logging.info(f"Auto-generated beneId: {bene_id}")
    
    # Validate required flat values
    command = payload.get("command")
    name = payload.get("name")
    ifsc = payload.get("ifsc")
    account = payload.get("account")
    
    if not customer_id:
        raise ValueError("'customerId' is required (provide in payload or configure in meta_info)")
    if not command:
        raise ValueError("'command' is required in the payload. Supported values: 'CREATE', 'VALIDATE'")
    if not name:
        raise ValueError("'name' is required in the payload")
    if not ifsc:
        raise ValueError("'ifsc' is required in the payload")
    if not account:
        raise ValueError("'account' is required in the payload")

    # Construct the API URL
    host = await get_juspay_host_from_api(meta_info=meta_info)
    api_url = f"https://api.juspay.in/payout/merchant/v2/benedetails"

    # Build nested beneDetails from flat values
    bene_details = {
        "type": "ACCOUNT_IFSC",
        "details": {
            "name": name,
            "ifsc": ifsc,
            "account": account
        }
    }

    # Build request body with required fields
    request_body = {
        "beneId": bene_id,
        "customerId": customer_id,
        "command": command,
        "beneDetails": bene_details
    }
    
    # Add optional fields if provided (from payload or meta_info)
    if email:
        request_body["email"] = email
    if phone:
        request_body["phone"] = phone

    # Prepare additional headers with Basic Authorization
    additional_headers = {
        "Content-Type": "application/json"
    }
    
    # Get API key from meta_info and add Basic Authorization
    api_key = meta_info.get("juspay_api_key")
    if api_key:
        # Base64 encode the API key for Basic Authorization
        encoded_key = base64.b64encode(api_key.encode()).decode()
        additional_headers["Authorization"] = f"Basic {encoded_key}"
        logging.info("Using Basic Authorization from meta_info API key")
    
    # Get merchant ID from meta_info
    merchant_id = meta_info.get("juspay_merchant_id")
    if merchant_id:
        additional_headers["x-merchantid"] = merchant_id
    
    # Add routing ID header (use customer_id as default)
    routing_id = customer_id
    if routing_id:
        additional_headers["x-routing-id"] = routing_id

    logging.info(f"Validating beneficiary: {api_url} with body: {request_body}")
    
    return await post(api_url, request_body, additional_headers, meta_info)
