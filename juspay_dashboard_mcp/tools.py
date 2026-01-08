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
import juspay_dashboard_mcp.api_schema as api_schema
import juspay_dashboard_mcp.utils as util

logger = logging.getLogger(__name__)

app = Server("juspay-dashboard")

AVAILABLE_TOOLS = [
    util.make_api_config(
        name="juspay_create_payout_order",
        description="""

Creates a payout request with Juspay for bank account disbursement operations.

Accepts simple flat values (name, ifsc, account, amount) - nested fulfillments payload is constructed automatically.

Key features:
- Creates payout orders for bank account transfers
- Auto-generates orderId if not provided
- Auto-fills customer details (customerId, customerEmail, customerPhone) from meta_info
- Uses Basic Authorization (API key from meta_info)
- Hardcodes type as "FULFILL_ONLY" and beneficiaryDetails.type as "ACCOUNT_IFSC"

Required fields:
- amount: Payout amount in major currency unit (e.g., rupees)
- name: Beneficiary's name as per bank account
- ifsc: IFSC code of the bank branch
- account: Bank account number

Optional fields (taken from meta_info if not provided):
- orderId: Unique order ID (auto-generated if not provided)
- customerId: Customer identifier
- customerEmail: Email address
- customerPhone: Phone number
- remark: Optional remark for the transaction

Example minimal payload:
{
    "amount": 100.00,
    "name": "John Doe",
    "ifsc": "YESB0000262",
    "account": "026291800001191"
}

Use this tool to initiate bank account payouts using account number and IFSC.

Essential for payout operations, finance teams, and automated disbursement workflows.""",
        model=api_schema.payout_orders.JuspayCreatePayoutOrderPayload,
        handler=payout_orders.create_payout_order_juspay,
        response_schema=None,
    ),
  
   
    util.make_api_config(
        name="juspay_create_or_validate_beneficiary",
        description="""
    
Creates or validates a beneficiary bank account for payout operations.

Supports two commands:
- CREATE: Register a new beneficiary with bank account details
- VALIDATE: Verify existing beneficiary details before initiating payouts

Accepts simple flat values (name, ifsc, account) - nested payload is constructed automatically.

Key features:
- Validates/creates beneficiary bank account using IFSC + Account Number
- Auto-generates beneId if not provided
- Auto-fills customer details (customerId, email, phone) from meta_info
- Uses Basic Authorization (API key from meta_info)
- Hardcodes type as "ACCOUNT_IFSC"

Required fields:
- command: 'CREATE' or 'VALIDATE'
- name: Beneficiary's name as per bank account
- ifsc: IFSC code of the bank branch
- account: Bank account number

Optional fields (taken from meta_info if not provided):
- beneId: Unique reference ID (auto-generated if not provided)
- customerId: Customer identifier
- email: Email address
- phone: Phone number

Essential for payout operations teams to validate/create beneficiary information before disbursements.""",
        model=api_schema.payout_beneficiary_details.JuspayCreateOrValidateBeneficiaryPayload,
        handler=payout_beneficiary_details.create_or_validate_beneficiary_juspay,
        response_schema=None,
    ),
    util.make_api_config(
        name="juspay_get_payout_balance",
        description="""NOTE: Always use this tool when user asks the query what is my balance
    
Retrieves current balance information from all configured payout gateways. This tool provides visibility into available funds across different payout providers configured for disbursement operations.

Key features:
- Fetches balance information from all configured payout gateways
- Shows available funds across different payout providers
- Supports force refresh for real-time balance data
- Provides account details and fund availability

Use this tool to:
- Check available funds across payout gateways
- Monitor balance levels for disbursement operations
- Verify account status and fund availability
- Get real-time balance information when needed

Essential for finance teams and operations personnel to monitor fund availability for payout processing.""",
        model=api_schema.payout_gateways.JuspayGetPayoutBalancePayload,
        handler=payout_gateways.get_payout_balance_juspay,
        response_schema=None,
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
