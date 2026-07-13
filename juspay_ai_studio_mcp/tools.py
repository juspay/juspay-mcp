# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import inspect
import json
import logging
from contextvars import ContextVar

import mcp.types as types
from mcp.server.lowlevel import Server

from juspay_ai_studio_mcp import response_schema
from juspay_ai_studio_mcp.api import *
import juspay_ai_studio_mcp.api_schema as api_schema
import juspay_ai_studio_mcp.utils as util

logger = logging.getLogger(__name__)

app = Server("juspay-ai-studio")

juspay_request_credentials: ContextVar[dict | None] = ContextVar(
    "juspay_ai_studio_request_credentials",
    default=None,
)


def set_juspay_request_credentials(credentials):
    """Set Juspay credentials for the current request context."""
    juspay_request_credentials.set(credentials)


def get_juspay_request_credentials():
    """Get Juspay credentials from current request context."""
    return juspay_request_credentials.get()


AVAILABLE_TOOLS = [
    util.make_api_config(
        name="get_merchant_details_ai_studio",
        description="""Return merchant and user session details for the authenticated AI Studio caller.

Key features:
- Returns merchantId, userId, email, username, tenantAccountId, validHost, and the caller's context.
- Takes no required input; all information is derived from the active AI Studio/Dashboard session token.

Use this before privileged Studio AI actions to confirm which merchant/user context the caller is operating under, or when the user asks who they are logged in as.""",
        model=api_schema.account.JuspayAIStudioGetMerchantDetailsPayload,
        handler=account.get_merchant_details_ai_studio,
    ),
    util.make_api_config(
        name="create_session",
        description="""Create a new PP Studio AI session for a merchant payment-page request.

Use this when the user wants Studio AI to start work on a payment page change, product question, UI change, feature toggle, icon change, direct config change, or theme redesign.

Required input:
- requirement: the user's natural-language request.

Optional input:
- client_id: merchant client ID.
- platforms: desktop, mobile, or both.
- model: model override for the worker.
- approved_version: approved Studio config version to start from.""",
        model=api_schema.sessions.CreateSessionPayload,
        handler=sessions.create_session,
        response_schema=response_schema.session_summary_response_schema,
    ),
    util.make_api_config(
        name="resume_session",
        description="""Resume an existing PP Studio AI session with a human answer or follow-up instruction.

Use this when a session is waiting for input, completed but needs a follow-up, failed and needs retry guidance, or was stopped and should continue.""",
        model=api_schema.sessions.ResumeSessionPayload,
        handler=sessions.resume_session,
        response_schema=response_schema.session_summary_response_schema,
    ),
    util.make_api_config(
        name="list_session",
        description="""List PP Studio AI sessions.

Use this to find recent Studio AI sessions, optionally filtering by status or merchant client_id.""",
        model=api_schema.sessions.ListSessionPayload,
        handler=sessions.list_session,
        response_schema=response_schema.session_list_response_schema,
    ),
    util.make_api_config(
        name="get_session",
        description="""Get full details for one PP Studio AI session.

Returns the current status, transcript messages, run history, worker events, state snapshot, final output, current question, and error details.""",
        model=api_schema.sessions.GetSessionPayload,
        handler=sessions.get_session,
        response_schema=response_schema.session_detail_response_schema,
    ),
    util.make_api_config(
        name="stop_session",
        description="""Stop or interrupt a PP Studio AI session.

Use this when a session is running too long, should be paused, or needs to be put into a follow-up state before continuing.""",
        model=api_schema.sessions.StopSessionPayload,
        handler=sessions.stop_session,
        response_schema=response_schema.session_summary_response_schema,
    ),
    util.make_api_config(
        name="payment_page_link",
        description="""Return the review URL for a PP Studio AI session's live payment-page preview.

Use this after a session has produced or is producing payment-page config so the user can inspect the generated page. This is the get_review_url-style tool.""",
        model=api_schema.sessions.PaymentPageLinkPayload,
        handler=sessions.payment_page_link,
        response_schema=response_schema.payment_page_link_response_schema,
    ),
    util.make_api_config(
        name="download_configs",
        description="""Return the config.zip download URL for a PP Studio AI session.

Use this when the user wants to download generated payment-page config files after Studio AI has created or modified them.""",
        model=api_schema.sessions.DownloadConfigsPayload,
        handler=sessions.download_configs,
        response_schema=response_schema.download_configs_response_schema,
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
    arguments = dict(arguments or {})
    try:
        from juspay_ai_studio_mcp.api.utils import set_ai_studio_credentials

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

        meta_info = arguments.pop("juspay_meta_info", None)
        model_cls = tool_entry.get("model")
        if model_cls:
            try:
                payload = model_cls(**arguments)
                payload_dict = payload.model_dump(exclude_none=True, by_alias=True)
            except Exception as e:
                raise ValueError(f"Validation error: {str(e)}")
        else:
            payload_dict = arguments

        juspay_creds = get_juspay_request_credentials()
        if juspay_creds:
            logger.info("Using request credentials for Juspay AI Studio API calls")
            set_ai_studio_credentials(juspay_creds)
        else:
            logger.info("No request credentials found, falling back to environment variables")
            set_ai_studio_credentials(None)

        sig = inspect.signature(handler)
        param_count = len(sig.parameters)

        if param_count == 0:
            response = await handler()
        elif param_count == 1:
            if payload_dict or not meta_info:
                response = await handler(payload_dict)
            else:
                response = await handler(meta_info)
        elif param_count == 2:
            response = await handler(payload_dict, meta_info)
        else:
            raise ValueError(f"Unsupported number of parameters in tool handler: {param_count}")

        return [types.TextContent(type="text", text=json.dumps(response))]

    except Exception as e:
        logger.error(f"Error in AI Studio tool execution: {e}")
        return [types.TextContent(type="text", text=f"ERROR: Tool execution failed: {str(e)}")]
