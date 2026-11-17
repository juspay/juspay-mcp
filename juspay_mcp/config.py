# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import os
import base64
import dotenv
import json
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

def _normalize_base_url(value: str) -> str:
    """Turn a bare host or a full URL into a scheme-qualified base URL."""
    value = value.strip().rstrip("/")
    if "://" not in value:
        value = f"https://{value}"
    return value


def build_api_url(path: str) -> str:
    """Join an ENDPOINTS path onto JUSPAY_BASE_URL.

    Absolute URLs are passed through untouched.
    """
    if path.startswith(("http://", "https://")):
        return path
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{JUSPAY_BASE_URL}{path}"


# Paths only — `build_api_url` prefixes them with JUSPAY_BASE_URL.
ENDPOINTS = {
    "session": "/session",
    "refund": "/orders/{order_id}/refunds",

    # Customer APIs
    "customer": "/customers/{customer_id}",
    "create_customer": "/customers",
    "update_customer": "/customers/{customer_id}",

    # Order APIs
    "order_status": "/orders/{order_id}",
    "create_order": "/orders",
    "update_order": "/orders/{order_id}",
    "order_fulfillment": "/orders/{order_id}/fulfillment",
    "txn_refund": "/refunds",
    "create_txn": "/txns",

    # Card APIs
    "card_add": "/card/add",
    "cards": "/cards",
    "card_delete": "/card/delete",
    "card_update": "/card/update",
    "card_info": "/cardbins",
    "bin_list": "/v2/bins/eligibility",

    # UPI APIs
    "saved_payment_methods": "/customers/{customer_id}/payment_methods",
    "verify_vpa": "/v2/upi/verify-vpa",
    # Note: UPI collect and UPI intent both use the create_txn endpoint which is already defined

    # Offer APIs
    "offer_list": "/v1/offers/list",
    "offer_order_status": "/orders/{order_id}",

    # Wallet APIs
    "list_wallets": "/customers/{customer_id}/wallets"
}

def verify_env_vars():
    """Verifies that required environment variables are set."""
    if not JUSPAY_API_KEY or not JUSPAY_MERCHANT_ID:
        logger.error("JUSPAY_API_KEY or JUSPAY_MERCHANT_ID not set in environment variables.")
        raise ValueError("JUSPAY_API_KEY and JUSPAY_MERCHANT_ID environment variables must be set.")

def resolve_credentials(juspay_creds: dict | None = None) -> tuple[str, str]:
    """Resolve (api_key, merchant_id) for this request, one field at a time.

    A request-supplied value always wins; the environment is the per-field
    fallback. Resolving each field independently is what lets an agent pass
    `merchant_id` in a tool payload while the API key still comes from the
    static header or the environment — the two no longer have to arrive
    together.
    """
    creds = juspay_creds or {}
    api_key = (creds.get("api_key") or JUSPAY_API_KEY or "").strip()
    merchant_id = (creds.get("merchant_id") or JUSPAY_MERCHANT_ID or "").strip()

    missing = [
        name
        for name, value in (("api_key", api_key), ("merchant_id", merchant_id))
        if not value
    ]
    if missing:
        raise ValueError(
            f"Missing Juspay credentials: {', '.join(missing)}. Supply them per request "
            "(JUSPAY_API_KEY / JUSPAY_MERCHANT_ID headers, or a merchant_id in the tool "
            "payload) or set the JUSPAY_API_KEY / JUSPAY_MERCHANT_ID environment variables."
        )

    return api_key, merchant_id

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
    Each credential is resolved independently by `resolve_credentials`: a
    request-supplied api_key/merchant_id wins, the environment fills the rest.
    Uses the provided routing_id, or defaults to the resolved merchant_id.
    """
    api_key, merchant_id = resolve_credentials(juspay_creds)

    return {
        "Authorization": f"Basic {get_base64_auth(api_key)}",
        "x-merchant-id": merchant_id, # ideally this should be updated to x-merchantid, post payments service starts accepting it
        "x-routing-id": routing_id or merchant_id,
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
