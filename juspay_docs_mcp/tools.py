# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

"""
Juspay Docs MCP Tools - Provides documentation retrieval and migration tools for Juspay integration.
"""

import json
import os
import logging
from typing import Annotated, Optional, Literal
from pydantic import Field
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

# === Intent-Based Juspay Integration Tools ===
# PSP-agnostic: any AI agent provides an intent + platform, gets Juspay code from .md files.

JUSPAY_DOC_BASE = "https://juspay.io/in/docs/hyper-checkout"
JUSPAY_EC_DOC_BASE = "https://juspay.io/in/docs/ec-headless"
JUSPAY_API_DOC_BASE = "https://juspay.io/in/docs/ec-api-global"

PLATFORM_DOC_MAP = {
    "web": "web",
    "android": "android",
    "ios": "ios",
    "react_native": "react-native",
    "flutter": "flutter",
}

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "skills")

# All available intents — each maps to a .md file in skills/
AVAILABLE_INTENTS = {
    # Flows (start here to understand the full picture)
    "flow_hypercheckout": "Complete end-to-end payment flow for HyperCheckout (Payment Page). Covers: prerequisites → SDK init → session creation → payment page → response → verification → webhooks. Start here for hosted UI integrations.",
    "flow_express_checkout": "Complete end-to-end flow for Express Checkout (Headless SDK). Covers: customer creation → order creation → payment methods → custom UI → payment → verification. Start here for custom UI integrations.",
    # Individual intents
    "environment_setup": "Set up environment variables, API keys, and credentials for Juspay integration.",
    "customer_management": "Create and retrieve customers via Juspay API. Required for Express Checkout; optional for HyperCheckout (auto-created by /session).",
    "create_order_session": "Create an order and payment session on the server. Returns payment_links (web) or sdk_payload (native SDKs).",
    "sdk_setup": "Install and configure the Juspay SDK for the target platform (dependencies, gradle, pods, etc.).",
    "initiate_sdk": "Initialize the Juspay SDK on app/screen load. Must complete before opening payment page. (Not needed for web.)",
    "open_payment_page": "Launch the Juspay payment UI — redirect/iframe on web, or SDK process() call on native platforms.",
    "handle_payment_response": "Handle the payment result from the SDK callback or return_url redirect. Includes server-side verification.",
    "order_status": "Check order status via server-to-server API call. Used to verify payments before fulfilling orders.",
    "refund": "Process a refund via server-to-server API call.",
    "webhook": "Handle incoming Juspay webhook notifications on your server.",
}


def _load_skill(intent: str) -> str:
    """Load a skill markdown file by intent name."""
    filepath = os.path.join(SKILLS_DIR, f"{intent}.md")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: Skill file not found at {filepath}"
    except Exception as e:
        return f"Error reading skill file: {str(e)}"


def _inject_values(content: str, platform: str, merchant_id: str | None = None, client_id: str | None = None) -> str:
    """Replace placeholders in skill content with actual values."""
    platform_doc = PLATFORM_DOC_MAP.get(platform, platform)
    if merchant_id:
        content = content.replace("<MERCHANT_ID>", merchant_id)
    if client_id:
        content = content.replace("<CLIENT_ID>", client_id)
    content = content.replace("{DOC_BASE}", JUSPAY_DOC_BASE)
    content = content.replace("{EC_DOC_BASE}", JUSPAY_EC_DOC_BASE)
    content = content.replace("{API_DOC_BASE}", JUSPAY_API_DOC_BASE)
    content = content.replace("{platform}", platform_doc)
    return content


# ── MCP Tool Definitions ──

