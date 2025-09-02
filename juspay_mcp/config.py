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

def verify_dynamic_credentials(juspay_creds: dict):
    """Verifies that required Juspay credentials are present in the auth context."""
    if not juspay_creds:
        raise ValueError("No Juspay credentials found in authentication context")
    
    api_key = juspay_creds.get("api_key")
    merchant_id = juspay_creds.get("merchant_id")
    
    if not api_key or not merchant_id:
        raise ValueError("Missing api_key or merchant_id in Juspay credentials")

def get_base64_auth(api_key: str = None):
    """Returns the base64 encoded auth string."""
    if api_key:
        auth_string = f"{api_key}:"
    else:
        verify_env_vars() 
        auth_string = f"{JUSPAY_API_KEY}:"
    return base64.b64encode(auth_string.encode()).decode()

def get_common_headers(routing_id: str | None = None, juspay_creds: dict = None):
    """
    Returns common headers used by all API calls.
    Uses the provided routing_id, or defaults to JUSPAY_MERCHANT_ID if None.
    If juspay_creds is provided, uses dynamic credentials; otherwise falls back to env vars.
    """
    if juspay_creds:
        verify_dynamic_credentials(juspay_creds)
        api_key = juspay_creds["api_key"]
        merchant_id = juspay_creds["merchant_id"]
        effective_routing_id = routing_id or merchant_id
        
        return {
            "Authorization": f"Basic {get_base64_auth(api_key)}",
            "x-merchantid": merchant_id,
            "x-routing-id": effective_routing_id,
            "Accept": "application/json",
            "x-request-id": f"mcp-tool-{os.urandom(6).hex()}" 
        }
    else:
        # Fallback to environment variables
        verify_env_vars()
        effective_routing_id = routing_id or JUSPAY_MERCHANT_ID
        return {
            "Authorization": f"Basic {get_base64_auth()}",
            "x-merchantid": JUSPAY_MERCHANT_ID,
            "x-routing-id": effective_routing_id,
            "Accept": "application/json",
            "x-request-id": f"mcp-tool-{os.urandom(6).hex()}" 
        }

def get_json_headers(routing_id: str | None = None, juspay_creds: dict = None):
    """Returns headers for JSON content type."""
    headers = get_common_headers(routing_id, juspay_creds)
    headers["Content-Type"] = "application/json"
    return headers

def get_form_headers(routing_id: str | None = None, juspay_creds: dict = None):
    """Returns headers for form URL-encoded content type."""
    headers = get_common_headers(routing_id, juspay_creds)
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    return headers
