# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import os
import base64
import dotenv
import logging 

logger = logging.getLogger(__name__)
dotenv.load_dotenv()

JUSPAY_API_KEY = os.getenv("JUSPAY_API_KEY")
JUSPAY_MERCHANT_ID = os.getenv("JUSPAY_MERCHANT_ID")
JUSPAY_ENV = os.getenv("JUSPAY_ENV", "sandbox").lower() 

if JUSPAY_ENV == "production":
    JUSPAY_BASE_URL = os.getenv("JUSPAY_PROD_BASE_URL", "https://api.juspay.in")
    logger.info("Using Juspay Production Environment")
else:
    JUSPAY_BASE_URL = os.getenv("JUSPAY_SANDBOX_BASE_URL", "https://sandbox.juspay.in")
    logger.info("Using Juspay Sandbox Environment")


ENDPOINTS = {
    "session": f"{JUSPAY_BASE_URL}/session",
    "refund": f"{JUSPAY_BASE_URL}/orders/{{order_id}}/refunds", 

    # Customer APIs
    "customer": f"{JUSPAY_BASE_URL}/customers/{{customer_id}}",
    "create_customer": f"{JUSPAY_BASE_URL}/customers",
    "update_customer": f"{JUSPAY_BASE_URL}/customers/{{customer_id}}",

    # Order APIs
    "order_status": f"{JUSPAY_BASE_URL}/orders/{{order_id}}",
    "create_order": f"{JUSPAY_BASE_URL}/orders",
    "update_order": f"{JUSPAY_BASE_URL}/orders/{{order_id}}",
    "order_fulfillment": f"{JUSPAY_BASE_URL}/orders/{{order_id}}/fulfillment",
    "txn_refund": f"{JUSPAY_BASE_URL}/refunds",
    "create_txn": f"{JUSPAY_BASE_URL}/txns",

    # Card APIs
    "card_add": f"{JUSPAY_BASE_URL}/card/add",
    "cards": f"{JUSPAY_BASE_URL}/cards",
    "card_delete": f"{JUSPAY_BASE_URL}/card/delete",
    "card_update": f"{JUSPAY_BASE_URL}/card/update", 
    "card_info": f"{JUSPAY_BASE_URL}/cardbins",
    "bin_list": f"{JUSPAY_BASE_URL}/v2/bins/eligibility",

    # UPI APIs
    "saved_payment_methods": f"{JUSPAY_BASE_URL}/customers/{{customer_id}}/payment_methods",
    "verify_vpa": f"{JUSPAY_BASE_URL}/v2/upi/verify-vpa",
    # Note: UPI collect and UPI intent both use the create_txn endpoint which is already defined

    # Offer APIs
    "offer_list": f"{JUSPAY_BASE_URL}/v1/offers/list",
    "offer_order_status": f"{JUSPAY_BASE_URL}/orders/{{order_id}}",

    # Wallet APIs
    "list_wallets": f"{JUSPAY_BASE_URL}/{{customer_id}}/wallets"
}

def verify_env_vars():
    """Verifies that required environment variables are set."""
    if not JUSPAY_API_KEY or not JUSPAY_MERCHANT_ID:
        logger.error("JUSPAY_API_KEY or JUSPAY_MERCHANT_ID not set in environment variables.")
        raise ValueError("JUSPAY_API_KEY and JUSPAY_MERCHANT_ID environment variables must be set.")

def get_base64_auth():
    """Returns the base64 encoded auth string."""
    verify_env_vars() 
    auth_string = f"{JUSPAY_API_KEY}:"
    return base64.b64encode(auth_string.encode()).decode()

def get_common_headers_with_meta_info(routing_id: str | None = None, meta_info: dict = None):
    """
    Returns common headers with meta_info support and env fallback.
    Priority: meta_info > environment variables
    """
    # Check if meta_info contains API key/merchant info
    api_key = None
    merchant_id = None
    
    if meta_info:
        logger.info(f"Using meta_info for authentication: {meta_info}")
        # Extract from meta_info if available
        api_key = meta_info.get("juspay_api_key")
        merchant_id = meta_info.get("juspay_merchant_id")
    
    # Fallback to environment variables
    if not api_key:
        verify_env_vars()  # Existing function
        api_key = JUSPAY_API_KEY
        merchant_id = JUSPAY_MERCHANT_ID
    
    # Generate auth header
    auth_string = f"{api_key}:"
    auth_header = base64.b64encode(auth_string.encode()).decode()
    
    # routing_id comes from function parameter, not meta_info
    effective_routing_id = routing_id or merchant_id
    
    return {
        "Authorization": f"Basic {auth_header}",
        "x-merchantid": merchant_id,
        "x-routing-id": effective_routing_id,
        "Accept": "application/json",
        "x-request-id": f"mcp-tool-{os.urandom(6).hex()}"
    }

def get_common_headers(routing_id: str | None = None, meta_info: dict = None):
    """
    Returns common headers used by all API calls.
    Uses the provided routing_id, or defaults to JUSPAY_MERCHANT_ID if None.
    Supports meta_info for authentication overrides with env variable fallback.
    """
    if meta_info is not None:
        return get_common_headers_with_meta_info(routing_id, meta_info)
    else:
        # Existing implementation for backward compatibility
        verify_env_vars()
        effective_routing_id = routing_id or JUSPAY_MERCHANT_ID
        return {
            "Authorization": f"Basic {get_base64_auth()}",
            "x-merchantid": JUSPAY_MERCHANT_ID,
            "x-routing-id": effective_routing_id,
            "Accept": "application/json",
            "x-request-id": f"mcp-tool-{os.urandom(6).hex()}"
        }

def get_json_headers(routing_id: str | None = None, meta_info: dict = None):
    """Returns headers for JSON content type with meta_info support."""
    headers = get_common_headers(routing_id, meta_info)
    headers["Content-Type"] = "application/json"
    return headers

def get_form_headers(routing_id: str | None = None, meta_info: dict = None):
    """Returns headers for form URL-encoded content type with meta_info support."""
    headers = get_common_headers(routing_id, meta_info)
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    return headers
