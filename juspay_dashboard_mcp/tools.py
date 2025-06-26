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

from juspay_dashboard_mcp import response_schema
from juspay_dashboard_mcp.api import *
import juspay_dashboard_mcp.api_schema as api_schema
import juspay_dashboard_mcp.utils as util

logger = logging.getLogger(__name__)

app = Server("juspay-dashboard")

AVAILABLE_TOOLS = [
    util.make_api_config(
        name="juspay_list_configured_gateway",
        description=" Retrieves a list of all payment gateways (PGs) configured for a merchant, including high-level details such as gateway reference ID, creation/modification dates, configured payment methods (PMs) and configured payment flows. Note: Payment Method Types (PMTs), configured EMI plans, configured mandate/subscriptions payment methods (PMs) and configured TPV PMs are not included in the response.",
        model=api_schema.gateway.JuspayListConfiguredGatewaysPayload,
        handler=gateway.list_configured_gateways_juspay,
        response_schema=response_schema.list_configured_gateways_response_schema,
    ),
    util.make_api_config(
        name="juspay_get_gateway_scheme",
        description="This API provides detailed configuration information for a gateway, including required/optional fields, supported payment methods and supported features/payment flows for that gateway.",
        model=api_schema.gateway.JuspayGetGatewaySchemePayload,
        handler=gateway.get_gateway_scheme_juspay,
        response_schema=response_schema.get_gateway_scheme_response_schema,
    ),
    util.make_api_config(
        name="juspay_get_gateway_details",
        description="This API returns detailed information about a specific gateway configured by the merchant. Requires mga_id which can be fetched from juspay_list_configured_gateway. This API returns all details of the gateway including payment methods (PM), EMI plans, mandate/subscriptions payment methods (PMs) and TPV PMs along with configured payment flows. Note: This API does not return payment method type (PMT) for each configured payment method.",
        model=api_schema.gateway.JuspayGetGatewayDetailsPayload,
        handler=gateway.get_gateway_details_juspay,
        response_schema=response_schema.get_gateway_details_response_schema,
    ),
    util.make_api_config(
        name="juspay_list_gateway_scheme",
        description="This API returns a list of all available payment gateways that can be configured on PGCC. Doesn't contain any details only a list of available gateways for configuration on PGCC.",
        model=api_schema.gateway.JuspayListGatewaySchemePayload,
        handler=gateway.list_gateway_scheme_juspay,
        response_schema=response_schema.list_gateway_scheme_response_schema,
    ),
    util.make_api_config(
        name="juspay_get_merchant_gateways_pm_details",
        description="This API fetches all gateways and their supported payment methods configured for the merchant. Only this API will give payment method type (PMT) for each configured payment method. Doesn't include any other details except for gateway wise configured payment methods with payment method type.",
        model=api_schema.gateway.JuspayGetMerchantGatewaysPmDetailsPayload,
        handler=gateway.get_merchant_gateways_pm_details_juspay,
        response_schema=response_schema.get_merchant_gateways_pm_details_response_schema,
    ),
    util.make_api_config(
        name="juspay_report_details",
        description="This API returns detailed information for a specific report ID, including data sources, metrics, dimensions, and filters.",
        model=api_schema.report.JuspayReportDetailsPayload,
        handler=report.report_details_juspay,
        response_schema=response_schema.report_details_response_schema,
    ),
    util.make_api_config(
        name="juspay_list_report",
        description="This API lists all reports configured by the merchant, along with their status, recipients, thresholds, and monitoring intervals.",
        model=api_schema.report.JuspayListReportPayload,
        handler=report.list_report_juspay,
        response_schema=response_schema.list_report_response_schema,
    ),
    util.make_api_config(
        name="juspay_get_offer_details",
        description="This API retrieves detailed information for a specific offer including eligibility rules, benefit types, and configurations.",
        model=api_schema.offer.JuspayGetOfferDetailsPayload,
        handler=offer.get_offer_details_juspay,
        response_schema=response_schema.get_offer_details_response_schema,
    ),
    util.make_api_config(
        name="juspay_list_offers",
        description="This API lists all offers configured by the merchant, with details such as status, payment methods, offer codes, and validity periods. Requires `sort_offers` (e.g., {\"field\": \"CREATED_AT\", \"order\": \"DESCENDING\"}).",
        model=api_schema.offer.JuspayListOffersPayload,
        handler=offer.list_offers_juspay,
        response_schema=response_schema.list_offers_response_schema,
    ),
    util.make_api_config(
        name="juspay_get_user",
        description="This API fetches details for a specific user, identified by user ID.",
        model=api_schema.user.JuspayGetUserPayload,
        handler=user.get_user_juspay,
        response_schema=response_schema.get_user_response_schema,
    ),
    util.make_api_config(
        name="juspay_list_users_v2",
        description="This API retrieves a list of users associated with a merchant, with optional pagination.",
        model=api_schema.user.JuspayListUsersV2Payload,
        handler=user.list_users_v2_juspay,
        response_schema=response_schema.list_users_v2_response_schema,
    ),
    util.make_api_config(
        name="juspay_get_conflict_settings",
        description="This API retrieves conflict settings configuration for payment processing.",
        model=api_schema.settings.JuspayConflictSettingsPayload,
        handler=settings.get_conflict_settings_juspay,
        response_schema=response_schema.get_conflict_settings_response_schema,
    ),
    util.make_api_config(
        name="juspay_get_general_settings",
        description="This API retrieves general configuration settings for the merchant.",
        model=api_schema.settings.JuspayGeneralSettingsPayload,
        handler=settings.get_general_settings_juspay,
        response_schema=response_schema.get_general_settings_response_schema,
    ),
    util.make_api_config(
        name="juspay_get_mandate_settings",
        description="This API retrieves mandate-related settings for recurring payments.",
        model=api_schema.settings.JuspayMandateSettingsPayload,
        handler=settings.get_mandate_settings_juspay,
        response_schema=response_schema.get_mandate_settings_response_schema,
    ),
    util.make_api_config(
        name="juspay_get_priority_logic_settings",
        description="This API fetches a list of all configured priority logic rules, including their current status and full logic definition.",
        model=api_schema.settings.JuspayPriorityLogicSettingsPayload,
        handler=settings.get_priority_logic_settings_juspay,
        response_schema=response_schema.get_priority_logic_settings_response_schema,
    ),
    util.make_api_config(
        name="juspay_get_routing_settings",
        description="This API provides details of success rate-based routing thresholds defined by the merchant, including enablement status and downtime-based switching thresholds.",
        model=api_schema.settings.JuspayRoutingSettingsPayload,
        handler=settings.get_routing_settings_juspay,
        response_schema=response_schema.get_routing_settings_response_schema,
    ),
    util.make_api_config(
        name="juspay_get_webhook_settings",
        description="This API retrieves webhook configuration settings for the merchant.",
        model=api_schema.settings.JuspayWebhookSettingsPayload,
        handler=settings.get_webhook_settings_juspay,
        response_schema=response_schema.get_webhook_settings_response_schema,
    ),
    util.make_api_config(
        name="juspay_alert_details",
        description="Provides detailed information for a specific alert ID, including source, monitored metrics, and applied filters.",
        model=api_schema.alert.JuspayAlertDetailsPayload,
        handler=alert.alert_details_juspay,
        response_schema=response_schema.alert_details_response_schema,
    ),
    util.make_api_config(
        name="juspay_list_alerts",
        description="Retrieves all alerts configured by the merchant, including their status, recipients, thresholds, and monitoring intervals.",
        model=api_schema.alert.JuspayListAlertsPayload,
        handler=alert.list_alerts_juspay,
        response_schema=response_schema.list_alerts_response_schema,
    ),
    util.make_api_config(
        name="juspay_list_orders_v4",
        description="Retrieves a list of orders created within a specified time range. Supports an optional top-level 'limit' parameter and optional 'qFilters' for payment status and order type.",
        model=api_schema.orders.JuspayListOrdersV4Payload,
        handler=orders.list_orders_v4_juspay,
        response_schema=response_schema.list_orders_v4_response_schema,
    ),
    util.make_api_config(
        name="juspay_get_order_details",
        description="Returns complete details for a given order ID.",
        model=api_schema.orders.JuspayGetOrderDetailsPayload,
        handler=orders.get_order_details_juspay,
        response_schema=response_schema.get_order_details_response_schema,
    ),
    util.make_api_config(
        name="juspay_list_payment_links_v1",
        description="Retrieves a list of payment links created within a specified time range (mandatory). Supports filters from the transactions (txns) domain such as payment_status and order_type.",
        model=api_schema.payments.JuspayListPaymentLinksV1Payload,
        handler=payments.list_payment_links_v1_juspay,
        response_schema=response_schema.list_payment_links_v1_response_schema,
    ),
    util.make_api_config(
        name="juspay_list_surcharge_rules",
        description="No input required. Returns a list of all configured surcharge rules, including their current status and rule definitions.",
        model=api_schema.surcharge.JuspayListSurchargeRulesPayload,
        handler=surcharge.list_surcharge_rules_juspay,
        response_schema=response_schema.list_surcharge_rules_response_schema,
    ),
    util.make_api_config(
        name="q_api",
        description=api_schema.qapi.api_description,
        model=api_schema.qapi.ToolQApiPayload,
        handler=qapi.q_api,
        response_schema=None,
    ),
    util.make_api_config(
    name="rag_tool_juspay",
    description="Query the RAG (Retrieval Augmented Generation) system using Vertex AI for intelligent document retrieval and question answering. Requires a 'query' parameter with the question to ask the RAG system. Optional 'similarity_top_k' parameter controls the number of similar documents to retrieve (default: 20).",
    model=api_schema.rag_tool.JuspayRagQueryPayload,
    handler=rag_tool.rag_tool_juspay,
    response_schema=response_schema.rag_query_response_schema,
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
        for tool in AVAILABLE_TOOLS
    ]

@app.call_tool()
async def handle_tool_calls(name: str, arguments: dict) -> list[types.TextContent]:
    logger.info(f"Tool called: {name} with arguments: {arguments}")
    try:
        tool_entry = next((t for t in AVAILABLE_TOOLS if t["name"] == name), None)
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
        
        meta_info = arguments.pop("juspay_meta_info", None)

        sig = inspect.signature(handler)
        param_count = len(sig.parameters)

        if param_count == 0:
            response = await handler()

        elif param_count == 1:
            if arguments or not meta_info:
                response = await handler(arguments)
            else:
                response = await handler(meta_info)

        elif param_count == 2:
            response = await handler(arguments, meta_info)

        else:
            raise ValueError(f"Unsupported number of parameters in tool handler: {param_count}")
        return [types.TextContent(type="text", text=json.dumps(response))]

    except Exception as e:
        logger.error(f"Error in tool execution: {e}")
        return [types.TextContent(type="text", text=f"ERROR: Tool execution failed: {str(e)}")]
