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

TENANT_HOST_MAP_ENV = "JUSPAY_TENANT_HOST_MAP"


def _normalize_base_url(value: str) -> str:
    """Turn a bare host or a full URL into a scheme-qualified base URL."""
    value = value.strip().rstrip("/")
    if "://" not in value:
        value = f"https://{value}"
    return value


def _load_tenant_host_map() -> dict[str, str]:
    """Parse the tenant-id -> host mapping from the environment.

    Expected shape: JUSPAY_TENANT_HOST_MAP='{"juspay":"api.juspay.in"}'
    Values may be bare hosts (https:// is assumed) or full URLs. A missing or
    malformed value yields an empty map, which makes `resolve_base_url` fall
    back to JUSPAY_BASE_URL.
    """
    raw = os.getenv(TENANT_HOST_MAP_ENV)
    if not raw or not raw.strip():
        logger.info("%s not set; all requests use %s", TENANT_HOST_MAP_ENV, JUSPAY_BASE_URL)
        return {}

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error("%s is not valid JSON (%s); ignoring it", TENANT_HOST_MAP_ENV, e)
        return {}

    if not isinstance(parsed, dict):
        logger.error("%s must be a JSON object, got %s; ignoring it", TENANT_HOST_MAP_ENV, type(parsed).__name__)
        return {}

    mapping: dict[str, str] = {}
    for tenant_id, host in parsed.items():
        tenant_id = str(tenant_id).strip()
        if not tenant_id or not isinstance(host, str) or not host.strip():
            logger.error("%s: skipping malformed entry %r -> %r", TENANT_HOST_MAP_ENV, tenant_id, host)
            continue
        mapping[tenant_id] = _normalize_base_url(host)

    logger.info("Loaded tenant host map for tenants: %s", sorted(mapping))
    return mapping


TENANT_HOST_MAP = _load_tenant_host_map()


def resolve_base_url(juspay_creds: dict | None = None) -> str:
    """Resolve the base URL for the current request.

    Precedence:
      1. `x-tenant-id` looked up in JUSPAY_TENANT_HOST_MAP.
      2. JUSPAY_BASE_URL, derived from JUSPAY_ENV.
    """
    tenant_id = ((juspay_creds or {}).get("tenant_id") or "").strip()

    if tenant_id:
        host = TENANT_HOST_MAP.get(tenant_id)
        if host:
            return host
        if TENANT_HOST_MAP:
            logger.warning(
                "Tenant '%s' is not present in %s; falling back to the default host",
                tenant_id,
                TENANT_HOST_MAP_ENV,
            )
        else:
            logger.warning(
                "Received tenant '%s' but %s is not configured; falling back to the default host",
                tenant_id,
                TENANT_HOST_MAP_ENV,
            )

    return JUSPAY_BASE_URL


def build_api_url(path: str, juspay_creds: dict | None = None) -> str:
    """Join an ENDPOINTS path onto the base URL resolved for this request.

    Absolute URLs are passed through untouched.
    """
    if path.startswith(("http://", "https://")):
        return path
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{resolve_base_url(juspay_creds)}{path}"


# Paths only — the base URL is resolved per request by `build_api_url`, because
# a tenant supplied via `x-tenant-id` can change the host on every call.
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
