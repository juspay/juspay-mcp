# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

"""
Juspay Docs MCP Tools - Provides documentation retrieval tools for Juspay integration.
"""

import json
import os
import logging
from contextvars import ContextVar
from juspay_docs_mcp.mcpdoc.main import create_server

logger = logging.getLogger(__name__)

# Context variable to store Juspay credentials for the current request
juspay_request_credentials: ContextVar[dict | None] = ContextVar('juspay_request_credentials', default=None)

def set_juspay_request_credentials(credentials):
    """Set Juspay credentials for the current request context."""
    juspay_request_credentials.set(credentials)
    
def get_juspay_request_credentials():
    """Get Juspay credentials from current request context."""
    return juspay_request_credentials.get()


# Instructions for the MCP server
instructions = [
    "Official Juspay Technologies MCP tools useful to help merchants integrate with Juspay SDKs, APIs, Stack. Juspay is a Payment Aggregator whose aim is to make digital payments democratized and robust.",
    "Juspay provides 3 types of integration on a high level to a merchat (use the official documentation to get a comprehensive understanding) :",
    "1. Payment-Page / Express Checkout : Hosted UI which merchant can use with a single call to Juspay SDK",
    "2. Headless Express Checkout : An SDK which simplifies the contract to all Juspay APIs with some basic UIs like loader, OTP screen etc. The merchant builds their own payment page but invoke corresponding function on the Headless SDK to handle invoking Juspay Payment APIs",
    "3. API Integration: S2S integration where merchant directly calls Juspay Rest APIs",
    "",
    "The Juspay SDKs are cross platform built on inhouse build cross-platform framework like react-native. When a merchant wants to interact with Juspay SDKs, the communication is divided into two actions `initiate` and `process`. This contract in seamless across SDKs either payment-page or headless integrations.",
    "When a merchant is using payment-page, the merchant call initiate and process calls on Juspay SDK with a service identifier of `in.juspay.hyperpay`, which loads Juspay's native UI on a specific platform. On attempting payment from Juspay's UI the corresponding actions are invoked on the headless SDK by the Juspay Payment Page to do payment / call  Juspay APIs.",
    "When a merchant wants to use headless SDK, they use `in.juspay.ec` as the service identifies and directly call the headless SDK.",
    "All SDKs actions are process calls which only works when a Juspay SDK is initiated, so on load of merchant cart view, merchant is advised to initiate Juspay SDKs (which doesn't render any UI) and on corresponding user actions merchant do the process calls to finally load payment-page or do the payment in headless mode.",
    "Invoking Juspay SDKs invoke `initiate` & `process` in the correct order, to receive updates / responses from Juspay SDKs, callbacks are used. A merchant on instantiating Juspay SDK registers a callback which gets updates in a specific format depending on the action. The callback is very important to accurately handle journeys from merchant UI to Juspay UI and back. For example backpress actions, API responses, use payment responses (process_result) all are supposed to be handled within this callback.",
    "This is a high level brief intro to how Juspay SDKs are supposed to be used, read the documentation to fully understand the integrations with examples payloads for different payment-methods",
    "",
    "",
    "## CRITICAL: Required Information Workflow",
    "**STOP AND READ CAREFULLY BEFORE PROCEEDING FURTHER**",
    "It's important to note that while mocking also, you can never mock client id and merchant id. These are unique identifiers assigned to each merchant by Juspay and are essential for processing payments and identifying the merchant's account within the Juspay system.",
    "You can only mock data in payloads like amount, order id, customer details, payment method details etc. But client id and merchant id must always be valid and correspond to an actual merchant account in Juspay's system.",
    "**STOP: Before providing ANY integration guidance or using documentation tools, you MUST gather these details:**",
    "Required Information:",
    "1. **merchant_id** - Juspay merchant identifier",
    "2. **integration_type** - Payment Page / Headless / API",
    "3. **platform** - iOS / Android / Web / React Native",
    "4. **auth_method** - Signature-based or API Key-based",
    "5. **backend_endpoint** - (if signature auth) Merchant's order creation API",
    "",
    "To navigate the documentations and handle user queries about Juspay SDKs / APIs: ",
    "- 1. First fetch the document sources available",
    "- 2. Then always fetch the overviews / base integrations pages which explains the entire architecture with possible integrations.",
    "- 3. When the context and requirement is clear, proceed with user query"
]

# Documentation sources
doc_sources = [
    {
        "name": "Name: Juspay Payment Page - CAT\n\n",
        "llms_txt": "https://juspay.io/in/docs/hyper-checkout/llms.txt",
        "description": "Official documentation of Juspay Technologies. Documentation contains info about the Juspay APIs, Platform specific SDKs, Payment Integrations for different environments and other payment services. To navigate this effectively, try to narrow down the platform, environment required."
    },
    {
        "name": "Name: Juspay Payment Page - Signature Flow\n\n",
        "llms_txt": "https://juspay.io/in/docs/payment-page-enterprise/llms.txt",
        "description": "Official documentation of Juspay Technologies. Documentation contains info about the Juspay APIs, Platform specific SDKs, Payment Integrations for different environments and other payment services. To navigate this effectively, try to narrow down the platform, environment required."
    },
    {
        "name": "Name: Juspay API Docs\n\nOfficial documentation of Juspay Technologies. Documentation contains info about the Juspay APIs, and other payment services. To navigate this effectively try to read overview and integration architecture before doing anything.",
        "llms_txt": "https://juspay.io/in/docs/ec-api-global/llms.txt",
        "description": "Official documentation of Juspay Technologies. Documentation contains info about the Juspay APIs, and other payment services. To navigate this effectively try to read overview and integration architecture before doing anything."
    },
    {
        "name": "Name: Juspay EC - Express Checkout Headless Docs\n\nOfficial documentation of Juspay Express Checkout. Documentation contains info about the Juspay EC Headless APIs including wallets, cards, UPI, Netbanking, BNPL, Rewards payment methods and other payment services. To navigate this effectively, try to narrow down the platform, environment required.",
        "llms_txt": "https://juspay.io/in/docs/ec-headless/llms.txt",
        "description": "Official documentation of Juspay EC Headless. Documentation contains info about the Juspay EC Headless APIs including wallets, cards, UPI, Netbanking, BNPL, Rewards payment methods and other payment services. To navigate this effectively, try to narrow down the platform, environment required."
    },
    {
        "name": "Name: Juspay Airborne \n Airborne empowers developers to effortlessly integrate Over-The-Air (OTA) update capabilities into their Android, iOS, and React Native applications",
        "llms_txt": "https://raw.githubusercontent.com/juspay/airborne/refs/heads/airborne-documentation/docs/llms-full.txt",
        "description": "This document provides a comprehensive, step-by-step guide to all Airborne components with hierarchical organization and links to specific documentation sections."
    }
]

# Load transcripts
def _load_transcripts():
    """Load transcripts from the transcripts.json file."""
    transcripts_path = os.path.join(os.path.dirname(__file__), "transcripts.json")
    try:
        with open(transcripts_path, "r") as f:
            transcripts = json.load(f)
            return {str(k): str(v) for k, v in transcripts.items()}
    except FileNotFoundError:
        logger.warning(f"Transcripts file not found at {transcripts_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.warning(f"Error decoding transcripts JSON: {e}")
        return {}

transcripts_map = _load_transcripts()

# Create the MCP server
mcp = create_server(
    doc_sources,
    follow_redirects=True,
    timeout=30.0,
    transcripts_map=transcripts_map,
    server_instructions="\n".join(instructions),
)

app = mcp._mcp_server
