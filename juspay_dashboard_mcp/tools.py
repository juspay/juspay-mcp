# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import json
import mcp.types as types
import inspect
import logging
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from pydantic import BaseModel

from juspay_dashboard_mcp import response_schema
from juspay_dashboard_mcp.api import *
from juspay_dashboard_mcp.config import JUSPAY_DASHBOARD_IGNORE_TOOL
from juspay_dashboard_mcp.api import integrationCheklist
import juspay_dashboard_mcp.api_schema as api_schema
import juspay_dashboard_mcp.utils as util

logger = logging.getLogger(__name__)

app = Server("juspay-dashboard")

AVAILABLE_TOOLS = [
    util.make_api_config(
        name="juspay_list_configured_gateway",
        description="""Use this tool when asked about the list of payment gateways . Retrieves a list of all payment gateways (PGs) configured for a merchant, including high-level details such as gateway reference ID, creation/modification dates, configured payment methods (PMs) and configured payment flows. Note: Payment Method Types (PMTs), configured EMI plans, configured mandate/subscriptions payment methods (PMs) and configured TPV PMs are not included in the response.

Key features:
- Fetches a comprehensive list of all configured payment gateways.
- Provides gateway reference ID for each gateway.
- Shows creation and last modification dates.
- Lists configured payment methods (PMs) for each gateway.
- Details the payment flows enabled for each gateway.

Use this tool to get an overview of all active payment gateways for a merchant, understand which payment methods are configured on each gateway, and check basic configuration details. Essential for gateway management and initial diagnostics.""",
        model=api_schema.gateway.JuspayListConfiguredGatewaysPayload,
        handler=gateway.list_configured_gateways_juspay,
        response_schema=None,
    ),
    util.make_api_config(
        name="juspay_get_gateway_scheme",
        description="""Use this tool when asked about configuration information about a particular gateway . This API provides detailed configuration information for a gateway, including required/optional fields, supported payment methods and supported features/payment flows for that gateway.

Key features:
- Provides detailed configuration schema for a specific gateway.
- Lists all required and optional fields for gateway configuration.
- Shows all supported payment methods.
- Details supported features and payment flows (e.g., 3DS, AFT, etc.).

Use this tool to understand the configuration requirements and capabilities of a specific payment gateway before or during integration. Helpful for developers and integration engineers.""",
        model=api_schema.gateway.JuspayGetGatewaySchemePayload,
        handler=gateway.get_gateway_scheme_juspay,
        response_schema=None,
    ),
    util.make_api_config(
        name="juspay_get_gateway_details",
        description="""Use this tool when asked about detailed information about any gateway and mga_id is provided.This API returns detailed information about a specific gateway configured by the merchant. Requires mga_id which can be fetched from juspay_list_configured_gateway. This API returns all details of the gateway including payment methods (PM), EMI plans, mandate/subscriptions payment methods (PMs) and TPV PMs along with configured payment flows. Note: This API does not return payment method type (PMT) for each configured payment method.

Key features:
- Fetches all configuration details for a specific merchant gateway account (mga_id).
- Lists configured payment methods (PMs).
- Details configured EMI plans.
- Provides information on mandate/subscription payment methods.
- Includes details on Third-Party Validation (TPV) PMs.
- Shows all configured payment flows.

Use this tool to get a complete picture of a specific configured gateway, including all its payment methods and special configurations. Essential for deep-dive analysis and troubleshooting of a particular gateway setup.""",
        model=api_schema.gateway.JuspayGetGatewayDetailsPayload,
        handler=gateway.get_gateway_details_juspay,
        response_schema=None,
    ),
    util.make_api_config(
        name="juspay_list_gateway_scheme",
        description="""This API returns a list of all available payment gateways that can be configured on PGCC. Doesn't contain any details only a list of available gateways for configuration on PGCC.

Key features:
- Provides a simple list of all payment gateways available for configuration.
- Contains only the names/identifiers of the gateways.
- No detailed configuration information is included.

Use this tool to discover which payment gateways are available to be configured for a merchant on the Juspay platform. Useful for initial setup and exploring new gateway options.""",
        model=api_schema.gateway.JuspayListGatewaySchemePayload,
        handler=gateway.list_gateway_scheme_juspay,
        response_schema=None,
    ),
    util.make_api_config(
        name="juspay_get_merchant_gateways_pm_details",
        description="""This API fetches all gateways and their supported payment methods configured for the merchant. Only this API will give payment method type (PMT) for each configured payment method. Doesn't include any other details except for gateway wise configured payment methods with payment method type.

Key features:
- Lists all configured gateways for the merchant.
- Details all supported payment methods for each gateway.
- Crucially, provides the Payment Method Type (PMT) for each payment method.

Use this tool specifically when you need to know the Payment Method Type (PMT) for configured payment methods on each gateway. This is the only tool that provides this specific piece of information.""",
        model=api_schema.gateway.JuspayGetMerchantGatewaysPmDetailsPayload,
        handler=gateway.get_merchant_gateways_pm_details_juspay,
        response_schema=None,
    ),
    util.make_api_config(
        name="juspay_report_details",
        description="""This API returns detailed information for a specific report ID, including data sources, metrics, dimensions, and filters.

Key features:
- Fetches configuration details for a single report by its ID.
- Shows the data sources used for the report.
- Lists the metrics and dimensions included in the report.
- Details the filters applied to the report data.

Use this tool to understand how a specific report is constructed, what data it contains, and how it is filtered. Essential for validating report data and understanding its scope.""",
        model=api_schema.report.JuspayReportDetailsPayload,
        handler=report.report_details_juspay,
        response_schema=None,
    ),
    util.make_api_config(
        name="juspay_list_report",
        description="""This API lists all reports configured by the merchant, along with their status, recipients, thresholds, and monitoring intervals.

Key features:
- Retrieves a list of all configured reports for the merchant.
- Shows the status of each report (e.g., active, inactive).
- Lists the recipients (email, etc.) for each report.
- Details any configured thresholds for alerting.
- Provides the monitoring or generation interval for each report.

Use this tool to get an overview of all configured reports, check their status, and see who receives them. Useful for managing reporting and alerting configurations.""",
        model=api_schema.report.JuspayListReportPayload,
        handler=report.list_report_juspay,
        response_schema=None,
    ),
    util.make_api_config(
        name="juspay_get_offer_details",
        description="""This API retrieves detailed information for a specific offer including eligibility rules, benefit types, and configurations.

Key features:
- Fetches complete details for a single offer by its ID.
- Details the eligibility rules for customers and transactions.
- Explains the benefit type (e.g., discount, cashback).
- Provides all associated configurations.

Use this tool to understand the exact mechanics of a specific offer. Essential for troubleshooting offer application issues, verifying offer setup, and for customer support inquiries about a specific promotion.""",
        model=api_schema.offer.JuspayGetOfferDetailsPayload,
        handler=offer.get_offer_details_juspay,
        response_schema=None,
    ),
    util.make_api_config(
        name="juspay_list_offers",
        description="""This API lists all offers configured by the merchant, with details such as status, payment methods, offer codes, and validity periods. Requires `sort_offers` (e.g., {"field": "CREATED_AT", "order": "DESCENDING"}).

Key features:
- Retrieves a list of all offers for the merchant.
- Shows the status of each offer (e.g., active, expired).
- Lists applicable payment methods for each offer.
- Provides offer codes if applicable.
- Details the validity period for each offer.
- Supports sorting to organize the results.

Use this tool to get an overview of all available offers, check their status, and see their high-level applicability. Useful for marketing teams, and for getting a list of active promotions.""",
        model=api_schema.offer.JuspayListOffersPayload,
        handler=offer.list_offers_juspay,
        response_schema=None,
    ),
    util.make_api_config(
        name="juspay_get_user",
        description="""This API fetches details for a specific user, identified by user ID.

Key features:
- Retrieves profile information for a single user.
- Includes details associated with the user account.

Use this tool to look up the details of a specific user on the dashboard. Essential for user management and verifying user permissions.""",
        model=api_schema.user.JuspayGetUserPayload,
        handler=user.get_user_juspay,
        response_schema=None,
    ),
    util.make_api_config(
        name="juspay_list_users_v2",
        description="""This API retrieves a list of users associated with a merchant, with optional pagination.

Key features:
- Fetches a list of all users for a merchant account.
- Provides details for each user in the list.
- Supports pagination to handle large numbers of users.

Use this tool to get a list of all dashboard users for a merchant. Useful for auditing user access and managing user accounts.""",
        model=api_schema.user.JuspayListUsersV2Payload,
        handler=user.list_users_v2_juspay,
        response_schema=None,
    ),
    util.make_api_config(
        name="juspay_get_conflict_settings",
        description="""This API retrieves conflict settings configuration for payment processing.

Key features:
- Fetches the current conflict settings for the merchant.

Use this tool to check the conflict settings configuration for payment processing. Essential for developers and operations teams.""",
        model=api_schema.settings.JuspayConflictSettingsPayload,
        handler=settings.get_conflict_settings_juspay,
        response_schema=None,
    ),
    util.make_api_config(
        name="juspay_get_general_settings",
        description="""This API retrieves general configuration settings for the merchant.

Key features:
- Fetches a wide range of general account settings for the merchant.

Use this tool to get a broad overview of the merchant's primary configuration on Juspay. Useful for verifying basic setup and feature enablement.""",
        model=api_schema.settings.JuspayGeneralSettingsPayload,
        handler=settings.get_general_settings_juspay,
        response_schema=None,
    ),
    util.make_api_config(
        name="juspay_get_mandate_settings",
        description="""This API retrieves mandate-related settings for recurring payments.

Key features:
- Fetches all settings related to payment mandates for recurring payments.

Use this tool to understand how recurring payments and subscriptions are configured for the merchant. Essential for managing subscription-based services.""",
        model=api_schema.settings.JuspayMandateSettingsPayload,
        handler=settings.get_mandate_settings_juspay,
        response_schema=None,
    ),
    util.make_api_config(
        name="juspay_get_priority_logic_settings",
        description="""This API fetches a list of all configured priority logic rules, including their current status and full logic definition.

Key features:
- Retrieves all priority logic rules defined for the merchant.
- Shows the status of each rule.
- Provides the complete logical definition of each rule.

Use this tool to understand how payment gateways are prioritized for routing transactions. Essential for analyzing and troubleshooting payment routing decisions.""",
        model=api_schema.settings.JuspayPriorityLogicSettingsPayload,
        handler=settings.get_priority_logic_settings_juspay,
        response_schema=None,
    ),
    util.make_api_config(
        name="juspay_get_routing_settings",
        description="""This API provides details of success rate-based routing thresholds defined by the merchant, including enablement status and downtime-based switching thresholds.

Key features:
- Fetches settings for dynamic, success-rate-based routing.
- Shows the enablement status of the feature.
- Details the success rate thresholds for switching gateways.
- Provides configuration for downtime-based gateway switching.

Use this tool to check the configuration of automated, performance-based payment routing. Crucial for understanding how the system optimizes transaction success rates.""",
        model=api_schema.settings.JuspayRoutingSettingsPayload,
        handler=settings.get_routing_settings_juspay,
        response_schema=None,
    ),
    util.make_api_config(
        name="juspay_get_webhook_settings",
        description="""This API retrieves webhook configuration settings for the merchant.

Key features:
- Fetches the webhook configuration settings.

Use this tool to verify webhook configurations and troubleshoot notification delivery issues. Essential for developers integrating with Juspay's event system.""",
        model=api_schema.settings.JuspayWebhookSettingsPayload,
        handler=settings.get_webhook_settings_juspay,
        response_schema=None,
    ),
    util.make_api_config(
        name="juspay_alert_details",
        description="""Provides detailed information for a specific alert ID, including source, monitored metrics, and applied filters.

Key features:
- Fetches the complete configuration for a single alert by its ID.
- Identifies the data source being monitored.
- Details the specific metrics being tracked.
- Shows the applied filters that trigger the alert.

Use this tool to understand why a specific alert was triggered or to review the exact configuration of an alert. Essential for operations teams and developers responsible for system monitoring.""",
        model=api_schema.alert.JuspayAlertDetailsPayload,
        handler=alert.alert_details_juspay,
        response_schema=None,
    ),
    util.make_api_config(
        name="juspay_list_alerts",
        description="""Retrieves all alerts configured by the merchant, including their status, recipients, thresholds, and monitoring intervals.

Key features:
- Fetches a list of all alerts configured for the merchant.
- Shows the status of each alert (enabled/disabled).
- Lists the recipients for each alert notification.
- Details the trigger thresholds and conditions.
- Provides the monitoring interval for each alert.

Use this tool to get a complete overview of the monitoring and alerting setup for the merchant. Useful for auditing alerts and managing notification configurations.""",
        model=api_schema.alert.JuspayListAlertsPayload,
        handler=alert.list_alerts_juspay,
        response_schema=None,
    ),
    util.make_api_config(
        name="juspay_find_orders",
        description="""Powerful order search and listing tool designed for both finding sample order IDs for debugging/issue investigation and general order management. Retrieves orders within a specified time range with advanced filtering capabilities for troubleshooting and investigation.

Key features:
- Fetches orders within a given start and end time range
- Advanced filtering by payment status, order type, error messages, and more
- Search by specific transaction identifiers for order ID discovery:
  * epg_txn_id: Transaction ID at the payment gateway's end
  * txn_uuid: Unique identifier for transaction record in Juspay's system  
  * pgr_rrn: Bank-assigned Retrieval Reference Number for tracking
- Supports filtering by amount, error codes and error messages for troubleshooting
- Allows limiting the number of results and pagination
- Domain parameter is mandatory (use 'txnsELS' if unsure)

Investigation Use Cases:
- Find orders by specific transaction IDs when investigating payment issues
- Search for orders with specific error messages reported by merchants
- Filter by error codes or error messages to identify patterns in payment failures
- Locate sample orders for a particular date range when merchants report issues basis any filter info available (like amount, customer ID, card last four digits etc.)

General Use Cases:
- Generate order reports and reconcile transactions
- Get high-level view of order activity by status or type
- Search orders by payment method, gateway, or other criteria

Use this tool whenever you need to find specific orders for investigation, troubleshooting, or general order management tasks.

IMPORTANT: If unsure about the type of a provided ID, the agent should ask the user for clarification, providing the available ID fields (epg_txn_id, txn_uuid, pgr_rrn) as options to choose from.""",
        model=api_schema.orders.JuspayListOrdersV4Payload,
        handler=orders.list_orders_v4_juspay,
        response_schema=None,
    ),
    util.make_api_config(
        name="juspay_get_order_details",
        description="""Returns complete details for a given order ID. 

CRITICAL RETRY LOGIC: If you receive an error like "Order with id = 'xyz' does not exist", the provided ID is likely a transaction ID (txn_id) instead of an order ID. You MUST extract the order_id from the txn_id and retry the call.

Extraction patterns (ALWAYS follow these steps):
1. Remove the last '-' and number (e.g., '-1', '-2') from the end
2. If there's still a '-' and number at the end, remove that too (for silent retries)  
3. Take the part after the merchant prefix (usually after the first or second hyphen)

Examples:
- creditmantri-22087705-1 → 22087705
- paypal-juspay-JP_1752481545-1 → JP_1752481545
- zee5-6a45de15-6edd-4463-9415-f638a6709ee8-1 → 6a45de15-6edd-4463-9415-f638a6709ee8
- 6E-JFTWE26E7250714112817-1 → JFTWE26E7250714112817
- merchant-ORDER123-1-1 → ORDER123

MANDATORY: When you get "does not exist" error, immediately extract order_id using above patterns and call this tool again with the extracted order_id.

Key features:
- Fetches complete order details for a specific order ID (if txn_id provided extract order_id using above logic).
- Returns the amount in the major currency unit (e.g., rupees, dollars).


Use this tool to look up the status of a specific payment, troubleshoot a customer's order issue, verify transaction details for reconciliation, or fetch data for customer support inquiries. Essential for support teams, operations personnel, and developers who need to inspect the state of individual orders.""",
        model=api_schema.orders.JuspayGetOrderDetailsPayload,
        handler=orders.get_order_details_juspay,
        response_schema=None,
    ),
    util.make_api_config(
        name="juspay_list_payment_links_v1",
        description="""Retrieves a list of payment links created within a specified time range (mandatory). Supports filters from the transactions (txns) domain such as payment_status and order_type.

Key features:
- Fetches a list of payment links created between a start and end time.
- Allows filtering by payment status.
- Supports filtering by order type.

Use this tool to search for payment links, check their status, or generate reports on link usage. Useful for support teams and for tracking payments made via links.""",
        model=api_schema.payments.JuspayListPaymentLinksV1Payload,
        handler=payments.list_payment_links_v1_juspay,
        response_schema=None,
    ),
    util.make_api_config(
        name="juspay_list_surcharge_rules",
        description="""No input required. Returns a list of all configured surcharge rules, including their current status and rule definitions.

Key features:
- Fetches all surcharge rules configured for the merchant.
- Shows the status of each rule.
- Provides the full definition of each rule.

Use this tool to review and audit all configured surcharge rules. Essential for understanding how and when additional fees are applied to transactions.""",
        model=api_schema.surcharge.JuspayListSurchargeRulesPayload,
        handler=surcharge.list_surcharge_rules_juspay,
        response_schema=None,
    ),
    util.make_api_config(
        name="q_api",
        description=api_schema.qapi.api_description,
        model=api_schema.qapi.ToolQApiPayload,
        handler=qapi.q_api,
        response_schema=None,
    ),
    util.make_api_config(
        name="list_outages_juspay",
        description="""Returns a list of outages within a specified time range.

Key features:
- Fetches a list of all recorded outages within a given time frame.
- Provides details for each outage, including start and end times, status, and affected components (like payment method).
- Converts outage period timestamps to IST in the response.

Use this tool to check for any service disruptions or performance degradation issues. Essential for monitoring system health and understanding the impact of outages on payment processing.""",
        model=api_schema.outages.JuspayListOutagesPayload,
        handler=outages.list_outages_juspay,
        response_schema=response_schema.list_outages_response_schema,
    ),
    util.make_api_config(
        name="create_payment_link_juspay",
        description="""Use this tool when asked to create a payment link.
IMPORTANT: You must ask the user for the required fields (amount), do not assume any of these fields always prompt the user.
Also, if the user asks to send an email, prompt the user to specify the email (shouldSendMail should be enabled), and similarly if the user asks to send SMS (shouldSendSMS should be enabled) or WhatsApp message (shouldSendWhatsapp should be enabled), prompt the user to ask for the mobile number if not already specified.
If the user does not ask to send the email , WhatsApp message or SMS then do not mark the fields - shouldSendMail,shouldSendSMS and shouldSendWhatsapp as true.
CRITICAL: Do not assume or auto-generate these values -  prompt the user to provide them explicitly if they ask for it.
NOTE: If any EMI option is enabled in payment_filter.emiOptions, at least one card type (credit/debit/cardless) must be enabled within that EMI type.
EMI OPTIONS: If the user requests EMI options, ask them to choose from: 1) Standard EMI (standardEmi), 2) Low Cost EMI (lowCostEmi), 3) No Cost EMI (noCostEmi).
For each selected EMI type, ask which card types to enable: credit cards (standard_credit/low_cost_credit/no_cost_credit), debit cards (standard_debit/low_cost_debit/no_cost_debit), or cardless EMI (standard_cardless/low_cost_cardless/no_cost_cardless).
Please note that it's extremely necessary to ask the user which EMI OPTIONS they want if the user asks for them.
Set showEmiOption to true only if any EMI option is requested.
RECREATE FROM ORDER: If the user asks to recreate a payment link and provides an order ID, first call the 'juspay_get_order_details' tool with that order_id to fetch the existing order details, then use those details (amount, customer information, payment methods, etc.) to create a new payment link with the same parameters.
CRITICAL : If all the necessary parameters are provided do not ask for confirmation from the user, directly create the payment link.
""",
        model=api_schema.payments.JuspayCreatePaymentLinkPayload,
        handler=payments.create_payment_link_juspay,
        response_schema=None,
    ),
    util.make_api_config(
        name="create_autopay_link_juspay",
        description="""Use this tool when asked to create an autopay payment link or recurring payment link or mandate payment link.
IMPORTANT: You must ask the user for ALL required fields (amount, mandate_max_amount, mandate_start_date, mandate_end_date, mandate_frequency), do not assume any of these fields always prompt the user.
Also, if the user asks to send an email, prompt the user to specify the email (shouldSendMail should be enabled), and similarly if the user asks to send SMS (shouldSendSMS should be enabled) or WhatsApp message (shouldSendWhatsapp should be enabled), prompt the user to ask for the mobile number if not already specified , the user should be prompted for the email ID and phone number if they want to send email and sms or Whatsapp message.
If the user does not ask to send the email , WhatsApp message or SMS then do not mark the fields - shouldSendMail,shouldSendSMS and shouldSendWhatsapp as true.
CRITICAL: Do not assume or auto-generate these values - prompt the user to provide them explicitly if they ask for it.
NOTE: If any EMI option is enabled in payment_filter.emiOptions, at least one card type (credit/debit/cardless) must be enabled within that EMI type.
EMI OPTIONS: If the user requests EMI options, prompt them to choose from: 1) Standard EMI (standardEmi), 2) Low Cost EMI (lowCostEmi), 3) No Cost EMI (noCostEmi).
For each selected EMI type, ask which card types to enable: credit cards (standard_credit/low_cost_credit/no_cost_credit), debit cards (standard_debit/low_cost_debit/no_cost_debit), or cardless EMI (standard_cardless/low_cost_cardless/no_cost_cardless), Please note that it's extremely necessary to ask the user which EMI OPTIONS they want if the user asks for them.
Set showEmiOption to true only if any EMI option is requested.
RECREATE FROM ORDER: If the user asks to recreate an autopay payment link and provides an order ID, first call the 'juspay_get_order_details' tool with that order_id to fetch the existing order details, then use those details (amount, customer information, mandate details, payment methods, etc.) to create a new autopay payment link with the same parameters.
CRITICAL : If all the necessary parameters are provided do not ask for confirmation from the user, directly create the autopay payment link.
""",
        model=api_schema.payments.JuspayCreateAutopayLinkPayload,
        handler=payments.create_autopay_link_juspay,
        response_schema=None,
    ),
  
    util.make_api_config(
        name="juspay_integration_monitoring_status",
        description="""Retrieves integration monitoring status for merchant's product integrations across different platforms.

This tool automatically routes to the appropriate API based on platform:
- Backend platform: Uses agnostic API (platform-independent monitoring)
- Web/Android/iOS platforms: Uses nonagnostic API (platform-specific monitoring)

Key features:
- Platform-aware API routing (agnostic vs nonagnostic)
- Time-range based monitoring data
- Success rate and total transaction metrics
- Stage-wise breakdown of integration status
- Feature-wise analysis (base, mandate, payout, etc.)
- Critical vs non-critical stage identification
- Visibility conditions and results for each stage

Required inputs:
- platform: Must be one of "Backend", "Web", "Android", "iOS"
- product_integrated: Must be one of "Payment Page Signature", "Payment Page Session", "EC + SDK", "EC Only"
- merchant_id: Merchant ID
- start_time: Start time in ISO format (YYYY-MM-DDTHH:MM:SSZ)
- end_time: End time in ISO format (YYYY-MM-DDTHH:MM:SSZ)

Time format example: "2025-08-03T00:00:00Z"

Response includes:
- Overall score data with critical and total success counts
- Feature-wise breakdown (base, mandate, payout, etc.)
- Section-wise analysis (e.g., "Payments Flow Checklist")
- Individual stage details with status, criticality, and visibility conditions
- Module metadata including platform dependencies and minimum hit requirements

Use this tool to monitor integration health, track success rates, analyze platform-specific performance metrics, and identify critical integration issues that need attention.""",
        model=api_schema.integrationCheklist.JuspayIntegrationMonitoringPayload,
        handler=integrationCheklist.get_integration_monitoring_status_juspay,
        response_schema=response_schema.integration_monitoring_status_response_schema,
    ),
]

