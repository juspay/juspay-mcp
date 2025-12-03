# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import click
import os
import uvicorn
import dotenv
import asyncio
import logging
import contextlib

from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

# Determine which MCP app to use based on JUSPAY_MCP_TYPE
JUSPAY_MCP_TYPE = os.getenv("JUSPAY_MCP_TYPE", "").upper()

MCP_APPS = {}

if JUSPAY_MCP_TYPE == "DASHBOARD":
    from juspay_dashboard_mcp.tools import app as dashboard_app
    from juspay_docs_mcp.tools import app as docs_app

    MCP_APPS["dashboard"] = dashboard_app
    MCP_APPS["docs"] = docs_app
else:
    # Single default FastMCP app
    from juspay_mcp.tools import app as default_app

    MCP_APPS["default"] = default_app

from juspay_mcp.stdio import run_stdio

# Load environment variables.
dotenv.load_dotenv()

# Configure logging.
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

class JuspayHeaderAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract Juspay credentials from headers.
    Supports partial credentials - tools will fallback to environment variables for missing values.
    """
    
    async def dispatch(self, request: Request, call_next):
        api_key = request.headers.get("JUSPAY_API_KEY")
        merchant_id = request.headers.get("JUSPAY_MERCHANT_ID") 
        dashboard_token = request.headers.get("JUSPAY_WEB_LOGIN_TOKEN")
        
        juspay_credentials = {}
        if api_key:
            juspay_credentials["api_key"] = api_key
        if merchant_id:
            juspay_credentials["merchant_id"] = merchant_id
        if dashboard_token:
            juspay_credentials["dashboard_token"] = dashboard_token
            
        if juspay_credentials:
            credential_summary = ", ".join(juspay_credentials.keys())
            logger.debug(f"Setting partial Juspay credentials from headers: {credential_summary}")
        else:
            logger.debug("No Juspay credentials in headers, using environment variables")
        
        request.state.juspay_credentials = juspay_credentials
            
        response = await call_next(request)
        return response

@click.command()
@click.option("--host", default="0.0.0.0", help="Host to bind the server to.")
@click.option("--port", default=8080, type=int, help="Port to listen on for SSE.")
@click.option("--mode", default="http", type=click.Choice(['http', 'stdio']), 
              help="Server mode: 'http' for HTTP/SSE server or 'stdio' for stdio server.")
def main(host: str, port: int, mode: str):
    """Runs the MCP server in the specified mode."""
    
    if mode == "stdio":
        # Run in stdio mode
        logger.info("Running in stdio mode.")
        asyncio.run(run_stdio())
        return
    
    # Run in HTTP/SSE mode (default)
    message_endpoint_path = "/messages/"
    if JUSPAY_MCP_TYPE == "DASHBOARD":
        # Dashboard MCP
        sse_dashboard_endpoint_path = "/juspay-dashboard"
        streamable_dashboard_endpoint_path = "/juspay-dashboard-stream"

        # Docs MCP
        sse_docs_endpoint_path = "/juspay-docs"
        streamable_docs_endpoint_path = "/juspay-docs-stream"
    else:
        sse_endpoint_path = "/juspay"
        streamable_endpoint_path = "/juspay-stream"
    
    logger.info("Running with header-based authentication")
    logger.info("Expected headers: JUSPAY_API_KEY, JUSPAY_MERCHANT_ID, JUSPAY_WEB_LOGIN_TOKEN")
    
    sse_transport_handler = SseServerTransport(message_endpoint_path)

    async def health_check(request: Request):
        return JSONResponse({"status": "ok"})

    def make_sse_handler(active_app_key: str):
        """
        Returns an async endpoint function bound to a specific MCP app
        (dashboard / docs / default).
        """
        active_app = MCP_APPS[active_app_key]

        async def handler(request: Request):
            logging.info(
                f"New SSE connection from: {request.client} - {request.method} {request.url.path}"
            )

            # Choose correct set_juspay_request_credentials based on which app is active
            if JUSPAY_MCP_TYPE == "DASHBOARD":
                if active_app_key == "dashboard":
                    from juspay_dashboard_mcp.tools import set_juspay_request_credentials
                elif active_app_key == "docs":
                    from juspay_docs_mcp.tools import set_juspay_request_credentials
                else:
                    # Fallback (should not happen in DASHBOARD mode)
                    from juspay_mcp.tools import set_juspay_request_credentials
            else:
                from juspay_mcp.tools import set_juspay_request_credentials

            juspay_creds = getattr(request.state, "juspay_credentials", None)
            set_juspay_request_credentials(juspay_creds)

            async with sse_transport_handler.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                logging.info(f"MCP Session starting for {request.client}")
                try:
                    await active_app.run(
                        streams[0],
                        streams[1],
                        active_app.create_initialization_options(),
                    )
                except Exception as e:
                    logging.error(
                        f"Error during MCP session for {request.client}: {e}"
                    )
                finally:
                    logging.info(f"MCP Session ended for {request.client}")

        return handler

    def make_streamable_http_handler(active_app_key: str):
        """
        Returns a Route-compatible endpoint function + its StreamableHTTPSessionManager,
        both bound to a specific MCP app.
        
        Uses Route instead of Mount to avoid 307 trailing slash redirects.
        """
        active_app = MCP_APPS[active_app_key]

        session_manager = StreamableHTTPSessionManager(
            app=active_app,
            event_store=None,
            json_response=True,
            stateless=True,
        )

        async def handle_streamable_http(request: Request):
            """Route-compatible endpoint for StreamableHTTP that handles credential injection."""
            logging.info(
                f"New StreamableHTTP request from: {request.client} - {request.method} {request.url.path}"
            )

            # Choose correct set_juspay_request_credentials based on which app is active
            if JUSPAY_MCP_TYPE == "DASHBOARD":
                if active_app_key == "dashboard":
                    from juspay_dashboard_mcp.tools import set_juspay_request_credentials
                elif active_app_key == "docs":
                    from juspay_docs_mcp.tools import set_juspay_request_credentials
                else:
                    from juspay_mcp.tools import set_juspay_request_credentials
            else:
                from juspay_mcp.tools import set_juspay_request_credentials

            juspay_creds = getattr(request.state, "juspay_credentials", None)
            set_juspay_request_credentials(juspay_creds)

            # Call session manager with the request's scope, receive, send
            await session_manager.handle_request(request.scope, request.receive, request._send)

        return handle_streamable_http, session_manager

    routes = [
        Route("/health", endpoint=health_check, methods=["GET"]),
        Route("/health/ready", endpoint=health_check, methods=["GET"]),
        Mount(message_endpoint_path, app=sse_transport_handler.handle_post_message),
    ]

    if JUSPAY_MCP_TYPE == "DASHBOARD":
        # Dashboard MCP
        dashboard_sse_handler = make_sse_handler("dashboard")
        dashboard_http_handler, dashboard_session_mgr = make_streamable_http_handler("dashboard")

        # Docs MCP
        docs_sse_handler = make_sse_handler("docs")
        docs_http_handler, docs_session_mgr = make_streamable_http_handler("docs")

        routes.extend(
            [
                # Dashboard MCP endpoints
                Route(sse_dashboard_endpoint_path, endpoint=dashboard_sse_handler),
                Route(
                    streamable_dashboard_endpoint_path,
                    endpoint=dashboard_http_handler,
                    methods=["GET", "POST", "DELETE"],
                ),
                # Docs MCP endpoints
                Route(sse_docs_endpoint_path, endpoint=docs_sse_handler),
                Route(
                    streamable_docs_endpoint_path,
                    endpoint=docs_http_handler,
                    methods=["GET", "POST", "DELETE"],
                ),
            ]
        )

        @contextlib.asynccontextmanager
        async def lifespan(app):
            """Application lifespan context manager for multiple MCP apps."""
            async with dashboard_session_mgr.run(), docs_session_mgr.run():
                logger.info("StreamableHTTP session managers (dashboard, docs) started")
                yield
            logger.info("StreamableHTTP session managers (dashboard, docs) stopped")

    else:
        default_sse_handler = make_sse_handler("default")
        default_http_handler, default_session_mgr = make_streamable_http_handler("default")

        routes.extend(
            [
                Route(sse_endpoint_path, endpoint=default_sse_handler),
                Route(
                    streamable_endpoint_path,
                    endpoint=default_http_handler,
                    methods=["GET", "POST", "DELETE"],
                ),
            ]
        )

        @contextlib.asynccontextmanager
        async def lifespan(app):
            """Application lifespan context manager for single MCP app."""
            async with default_session_mgr.run():
                logger.info("StreamableHTTP session manager started")
                yield
            logger.info("StreamableHTTP session manager stopped")

    # Add header authentication middleware
    middleware = [
        Middleware(JuspayHeaderAuthMiddleware),
    ]

    starlette_app = Starlette(
        debug=False,
        lifespan=lifespan,
        routes=routes,
        middleware=middleware,
    )

    # Log endpoints
    if JUSPAY_MCP_TYPE == "DASHBOARD":
        logger.info("Starting MCP server (DASHBOARD mode) on:")
        logger.info(f"  Dashboard SSE endpoint:        http://{host}:{port}{sse_dashboard_endpoint_path}")
        logger.info(f"  Dashboard Streamable endpoint: http://{host}:{port}{streamable_dashboard_endpoint_path}")
        logger.info(f"  Docs SSE endpoint:             http://{host}:{port}{sse_docs_endpoint_path}")
        logger.info(f"  Docs Streamable endpoint:      http://{host}:{port}{streamable_docs_endpoint_path}")
    else:
        logger.info("Starting MCP server on:")
        logger.info(f"  SSE endpoint:                  http://{host}:{port}{sse_endpoint_path}")
        logger.info(f"  StreamableHTTP endpoint:       http://{host}:{port}{streamable_endpoint_path}")

    uvicorn.run(starlette_app, host=host, port=port)


if __name__ == "__main__":
    main()
