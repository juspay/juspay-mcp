# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import asyncio
import os
import logging 
import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import NotificationOptions
from mcp.server.models import InitializationOptions

logger = logging.getLogger(__name__)

# Determine which MCP app to use based on JUSPAY_MCP_TYPE
JUSPAY_MCP_TYPE = os.getenv("JUSPAY_MCP_TYPE", "").upper()

if JUSPAY_MCP_TYPE == "DASHBOARD":
    from juspay_dashboard_mcp.tools import app
elif JUSPAY_MCP_TYPE == "INTEGRATION_DOCS":
    from juspay_docs_mcp.tools import app
else:
    from juspay_mcp.tools import app

async def run_stdio():
    """Runs the MCP server using stdio for input/output."""
    logger.info("Starting Juspay Tools in stdio mode...")
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="juspay",
                server_version="0.1.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(run_stdio())
