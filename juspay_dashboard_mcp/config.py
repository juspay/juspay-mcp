# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import os
import base64
import dotenv
import logging 
import json


logger = logging.getLogger(__name__)

dotenv.load_dotenv()

JUSPAY_DASHBOARD_IGNORE_TOOL = json.loads(os.getenv('DASHBOARD_TOOL_IGNORE_LIST', '["juspay_list_configured_gateway","juspay_get_gateway_scheme","juspay_get_gateway_details","juspay_list_gateway_scheme","juspay_get_merchant_gateways_pm_details","juspay_report_details","juspay_list_report","juspay_get_offer_details","juspay_list_offers","juspay_alert_details","juspay_list_alerts","q_api"]'))

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
    
def get_base64_auth():
    """Returns the base64 encoded auth string."""
    pass
    
def get_common_headers(payload: dict, meta_info: dict = None):
    """
    Returns common headers used by all API calls.
    Uses the provided routing_id, or defaults to JUSPAY_MERCHANT_ID if None.
    """
    if "x-web-logintoken" not in (meta_info or {}):
        verify_env_vars()

    token = meta_info.get("x-web-logintoken", JUSPAY_WEB_LOGIN_TOKEN)

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