@mcp.tool()
def list_juspay_intents() -> str:
    """
    List all available Juspay integration intents.

    Returns the set of payment intents you can query, each with a description.
    Use this to understand what Juspay code snippets are available.

    After finding the right intent, call `get_juspay_code` with the intent and platform.

    This tool is PSP-agnostic — it works whether you're migrating from Adyen, Stripe,
    Razorpay, Braintree, PayPal, or building a new integration from scratch.
    """
    result = "# Available Juspay Integration Intents\n\n"
    result += "Call `get_juspay_code(intent, platform)` with any of these intents:\n\n"

    result += "## START HERE: Full Integration Flows\n"
    result += "These give you the complete picture — step-by-step from start to finish:\n\n"
    result += "1. **`flow_hypercheckout`** — " + AVAILABLE_INTENTS["flow_hypercheckout"] + "\n"
    result += "2. **`flow_express_checkout`** — " + AVAILABLE_INTENTS["flow_express_checkout"] + "\n"

    result += "\n## Individual Intents (for specific steps)\n"
    step_order = [
        "environment_setup",
        "customer_management",
        "sdk_setup",
        "create_order_session",
        "initiate_sdk",
        "open_payment_page",
        "handle_payment_response",
        "order_status",
        "webhook",
        "refund",
    ]

    for i, intent in enumerate(step_order, 1):
        desc = AVAILABLE_INTENTS[intent]
        result += f"{i}. **`{intent}`** — {desc}\n"

    result += "\n## Supported Platforms\n"
    result += "- `web` — Browser (redirect or iframe, no SDK package needed)\n"
    result += "- `android` — Native Android (HyperSDK via Gradle)\n"
    result += "- `ios` — Native iOS (HyperSDK via CocoaPods)\n"
    result += "- `react_native` — React Native (hyper-sdk-react via npm)\n"
    result += "- `flutter` — Flutter (hypersdkflutter via pub.dev)\n"

    result += "\n## Migration Workflow\n"
    result += "To migrate from any PSP to Juspay:\n"
    result += "1. Start with `flow_hypercheckout` or `flow_express_checkout` to understand the full picture\n"
    result += "2. Identify which intents your current code implements\n"
    result += "3. Call `get_juspay_code` for each intent + your platform\n"
    result += "4. Replace existing PSP code with the returned Juspay code\n"
    result += "5. Use `validate_juspay_integration` when done\n"
    result += "\n**IMPORTANT:** Before calling `get_juspay_code`, ask the merchant for:\n"
    result += "- **Juspay Merchant ID** (from Dashboard > Settings > Profile)\n"
    result += "- **Juspay Client ID** (from Dashboard > Settings > Profile)\n"
    result += "These are NEVER mockable.\n"

    return result


@mcp.tool()
def get_juspay_code(
    intent: Annotated[
        Literal[
            "flow_hypercheckout",
            "flow_express_checkout",
            "environment_setup",
            "customer_management",
            "create_order_session",
            "sdk_setup",
            "initiate_sdk",
            "open_payment_page",
            "handle_payment_response",
            "order_status",
            "refund",
            "webhook",
        ],
        Field(description="The payment integration intent. Start with 'flow_hypercheckout' or 'flow_express_checkout' for the full picture."),
    ],
    platform: Annotated[
        Literal["web", "android", "ios", "react_native", "flutter"],
        Field(description="Target platform"),
    ],
    merchant_id: Annotated[
        Optional[str],
        Field(description="Juspay Merchant ID. Required for sdk_setup, initiate_sdk, create_order_session. Must be a real value from Juspay Dashboard, not a placeholder."),
    ] = None,
    client_id: Annotated[
        Optional[str],
        Field(description="Juspay Client ID. Required for sdk_setup, initiate_sdk, create_order_session. Must be a real value from Juspay Dashboard, not a placeholder."),
    ] = None,
) -> str:
    """
    Get production-ready Juspay code for a specific payment intent and platform.

    This tool is PSP-AGNOSTIC — it works for migration from any payment provider
    (Adyen, Stripe, Razorpay, Braintree, PayPal) or for new integrations.

    The AI agent should:
    1. Analyze the merchant's existing code to identify which intents are used
    2. Call this tool for each intent to get the Juspay equivalent
    3. Replace the existing PSP code with the returned Juspay code

    For intents that need credentials (sdk_setup, initiate_sdk, create_order_session),
    you MUST provide merchant_id and client_id. Ask the merchant for these first.

    Returns: Complete code snippet with API details, code examples (multi-language
    for server-side intents), configuration, and links to official Juspay documentation.
    Use `fetch_docs` to get the latest docs for any URL returned.
    """
    if intent not in AVAILABLE_INTENTS:
        return (
            f"Unknown intent '{intent}'.\n"
            f"Available intents: {', '.join(AVAILABLE_INTENTS.keys())}"
        )

    # Load the skill markdown file
    content = _load_skill(intent)
    if content.startswith("Error:"):
        return content

    # Inject credentials and doc URLs
    content = _inject_values(content, platform, merchant_id, client_id)

    # Add header
    header = f"**Intent:** `{intent}` | **Platform:** `{platform}`"
    if merchant_id:
        header += f" | **Merchant:** `{merchant_id}`"
    if client_id:
        header += f" | **Client:** `{client_id}`"
    header += "\n\n---\n"

    # Add credential warning if needed
    needs_creds = intent in ("sdk_setup", "initiate_sdk", "create_order_session")
    if needs_creds and (not merchant_id or not client_id):
        header += (
            "\n> **WARNING:** merchant_id and/or client_id were not provided. "
            "Placeholders `<MERCHANT_ID>` / `<CLIENT_ID>` are in the code below. "
            "Ask the merchant for real values from Juspay Dashboard before using this code.\n\n"
        )

    return header + content


