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
if os.getenv("JUSPAY_MCP_TYPE") == "DASHBOARD":
    from juspay_dashboard_mcp.tools import app
else:
    from juspay_mcp.tools import app
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
    # Define endpoint paths.
    message_endpoint_path = "/messages/"
    if os.getenv("JUSPAY_MCP_TYPE") == "DASHBOARD":
        sse_endpoint_path = "/juspay-dashboard"
        streamable_endpoint_path = "/juspay-dashboard-stream"
    else:
        sse_endpoint_path = "/juspay"
        streamable_endpoint_path = "/juspay-stream"
    
    logger.info("Running with header-based authentication")
    logger.info("Expected headers: JUSPAY_API_KEY, JUSPAY_MERCHANT_ID, JUSPAY_WEB_LOGIN_TOKEN")
    
    sse_transport_handler = SseServerTransport(message_endpoint_path)
    
    streamable_session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None, 
        json_response=True, 
        stateless=True  
    )

    async def health_check(request):
        return JSONResponse({"status": "ok"})
    
    async def handle_sse_connection(request):
        """Handles a single client SSE connection and runs the MCP session."""
        logging.info(f"New SSE connection from: {request.client} - {request.method} {request.url.path}")
        
        # Set credentials for SSE connections 
        if os.getenv("JUSPAY_MCP_TYPE") == "DASHBOARD":
            from juspay_dashboard_mcp.tools import set_juspay_request_credentials
        else:
            from juspay_mcp.tools import set_juspay_request_credentials
            
        juspay_creds = getattr(request.state, 'juspay_credentials', None)
        set_juspay_request_credentials(juspay_creds)
        
        async with sse_transport_handler.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            logging.info(f"MCP Session starting for {request.client}")
            try:
                await app.run(
                    streams[0],
                    streams[1],
                    app.create_initialization_options()
                )
            except Exception as e:
                logging.error(f"Error during MCP session for {request.client}: {e}")
            finally:
                logging.info(f"MCP Session ended for {request.client}")

    async def handle_streamable_http(request):
        """Handles StreamableHTTP requests."""
        
        logging.info(f"New StreamableHTTP request from: {request.client} - {request.method} {request.url.path}")

        if os.getenv("JUSPAY_MCP_TYPE") == "DASHBOARD":
            from juspay_dashboard_mcp.tools import set_juspay_request_credentials
        else:
            from juspay_mcp.tools import set_juspay_request_credentials
            
        juspay_creds = getattr(request.state, 'juspay_credentials', None)
        set_juspay_request_credentials(juspay_creds)

        await streamable_session_manager.handle_request(
            request.scope, request.receive, request._send
        )

    @contextlib.asynccontextmanager
    async def lifespan(app):
        """Application lifespan context manager."""
        async with streamable_session_manager.run():
            logger.info("StreamableHTTP session manager started")
            yield
        logger.info("StreamableHTTP session manager stopped")

    # Prepare routes and middleware with header-based authentication
    routes = [
        Route("/health", endpoint=health_check, methods=["GET"]),
        Route("/health/ready", endpoint=health_check, methods=["GET"]),
        Route(sse_endpoint_path, endpoint=handle_sse_connection),
        Mount(message_endpoint_path, app=sse_transport_handler.handle_post_message),
        Route(streamable_endpoint_path, endpoint=handle_streamable_http, methods=["GET", "POST", "DELETE"]),
    ]
    
    # Add header authentication middleware
    middleware = [
        Middleware(JuspayHeaderAuthMiddleware)
    ]

    starlette_app = Starlette(
        debug=False,
        lifespan=lifespan,
        routes=routes,
        middleware=middleware,
    )

    logger.info(f"Starting MCP server on:")
    logger.info(f"  SSE endpoint: http://{host}:{port}{sse_endpoint_path}")
    logger.info(f"  StreamableHTTP endpoint: http://{host}:{port}{streamable_endpoint_path}")
    uvicorn.run(starlette_app, host=host, port=port)

if __name__ == "__main__":
    main()
