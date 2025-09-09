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

JUSPAY_ENV = os.getenv("JUSPAY_ENV", "production").lower() 
JUSPAY_WEB_LOGIN_TOKEN = os.getenv("JUSPAY_WEB_LOGIN_TOKEN")

if JUSPAY_ENV == "production":
    JUSPAY_BASE_URL = os.getenv("JUSPAY_PROD_BASE_URL", "https://portal.juspay.in")
    logger.info("Using Juspay Production Environment")
else:
    JUSPAY_BASE_URL = os.getenv("JUSPAY_SANDBOX_BASE_URL", "https://sandbox.portal.juspay.in")
    logger.info("Using Juspay Sandbox Environment")

def verify_env_vars():
    """ 
    Verifies that all required environment variables are set.
    """

    if not JUSPAY_WEB_LOGIN_TOKEN:
        raise ValueError("JUSPAY_WEB_LOGIN_TOKEN environment variable must be set.")

def verify_dynamic_credentials(juspay_creds: dict):
    """Verifies that required Juspay credentials are present in the auth context."""
    if not juspay_creds:
        raise ValueError("No Juspay credentials found in authentication context")
    
    dashboard_token = juspay_creds.get("dashboard_token")
    
    if not dashboard_token:
        raise ValueError("Missing dashboard_token in Juspay credentials")

def get_base64_auth():
    """Returns the base64 encoded auth string."""
    pass


def get_common_headers(payload: dict, meta_info: dict = None, juspay_creds: dict = None):
    """
    Returns common headers used by all API calls.
    If juspay_creds is provided, uses dynamic credentials; otherwise falls back to env vars and meta_info.
    """
    if juspay_creds:
        # Use dynamic credentials from headers
        verify_dynamic_credentials(juspay_creds)
        token = juspay_creds["dashboard_token"]
    else:
        # Fallback to original logic
        if "x-web-logintoken" not in (meta_info or {}):
            verify_env_vars()

        if meta_info:
            token = meta_info.get("x-web-logintoken", JUSPAY_WEB_LOGIN_TOKEN)
        else:
            token = JUSPAY_WEB_LOGIN_TOKEN

    default_headers = {
        "Content-Type": "application/json",
        "accept": "*/*",
        "x-request-id": f"mcp-tool-{os.urandom(6).hex()}",
        "x-web-logintoken": f"{token}",
    }

    if payload.get("tenant_id"):
        default_headers["x-tenant-id"] = payload.pop("tenant_id")

    if payload.get("cookie"):
        default_headers["cookie"] = payload.pop("cookie")

    if payload.get("x-source-id"):
        default_headers["x-source-id"] = payload.pop("x-source-id")
    else:
        default_headers["x-source-id"] = "juspay-mcp"

    return default_headers