@mcp.tool()
def validate_juspay_integration(
    platform: Annotated[
        Literal["web", "android", "ios", "react_native", "flutter"],
        Field(description="The platform being validated"),
    ],
    has_session_api: Annotated[bool, Field(description="Backend: Session/order creation endpoint implemented?")],
    has_order_status_api: Annotated[bool, Field(description="Backend: Order status endpoint implemented?")],
    has_refund_api: Annotated[bool, Field(description="Backend: Refund endpoint implemented?")],
    has_webhook_handler: Annotated[bool, Field(description="Backend: Webhook handler implemented?")],
    has_sdk_setup: Annotated[bool, Field(description="Frontend: SDK installed and configured?")],
    has_payment_page: Annotated[bool, Field(description="Frontend: Payment page launch implemented?")],
    has_response_handling: Annotated[bool, Field(description="Frontend: Payment response handling implemented?")],
    has_server_side_verification: Annotated[bool, Field(description="Security: Order Status API called server-side before fulfilling orders?")],
    has_sandbox_test: Annotated[bool, Field(description="Testing: Full payment flow tested in Juspay sandbox?")],
) -> str:
    """
    Validate that a Juspay integration is complete.

    Call this after implementing all intents to get a pass/fail checklist.
    For any failed check, call `get_juspay_code` with the relevant intent to get the code.
    """
    platform_doc = PLATFORM_DOC_MAP.get(platform, platform)
    checks = [
        ("Backend: Session API", has_session_api, True, "create_order_session"),
        ("Backend: Order Status API", has_order_status_api, True, "order_status"),
        ("Backend: Refund API", has_refund_api, False, "refund"),
        ("Backend: Webhook Handler", has_webhook_handler, True, "webhook"),
        ("Frontend: SDK Setup", has_sdk_setup, True, "sdk_setup"),
        ("Frontend: Payment Page", has_payment_page, True, "open_payment_page"),
        ("Frontend: Response Handling", has_response_handling, True, "handle_payment_response"),
        ("Security: Server-Side Verification", has_server_side_verification, True, "order_status"),
        ("Testing: Sandbox Tested", has_sandbox_test, True, None),
    ]

    passed = sum(1 for _, ok, _, _ in checks if ok)
    total = len(checks)
    critical_fails = [(name, intent) for name, ok, crit, intent in checks if not ok and crit]

    report = f"# Juspay Integration Validation — {platform}\n\n"
    report += f"**Score: {passed}/{total}** ({passed/total*100:.0f}%)\n\n"

    if not critical_fails and passed == total:
        report += "## Status: READY FOR PRODUCTION\n\n"
    elif critical_fails:
        report += "## Status: NOT READY — CRITICAL ISSUES\n\n"
    else:
        report += "## Status: MOSTLY READY — MINOR ISSUES\n\n"

    report += "| Check | Status | Fix |\n|---|---|---|\n"
    for name, ok, critical, intent in checks:
        status = "PASS" if ok else ("**FAIL (critical)**" if critical else "FAIL")
        fix = ""
        if not ok and intent:
            fix = f'`get_juspay_code("{intent}", "{platform}")`'
        elif not ok:
            fix = f"Test in sandbox: `fetch_docs(\"{JUSPAY_DOC_BASE}/{platform_doc}/resources/test-resources.md\")`"
        report += f"| {name} | {status} | {fix} |\n"

    if passed == total:
        report += "\n**Next steps:**\n"
        report += "1. Switch `JUSPAY_BASE_URL` to `https://api.juspay.in`\n"
        report += "2. Update SDK environment to `production`\n"
        report += "3. Use production API keys\n"

    return report


app = mcp._mcp_server
