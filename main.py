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

from starlette.applications import Starlette
from starlette.routing import Mount, Route
from mcp.server.sse import SseServerTransport
if os.getenv("JUSPAY_MCP_TYPE") == "DASHBOARD":
    from juspay_dashboard_mcp.tools import app
else:
    from juspay_mcp.tools import app
from stdio import run_stdio

# Load environment variables.
dotenv.load_dotenv()

# Configure logging.
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", default="127.0.0.1", help="Host to bind the server to.")
@click.option("--port", default=8000, type=int, help="Port to listen on for SSE.")
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
    else:
        sse_endpoint_path = "/juspay"
    
    # Create the SSE transport handler.
    sse_transport_handler = SseServerTransport(message_endpoint_path)
    
    async def handle_sse_connection(request):
        """Handles a single client SSE connection and runs the MCP session."""
        logging.info(f"New SSE connection from: {request.client}")
        
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

    # Create a Starlette application with the desired routes.
    starlette_app = Starlette(
        debug=False,
        routes=[
            Route(sse_endpoint_path, endpoint=handle_sse_connection),
            Mount(message_endpoint_path, app=sse_transport_handler.handle_post_message),
        ],
    )

    logger.info(f"Starting MCP server on http://{host}:{port}{sse_endpoint_path}")
    uvicorn.run(starlette_app, host=host, port=port)

if __name__ == "__main__":
    main()
