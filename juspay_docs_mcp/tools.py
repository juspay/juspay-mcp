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

# === Migration Skills ===

# Available migration skills
migration_skills = [
    {
        "source_psp": "adyen",
        "name": "Adyen to Juspay Migration Skill",
        "file": "adyen_to_juspay.md",
        "description": "Complete migration guide from Adyen (Drop-in, Sessions, Components, API) to Juspay (HyperCheckout, Express Checkout, API). Covers all platforms: Web, Android, iOS, React Native, Flutter.",
        "platforms": ["web", "android", "ios", "react_native", "flutter"],
        "covers": [
            "session/order creation",
            "frontend SDK integration",
            "webhooks",
            "order status",
            "refunds",
            "payment result handling",
            "environment variables",
            "dependency management",
            "testing",
            "production readiness",
        ],
    },
]

# Juspay doc URLs for validation
JUSPAY_DOC_BASE = "https://juspay.io/in/docs/hyper-checkout"
JUSPAY_PLATFORM_MAP = {
    "web": "web",
    "android": "android",
    "ios": "ios",
    "react_native": "react-native",
    "flutter": "flutter",
}


def _load_skill_file(filename: str) -> str:
    """Load a migration skill file from the skills directory."""
    skills_dir = os.path.join(os.path.dirname(__file__), "skills")
    filepath = os.path.join(skills_dir, filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: Skill file not found: {filename}"
    except Exception as e:
        return f"Error reading skill file: {str(e)}"


@mcp.tool()
def list_migration_skills(
    source_psp: Annotated[
        str,
        Field(description="The payment service provider you are migrating FROM (e.g., 'adyen'). Case-insensitive."),
    ],
) -> str:
    """
    List available migration skills for moving from a source payment provider to Juspay.

    Migration skills are comprehensive, step-by-step guides that cover:
    - Credential and environment mapping
    - Backend API migration (session creation, webhooks, refunds, order status)
    - Frontend SDK migration for all supported platforms
    - Testing and production readiness checklists

    Call this tool first to see what migrations are available.
    Then use `get_migration_skill` to fetch the full migration guide.

    Currently supported source PSPs: adyen
    Future support planned for: stripe, razorpay, braintree, paypal
    """
    source = source_psp.strip().lower()
    matching = [s for s in migration_skills if s["source_psp"] == source]

    if not matching:
        available = list(set(s["source_psp"] for s in migration_skills))
        return (
            f"No migration skill found for '{source_psp}'.\n\n"
            f"Available source PSPs: {', '.join(available)}\n\n"
            "If you need a migration from a different PSP, the general approach is:\n"
            "1. Use `list_doc_sources` to find Juspay integration documentation\n"
            "2. Use `fetch_docs` to read the integration guide for your target platform\n"
            "3. Manually map your current PSP's concepts to Juspay equivalents"
        )

    result = f"# Migration Skills: {source_psp.title()} -> Juspay\n\n"
    for skill in matching:
        result += f"## {skill['name']}\n"
        result += f"**Description:** {skill['description']}\n\n"
        result += f"**Supported Platforms:** {', '.join(skill['platforms'])}\n\n"
        result += f"**Covers:**\n"
        for item in skill["covers"]:
            result += f"- {item}\n"
        result += "\n"

    result += (
        "---\n\n"
        "**Next step:** Call `get_migration_skill` with the following parameters:\n"
        f"- `source_psp`: \"{source}\"\n"
        "- `platform`: your target platform (web, android, ios, react_native, flutter)\n"
        "- `merchant_id`: your Juspay Merchant ID (from Juspay Dashboard)\n"
        "- `client_id`: your Juspay Client ID (from Juspay Dashboard)\n\n"
        "**IMPORTANT:** You MUST ask the merchant for their actual `merchant_id` and `client_id` values. "
        "These cannot be mocked or placeholder values."
    )
    return result


@mcp.tool()
def get_migration_skill(
    source_psp: Annotated[
        str,
        Field(description="The payment provider migrating FROM (e.g., 'adyen')"),
    ],
    platform: Annotated[
        Literal["web", "android", "ios", "react_native", "flutter"],
        Field(description="The target platform for migration"),
    ],
    merchant_id: Annotated[
        str,
        Field(description="The merchant's Juspay Merchant ID from the Juspay Dashboard. MUST be a real value, not a placeholder."),
    ],
    client_id: Annotated[
        str,
        Field(description="The merchant's Juspay Client ID from the Juspay Dashboard. MUST be a real value, not a placeholder."),
    ],
) -> str:
    """
    Fetch the complete migration skill document for migrating from a source PSP to Juspay.

    This returns a comprehensive, step-by-step migration guide that any AI agent can follow.
    The guide includes code examples, concept mappings, and validation checklists.

    IMPORTANT:
    - merchant_id and client_id MUST be real values from the Juspay Dashboard
    - DO NOT use placeholder values like "your_merchant_id" or "test_merchant"
    - Ask the merchant to provide these values before calling this tool

    After receiving the skill document:
    1. Read through the entire document first to understand the full scope
    2. Follow the phases in order (Phase 0 through Phase 10)
    3. Replace all placeholder values (<YOUR_MERCHANT_ID>, <YOUR_CLIENT_ID>) with the actual values
    4. Focus on the platform-specific sections relevant to the merchant's platform
    5. After migration, use `validate_juspay_integration` to verify completeness
    6. Use `fetch_docs` to look up any Juspay documentation URLs referenced in the skill
    """
    source = source_psp.strip().lower()
    matching = [s for s in migration_skills if s["source_psp"] == source]

    if not matching:
        available = list(set(s["source_psp"] for s in migration_skills))
        return (
            f"No migration skill found for '{source_psp}'. "
            f"Available: {', '.join(available)}"
        )

    skill = matching[0]
    if platform not in skill["platforms"]:
        return (
            f"Platform '{platform}' is not supported for {skill['name']}. "
            f"Supported platforms: {', '.join(skill['platforms'])}"
        )

    # Load the skill file
    content = _load_skill_file(skill["file"])

    # Inject merchant-specific values
    content = content.replace("<YOUR_MERCHANT_ID>", merchant_id)
    content = content.replace("<YOUR_JUSPAY_CLIENT_ID>", client_id)
    content = content.replace("<YOUR_CLIENT_ID>", client_id)

    # Add platform-specific header
    platform_label = JUSPAY_PLATFORM_MAP.get(platform, platform)
    header = (
        f"# Migration Skill Loaded: {skill['name']}\n"
        f"**Target Platform:** {platform_label}\n"
        f"**Merchant ID:** {merchant_id}\n"
        f"**Client ID:** {client_id}\n\n"
        f"## Instructions for AI Agent\n"
        f"1. This document contains migration steps for ALL platforms. Focus on **{platform_label}** sections.\n"
        f"2. The backend migration (Phase 2) is platform-agnostic — always apply it.\n"
        f"3. For frontend, follow Phase 3 (Web), Phase 4 (Android), Phase 5 (iOS), Phase 6 (React Native), or Phase 7 (Flutter) as appropriate.\n"
        f"4. All placeholder values have been replaced with the merchant's actual credentials.\n"
        f"5. After completing migration, call `validate_juspay_integration` to verify.\n"
        f"6. For any doc URL in the checklist, use `fetch_docs` to get the latest documentation.\n\n"
        f"## Relevant Juspay Documentation URLs for {platform_label}\n"
        f"- Overview: {JUSPAY_DOC_BASE}/{platform_label}/overview/integration-architecture.md\n"
        f"- Session API: {JUSPAY_DOC_BASE}/{platform_label}/base-sdk-integration/session.md\n"
        f"- SDK Setup: {JUSPAY_DOC_BASE}/{platform_label}/base-sdk-integration/getting-sdk.md\n"
        f"- Webhooks: {JUSPAY_DOC_BASE}/{platform_label}/base-sdk-integration/webhooks.md\n"
        f"- Order Status: {JUSPAY_DOC_BASE}/{platform_label}/base-sdk-integration/order-status-api.md\n"
        f"- Refunds: {JUSPAY_DOC_BASE}/{platform_label}/base-sdk-integration/refund-order-api.md\n"
        f"- Test Resources: {JUSPAY_DOC_BASE}/{platform_label}/resources/test-resources.md\n"
        f"- Error Codes: {JUSPAY_DOC_BASE}/{platform_label}/resources/error-codes.md\n\n"
        f"---\n\n"
    )

    return header + content


@mcp.tool()
def validate_juspay_integration(
    platform: Annotated[
        Literal["web", "android", "ios", "react_native", "flutter"],
        Field(description="The platform being validated"),
    ],
    integration_type: Annotated[
        Literal["payment-page", "express-checkout", "api"],
        Field(description="The Juspay integration type used. 'payment-page' for HyperCheckout (recommended for Adyen Drop-in migrants), 'express-checkout' for Headless SDK, 'api' for direct API integration."),
    ],
    backend_session_api: Annotated[
        bool,
        Field(description="Has the backend session/order creation endpoint been migrated?"),
    ],
    backend_order_status_api: Annotated[
        bool,
        Field(description="Has the backend order status endpoint been migrated?"),
    ],
    backend_refund_api: Annotated[
        bool,
        Field(description="Has the backend refund endpoint been migrated?"),
    ],
    backend_webhook_handler: Annotated[
        bool,
        Field(description="Has the webhook handler been migrated?"),
    ],
    frontend_sdk_installed: Annotated[
        bool,
        Field(description="Has the Juspay SDK been installed for the target platform?"),
    ],
    frontend_sdk_initiate: Annotated[
        bool,
        Field(description="Has the SDK initiate call been implemented?"),
    ],
    frontend_sdk_process: Annotated[
        bool,
        Field(description="Has the SDK process call (payment page launch) been implemented?"),
    ],
    frontend_result_handling: Annotated[
        bool,
        Field(description="Has payment result handling been implemented with server-side verification?"),
    ],
    adyen_dependencies_removed: Annotated[
        bool,
        Field(description="Have all Adyen SDK packages and imports been removed?"),
    ],
    adyen_env_vars_removed: Annotated[
        bool,
        Field(description="Have all ADYEN_* environment variables been replaced with JUSPAY_* equivalents?"),
    ],
    sandbox_tested: Annotated[
        bool,
        Field(description="Has the integration been tested in Juspay sandbox?"),
    ],
    server_side_verification: Annotated[
        bool,
        Field(description="Is Order Status API called server-side to verify payment before fulfilling orders? This is a CRITICAL security requirement."),
    ],
) -> str:
    """
    Validate that a Juspay integration migration is complete and correct.

    This tool checks each component of the migration against Juspay's requirements
    and returns a detailed pass/fail report with remediation steps.

    Call this tool AFTER completing the migration to verify nothing was missed.
    For any failed checks, use `fetch_docs` to look up the relevant Juspay documentation.
    """
    platform_label = JUSPAY_PLATFORM_MAP.get(platform, platform)
    checks = []
    passed = 0
    failed = 0
    critical_failures = []

    def add_check(name: str, status: bool, category: str, critical: bool = False,
                  doc_path: str = "", remediation: str = ""):
        nonlocal passed, failed
        if status:
            passed += 1
            checks.append(f"  PASS  {category} > {name}")
        else:
            failed += 1
            entry = f"  FAIL  {category} > {name}"
            if remediation:
                entry += f"\n         -> {remediation}"
            if doc_path:
                doc_url = f"{JUSPAY_DOC_BASE}/{platform_label}/{doc_path}"
                entry += f"\n         -> Docs: {doc_url}"
            checks.append(entry)
            if critical:
                critical_failures.append(name)

    # Backend checks
    add_check(
        "Session/Order API migrated",
        backend_session_api,
        "Backend",
        critical=True,
        doc_path="base-sdk-integration/session.md",
        remediation="Implement POST /session endpoint. See Phase 2.2 in migration skill.",
    )
    add_check(
        "Order Status API migrated",
        backend_order_status_api,
        "Backend",
        critical=True,
        doc_path="base-sdk-integration/order-status-api.md",
        remediation="Implement GET /orders/{order_id} endpoint. See Phase 2.3 in migration skill.",
    )
    add_check(
        "Refund API migrated",
        backend_refund_api,
        "Backend",
        doc_path="base-sdk-integration/refund-order-api.md",
        remediation="Implement POST /orders/{order_id}/refunds endpoint. See Phase 2.4 in migration skill.",
    )
    add_check(
        "Webhook handler migrated",
        backend_webhook_handler,
        "Backend",
        critical=True,
        doc_path="base-sdk-integration/webhooks.md",
        remediation="Implement webhook handler with Basic Auth validation. Must return HTTP 200. See Phase 2.5 in migration skill.",
    )

    # Frontend checks
    if platform == "web":
        add_check(
            "Juspay payment page integration (redirect or iframe)",
            frontend_sdk_installed and frontend_sdk_process,
            "Frontend",
            critical=True,
            doc_path="base-sdk-integration/open-hypercheckout-screen.md",
            remediation="Web uses URL redirect or iframe. No SDK package needed. See Phase 3 in migration skill.",
        )
    else:
        add_check(
            "Juspay SDK installed",
            frontend_sdk_installed,
            "Frontend",
            critical=True,
            doc_path="base-sdk-integration/getting-sdk.md",
            remediation=f"Install Juspay HyperSDK for {platform_label}. See Phase {'4' if platform == 'android' else '5' if platform == 'ios' else '6' if platform == 'react_native' else '7'} in migration skill.",
        )
        add_check(
            "SDK initiate implemented",
            frontend_sdk_initiate,
            "Frontend",
            critical=True,
            doc_path="base-sdk-integration/initiating-sdk.md",
            remediation="Call hyperServices.initiate() / HyperSdkReact.initiate() / hyperSDK.initiate() on screen load.",
        )
        add_check(
            "SDK process implemented",
            frontend_sdk_process,
            "Frontend",
            critical=True,
            doc_path="base-sdk-integration/open-hypercheckout-screen.md",
            remediation="Call process() with sdk_payload from your backend /session endpoint.",
        )

    add_check(
        "Payment result handling implemented",
        frontend_result_handling,
        "Frontend",
        critical=True,
        doc_path="base-sdk-integration/handle-payment-response.md",
        remediation="Handle process_result event / return_url redirect. MUST verify server-side.",
    )

    # Security checks
    add_check(
        "Server-side order verification",
        server_side_verification,
        "Security",
        critical=True,
        doc_path="base-sdk-integration/order-status-api.md",
        remediation="CRITICAL: Always call Order Status API server-side before fulfilling orders. Never trust client-side status.",
    )

    # Cleanup checks
    add_check(
        "Adyen dependencies removed",
        adyen_dependencies_removed,
        "Cleanup",
        remediation="Remove all Adyen SDK packages (npm, gradle, pods, pub.dev) and imports.",
    )
    add_check(
        "Adyen env vars replaced",
        adyen_env_vars_removed,
        "Cleanup",
        remediation="Replace ADYEN_API_KEY, ADYEN_MERCHANT_ACCOUNT, ADYEN_CLIENT_KEY, ADYEN_HMAC_KEY with JUSPAY equivalents.",
    )

    # Testing check
    add_check(
        "Sandbox tested",
        sandbox_tested,
        "Testing",
        critical=True,
        doc_path="resources/test-resources.md",
        remediation="Test the full payment flow in Juspay sandbox before going to production.",
    )

    # Build report
    total = passed + failed
    score = (passed / total * 100) if total > 0 else 0

    report = f"# Juspay Integration Validation Report\n\n"
    report += f"**Platform:** {platform_label}\n"
    report += f"**Integration Type:** {integration_type}\n"
    report += f"**Score:** {passed}/{total} checks passed ({score:.0f}%)\n\n"

    if critical_failures:
        report += f"## CRITICAL FAILURES ({len(critical_failures)})\n"
        report += "These MUST be fixed before going to production:\n"
        for cf in critical_failures:
            report += f"- {cf}\n"
        report += "\n"

    if score == 100:
        report += "## Status: READY FOR PRODUCTION\n"
        report += "All checks passed. Proceed with:\n"
        report += "1. Switch `JUSPAY_BASE_URL` to `https://api.juspay.in`\n"
        report += "2. Update SDK environment to `production`\n"
        report += "3. Use production API keys from Juspay Dashboard\n"
        report += "4. Run a live test transaction with a real payment method\n\n"
    elif critical_failures:
        report += "## Status: NOT READY - CRITICAL ISSUES\n"
        report += "Fix the critical failures listed above before proceeding.\n\n"
    else:
        report += "## Status: MOSTLY READY - MINOR ISSUES\n"
        report += "No critical failures, but fix the remaining issues for a complete migration.\n\n"

    report += "## Detailed Results\n\n"
    report += "```\n"
    for check in checks:
        report += check + "\n"
    report += "```\n\n"

    report += "## Next Steps\n\n"
    if not sandbox_tested:
        report += "1. **Test in sandbox** - Use Juspay's Dummy PG for end-to-end testing\n"
        report += f"   Fetch test resources: `fetch_docs(\"{JUSPAY_DOC_BASE}/{platform_label}/resources/test-resources.md\")`\n\n"
    if failed > 0:
        report += "For any FAIL items above, use `fetch_docs` with the provided documentation URL to get detailed implementation guidance.\n\n"
    report += (
        "For comprehensive validation, also verify:\n"
        f"- Sample payloads: `fetch_docs(\"{JUSPAY_DOC_BASE}/{platform_label}/resources/sample-payloads.md\")`\n"
        f"- Error codes: `fetch_docs(\"{JUSPAY_DOC_BASE}/{platform_label}/resources/error-codes.md\")`\n"
        f"- Transaction statuses: `fetch_docs(\"{JUSPAY_DOC_BASE}/{platform_label}/resources/transaction-status.md\")`\n"
    )

    return report


app = mcp._mcp_server
