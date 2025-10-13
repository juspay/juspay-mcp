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

from juspay_mcp import response_schema
from juspay_mcp.api import *
import juspay_mcp.api_schema as api_schema
import juspay_mcp.utils as util

logger = logging.getLogger(__name__)
app = Server("juspay")

AVAILABLE_TOOLS = [
    util.make_api_config(
        name="session_api_juspay",
        description="Creates a new Juspay session for a given order.",
        model=api_schema.session.JuspaySessionPayload,
        handler=session.session_api_juspay,
        response_schema=response_schema.session_response_schema,
    ),
    util.make_api_config(
        name="order_status_api_juspay",
        description="Retrieves the status of a specific Juspay order using its `order_id`.",
        model=api_schema.order.JuspayOrderStatusPayload,
        handler=order.order_status_api_juspay,
        response_schema=response_schema.order_status_response_schema,
    ),

    util.make_api_config(
        name="create_txn_juspay",
        description="Creates an order and processes payment in a single API call.",
        model=api_schema.txn.JuspayCreateTxnPayload,
        handler=txn.create_txn_juspay,
        response_schema=response_schema.create_txn_response_schema,
    ),
    util.make_api_config(
        name="list_offers_juspay",
        description="Lists available offers for a given order with optional coupon code.",
        model=api_schema.offer.JuspayListOffersPayload,
        handler=offer.list_offers_juspay,
        response_schema=response_schema.list_offers_response_schema,
    ),
    util.make_api_config(
        name="create_order_juspay",
        description="Creates a new order in Juspay payment system.",
        model=api_schema.order.JuspayCreateOrderPayload,
        handler=order.create_order_juspay,
        response_schema=response_schema.create_order_response_schema,
    ),

    util.make_api_config(
        name="create_cash_txn_juspay",
        description="Creates a CASH transaction for offline/cash-on-delivery payments.",
        model=api_schema.txn.JuspayCashTxnPayload,
        handler=txn.create_cash_txn_juspay,
        response_schema=response_schema.create_txn_response_schema,
    ),
    util.make_api_config(
        name="create_card_txn_juspay",
        description="Creates a CARD transaction using a saved card token. CRITICAL : Also requires `card_security_code` (CVV) to be passed. Prompt the user to enter CVV if it is not provided.",
        model=api_schema.txn.JuspayCardTxnPayload,
        handler=txn.create_card_txn_juspay,
        response_schema=response_schema.create_txn_response_schema,
    ),
    util.make_api_config(
        name="get_saved_payment_methods",
        description="Retrieves a customer's saved payment methods.",
        model=api_schema.upi.JuspaySavedPaymentMethodsPayload,
        handler=upi.get_saved_payment_methods,
        response_schema=response_schema.saved_payment_methods_response_schema,
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
async def handle_tool_calls(name: str, arguments: dict, meta_info: dict = None) -> list[types.TextContent]:
    logger.info(f"Calling tool: {name} with args: {arguments} and meta_info: {meta_info}")
    try:
        # Extract meta_info from arguments if present, or use provided meta_info
        current_meta_info = arguments.get("juspay_meta_info", meta_info or {})
        
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
        if model_cls:
            try:
                payload = model_cls(**arguments)  
                payload_dict = payload.dict(exclude_none=True) 
            except Exception as e:
                raise ValueError(f"Validation error: {str(e)}")
        else:
            payload_dict = arguments 
        
        # Remove meta_info from arguments to avoid passing it to API functions as regular parameter
        if "juspay_meta_info" in arguments:
            arguments.pop("juspay_meta_info")

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
        logger.error(f"Error executing tool {name}: {e}")
        return [types.TextContent(type="text", text=f"ERROR: Tool execution failed: {str(e)}")]