@app.list_tools()
async def list_my_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name=tool["name"],
            description=tool["description"],
            inputSchema=tool["schema"],
        )
        for tool in AVAILABLE_TOOLS if tool["name"] not in JUSPAY_DASHBOARD_IGNORE_TOOL
    ]

@app.call_tool()
async def handle_tool_calls(
    name: str, arguments: dict, meta_info: dict = None
) -> list[types.TextContent]:
    logger.info(f"Tool called: {name} with arguments: {arguments} and meta_info: {meta_info}")
    try:
        current_meta_info = arguments.get("juspay_meta_info", meta_info or {})

        is_hdfc = False
        if current_meta_info:
            token_response = current_meta_info.get("token_response")
            if token_response and isinstance(token_response, dict):
                is_hdfc = token_response.get("validHost") in [
                    "dashboard.smartgateway.hdfcbank.com/", 
                    "dashboard.smartgateway.hdfcbank.com",
                    "dashboarduat.smartgatewayuat.hdfcbank.com",
                    "dashboarduat.smartgatewayuat.hdfcbank.com/"
                ]
        for tool in AVAILABLE_TOOLS:
            if tool["name"] in ["create_payment_link_juspay", "create_autopay_link_juspay"]:
                if is_hdfc:
                    tool["description"] = tool["description"].replace(
                        "IMPORTANT: You must ask the user for the required fields (amount, payment_page_client_id)",
                        "IMPORTANT: You must ask the user for the required fields (amount)"
                    ).replace(
                        "IMPORTANT: You must ask the user for ALL required fields (amount, payment_page_client_id, mandate_max_amount, mandate_start_date, mandate_end_date, mandate_frequency)",
                        "IMPORTANT: You must ask the user for ALL required fields (amount, mandate_max_amount, mandate_start_date, mandate_end_date, mandate_frequency)"
                    )
                else:
                    tool["description"] = tool["description"].replace(
                        "IMPORTANT: You must ask the user for the required fields (amount)",
                        "IMPORTANT: You must ask the user for the required fields (amount, payment_page_client_id)"
                    ).replace(
                        "IMPORTANT: You must ask the user for ALL required fields (amount, mandate_max_amount, mandate_start_date, mandate_end_date, mandate_frequency)",
                        "IMPORTANT: You must ask the user for ALL required fields (amount, payment_page_client_id, mandate_max_amount, mandate_start_date, mandate_end_date, mandate_frequency)"
                    )

        tool_entry = next((t for t in AVAILABLE_TOOLS if t["name"] == name and t["name"] not in JUSPAY_DASHBOARD_IGNORE_TOOL), None)
        if not tool_entry:
            raise ValueError(f"Unknown tool: {name}")

        schema = tool_entry["schema"]
        required = schema.get("required", [])
        missing = [key for key in required if key not in arguments]
        if missing:
            raise ValueError(f"Missing required fields for {name}: {missing}")

        handler = tool_entry["handler"]
        if not handler:
            raise ValueError(f"No handler defined for tool: {name}")

        model_cls = tool_entry.get("model")
        if (model_cls):
            try:
                payload = model_cls(**arguments)  
                payload_dict = payload.dict(exclude_none=True) 
            except Exception as e:
                raise ValueError(f"Validation error: {str(e)}")
        else:
            payload_dict = arguments 
        
        if isinstance(current_meta_info, BaseModel):
            current_meta_info = current_meta_info.model_dump()

        sig = inspect.signature(handler)
        param_count = len(sig.parameters)

        if param_count == 0:
            response = await handler()
        elif param_count == 1:
            if arguments or not current_meta_info:
                response = await handler(arguments)
            else:
                response = await handler(current_meta_info)
        elif param_count == 2:
            response = await handler(arguments, current_meta_info)
        else:
            raise ValueError(f"Unsupported number of parameters in tool handler: {param_count}")
        return [types.TextContent(type="text", text=json.dumps(response))]

    except Exception as e:
        logger.error(f"Error in tool execution: {e}")
        return [types.TextContent(type="text", text=f"ERROR: Tool execution failed: {str(e)}")]
