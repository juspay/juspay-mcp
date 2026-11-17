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
from urllib.parse import urlparse

# Load .env BEFORE any os.getenv() so JUSPAY_MCP_TYPE etc.
# from the env file participate in the import-time branching below.
dotenv.load_dotenv()

from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse, Response
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

from juspay_mcp.auth.header_creds import extract_header_credentials

# Determine which MCP app to use based on JUSPAY_MCP_TYPE
JUSPAY_MCP_TYPE = os.getenv("JUSPAY_MCP_TYPE", "").upper()
AI_STUDIO_MCP_TYPES = {"PP_AI_STUDIO", "AI_STUDIO"}

MCP_APPS = {}

if JUSPAY_MCP_TYPE == "DASHBOARD":
    from juspay_dashboard_mcp.tools import app as dashboard_app
    from juspay_docs_mcp.server import (
        app as docs_app,
        refresh_catalog,
    )

    MCP_APPS["dashboard"] = dashboard_app
    MCP_APPS["docs"] = docs_app
elif JUSPAY_MCP_TYPE in AI_STUDIO_MCP_TYPES:
    from juspay_ai_studio_mcp.tools import app as ai_studio_app
    from juspay_docs_mcp.server import (
        app as docs_app,
        refresh_catalog,
    )

    MCP_APPS["ai_studio"] = ai_studio_app
    MCP_APPS["docs"] = docs_app
else:
    # Single default FastMCP app
    from juspay_mcp.tools import app as default_app

    MCP_APPS["default"] = default_app

from juspay_mcp.stdio import run_stdio

# Configure logging.
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Upstream URLs carry IDs (user, order, merchant), so keep the HTTP client's per-request INFO lines out of the logs.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

if JUSPAY_MCP_TYPE == "DASHBOARD":
    REQUIRED_HEADER_CREDENTIALS = {"dashboard_token": "JUSPAY_WEB_LOGIN_TOKEN"}
elif JUSPAY_MCP_TYPE in AI_STUDIO_MCP_TYPES:
    REQUIRED_HEADER_CREDENTIALS = {
        "pp_ai_studio_api_key": "PP_AI_STUDIO_API_KEY",
        "pp_ai_studio_token": "PP_AI_STUDIO_TOKEN",
        "dashboard_token": "JUSPAY_WEB_LOGIN_TOKEN",
        "api_key": "JUSPAY_API_KEY",
    }
else:
    REQUIRED_HEADER_CREDENTIALS = {"api_key": "JUSPAY_API_KEY"}

LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
ALLOW_ENV_CREDENTIALS_ENV = "JUSPAY_MCP_ALLOW_ENV_CREDENTIALS"


class JuspayHeaderAuthMiddleware(BaseHTTPMiddleware):
    """Rejects HTTP requests that don't carry their own Juspay credential."""

    def __init__(
        self,
        app,
        skip_path_prefixes: tuple[str, ...] = (),
        allow_env_credentials: bool = False,
    ) -> None:
        super().__init__(app)
        self._skip_path_prefixes = skip_path_prefixes
        self._allow_env_credentials = allow_env_credentials

    @staticmethod
    def _is_loopback_name(value) -> bool:
        try:
            return (urlparse(value).hostname or "") in LOOPBACK_HOSTS
        except ValueError:
            return False

    def _is_unauthenticated_path(self, path: str) -> bool:
        if path in ("/health", "/health/ready"):
            return True
        return any(path == p or path.startswith(p + "/") for p in self._skip_path_prefixes)

    async def dispatch(self, request: Request, call_next):
        juspay_credentials = extract_header_credentials(request)
        request.state.juspay_credentials = juspay_credentials

        # Use the raw ASGI path, not request.url.path, which is derived from the Host header.
        path = request.scope.get("path", "")
        has_credential = any(juspay_credentials.get(key) for key in REQUIRED_HEADER_CREDENTIALS)

        if self._allow_env_credentials and not has_credential:
            # The server's own credentials are in use: only loopback callers may reach it.
            # A web page on another site sends its own Host/Origin, so it is refused here.
            origin = request.headers.get("origin")
            if not self._is_loopback_name("//" + request.headers.get("host", "")) or (
                origin and not self._is_loopback_name(origin)
            ):
                logger.warning("Rejected non-loopback Host/Origin in env-credentials mode")
                return JSONResponse(
                    {"jsonrpc": "2.0", "id": None, "error": {"code": -32001, "message": "Forbidden host or origin"}},
                    status_code=403,
                )

        if (
            self._allow_env_credentials
            or self._is_unauthenticated_path(path)
            or has_credential
        ):
            return await call_next(request)

        expected = " or ".join(REQUIRED_HEADER_CREDENTIALS.values())
        logger.warning("Rejected unauthenticated request to %s", path)
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32001,
                    "message": f"Unauthorized: send the {expected} header",
                },
            },
            status_code=401,
        )

@click.command()
@click.option("--host", default="127.0.0.1", help="Host to bind the server to. Use 0.0.0.0 to accept connections from other machines.")
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
    if JUSPAY_MCP_TYPE == "DASHBOARD":
        # Dashboard MCP
        sse_dashboard_endpoint_path = "/juspay-dashboard"
        streamable_dashboard_endpoint_path = "/juspay-dashboard-stream"
        dashboard_message_path = "/messages/"

        # Docs MCP — own message path so it can be excluded from auth
        sse_docs_endpoint_path = "/juspay-docs"
        streamable_docs_endpoint_path = "/juspay-docs-stream"
        docs_message_path = "/docs-messages/"
    elif JUSPAY_MCP_TYPE in AI_STUDIO_MCP_TYPES:
        # AI Studio MCP
        sse_ai_studio_endpoint_path = "/juspay-ai-studio"
        streamable_ai_studio_endpoint_path = "/juspay-ai-studio-stream"
        ai_studio_message_path = "/juspay-ai-studio/messages/"

        # Docs MCP — own message path so it can be excluded from auth
        sse_docs_endpoint_path = "/juspay-docs"
        streamable_docs_endpoint_path = "/juspay-docs-stream"
        docs_message_path = "/docs-messages/"

    else:
        sse_endpoint_path = "/juspay"
        streamable_endpoint_path = "/juspay-stream"
        message_endpoint_path = "/messages/"
    
    logger.info("Running with header-based authentication")
    logger.info(
        "Required header (one of): %s", ", ".join(REQUIRED_HEADER_CREDENTIALS.values())
    )

    if JUSPAY_MCP_TYPE == "DASHBOARD":
        sse_transport_handler = SseServerTransport(dashboard_message_path)
        docs_sse_transport_handler = SseServerTransport(docs_message_path)
    elif JUSPAY_MCP_TYPE in AI_STUDIO_MCP_TYPES:
        sse_transport_handler = SseServerTransport(ai_studio_message_path)
        docs_sse_transport_handler = SseServerTransport(docs_message_path)
    else:
        sse_transport_handler = SseServerTransport(message_endpoint_path)

    class _AlreadySentResponse(Response):
        """No-op response — SSE/StreamableHTTP transport already wrote to send."""
        async def __call__(self, scope, receive, send):
            pass

    async def health_check(request: Request):
        return JSONResponse({"status": "ok"})

    def make_sse_handler(active_app_key: str, transport: SseServerTransport):
        """Returns an async SSE endpoint bound to a specific MCP app and transport."""
        active_app = MCP_APPS[active_app_key]

        async def handler(request: Request):
            logging.info(
                f"New SSE connection: {request.method} {request.url.path}"
            )

            if active_app_key == "dashboard":
                from juspay_dashboard_mcp.tools import set_juspay_request_credentials
                juspay_creds = getattr(request.state, "juspay_credentials", None)
                set_juspay_request_credentials(juspay_creds)
            elif active_app_key == "ai_studio":
                from juspay_ai_studio_mcp.tools import set_juspay_request_credentials
                juspay_creds = getattr(request.state, "juspay_credentials", None)
                set_juspay_request_credentials(juspay_creds)
            elif active_app_key == "default":
                from juspay_mcp.tools import set_juspay_request_credentials
                juspay_creds = getattr(request.state, "juspay_credentials", None)
                set_juspay_request_credentials(juspay_creds)
            # docs: no credentials needed

            async with transport.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                logging.info("MCP Session starting")
                try:
                    await active_app.run(
                        streams[0],
                        streams[1],
                        active_app.create_initialization_options(),
                    )
                except Exception as e:
                    logging.error(
                        f"Error during MCP session: {type(e).__name__}"
                    )
                finally:
                    logging.info("MCP Session ended")

            return _AlreadySentResponse()

        return handler

    def make_streamable_http_handler(active_app_key: str):
        """
        Returns a Route-compatible endpoint function + its StreamableHTTPSessionManager,
        both bound to a specific MCP app.
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
                f"New StreamableHTTP request: {request.method} {request.url.path}"
            )

            if active_app_key == "dashboard":
                from juspay_dashboard_mcp.tools import set_juspay_request_credentials
                juspay_creds = getattr(request.state, "juspay_credentials", None)
                set_juspay_request_credentials(juspay_creds)
            elif active_app_key == "ai_studio":
                from juspay_ai_studio_mcp.tools import set_juspay_request_credentials
                juspay_creds = getattr(request.state, "juspay_credentials", None)
                set_juspay_request_credentials(juspay_creds)
            elif active_app_key == "default":
                from juspay_mcp.tools import set_juspay_request_credentials
                juspay_creds = getattr(request.state, "juspay_credentials", None)
                set_juspay_request_credentials(juspay_creds)
            # docs: no credentials needed

            # session_manager writes the full HTTP response directly to send
            await session_manager.handle_request(request.scope, request.receive, request._send)
            return _AlreadySentResponse()

        return handle_streamable_http, session_manager

    if JUSPAY_MCP_TYPE == "DASHBOARD":
        routes = [
            Route("/health", endpoint=health_check, methods=["GET"]),
            Route("/health/ready", endpoint=health_check, methods=["GET"]),
            Mount(dashboard_message_path, app=sse_transport_handler.handle_post_message),
            Mount(docs_message_path, app=docs_sse_transport_handler.handle_post_message),
        ]
    elif JUSPAY_MCP_TYPE in AI_STUDIO_MCP_TYPES:
        routes = [
            Route("/health", endpoint=health_check, methods=["GET"]),
            Route("/health/ready", endpoint=health_check, methods=["GET"]),
            Mount(ai_studio_message_path, app=sse_transport_handler.handle_post_message),
            Mount(docs_message_path, app=docs_sse_transport_handler.handle_post_message),
        ]
    else:
        routes = [
            Route("/health", endpoint=health_check, methods=["GET"]),
            Route("/health/ready", endpoint=health_check, methods=["GET"]),
            Mount(message_endpoint_path, app=sse_transport_handler.handle_post_message),
        ]

    if JUSPAY_MCP_TYPE == "DASHBOARD":
        # Dashboard MCP
        dashboard_sse_handler = make_sse_handler("dashboard", sse_transport_handler)
        dashboard_http_handler, dashboard_session_mgr = make_streamable_http_handler("dashboard")

        # Docs MCP
        docs_sse_handler = make_sse_handler("docs", docs_sse_transport_handler)
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
            docs_refresh = None
            try:
                async with contextlib.AsyncExitStack() as stack:
                    await stack.enter_async_context(dashboard_session_mgr.run())
                    logger.info("Dashboard StreamableHTTP session manager started")
                    await stack.enter_async_context(docs_session_mgr.run())
                    logger.info("Docs StreamableHTTP session manager started")
                    logger.info("All StreamableHTTP session managers started successfully")
                    docs_refresh = asyncio.create_task(refresh_catalog())
                    yield
            finally:
                if docs_refresh is not None:
                    docs_refresh.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await docs_refresh
            logger.info("StreamableHTTP session managers stopped")
    elif JUSPAY_MCP_TYPE in AI_STUDIO_MCP_TYPES:
        ai_studio_sse_handler = make_sse_handler("ai_studio", sse_transport_handler)
        ai_studio_http_handler, ai_studio_session_mgr = make_streamable_http_handler("ai_studio")

        # Docs MCP
        docs_sse_handler = make_sse_handler("docs", docs_sse_transport_handler)
        docs_http_handler, docs_session_mgr = make_streamable_http_handler("docs")

        routes.extend(
            [
                # AI Studio MCP endpoints
                Route(sse_ai_studio_endpoint_path, endpoint=ai_studio_sse_handler),
                Route(
                    streamable_ai_studio_endpoint_path,
                    endpoint=ai_studio_http_handler,
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
            docs_refresh = None
            try:
                async with contextlib.AsyncExitStack() as stack:
                    await stack.enter_async_context(ai_studio_session_mgr.run())
                    logger.info("AI Studio StreamableHTTP session manager started")
                    await stack.enter_async_context(docs_session_mgr.run())
                    logger.info("Docs StreamableHTTP session manager started")
                    logger.info("All StreamableHTTP session managers started successfully")
                    docs_refresh = asyncio.create_task(refresh_catalog())
                    yield
            finally:
                if docs_refresh is not None:
                    docs_refresh.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await docs_refresh
            logger.info("StreamableHTTP session managers stopped")

    else:
        default_sse_handler = make_sse_handler("default", sse_transport_handler)
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
                logger.info("StreamableHTTP session manager started successfully")
                yield
            logger.info("StreamableHTTP session manager stopped")

    # Authentication middleware: every request must carry its own Juspay
    # credential header (JUSPAY_WEB_LOGIN_TOKEN, API key, ...).
    # In DASHBOARD / AI Studio modes the docs endpoints are public (no auth required).
    docs_skip_prefixes: tuple[str, ...] = ()
    if JUSPAY_MCP_TYPE == "DASHBOARD":
        docs_skip_prefixes = (
            sse_docs_endpoint_path,
            streamable_docs_endpoint_path,
            docs_message_path,
        )
    elif JUSPAY_MCP_TYPE in AI_STUDIO_MCP_TYPES:
        docs_skip_prefixes = (
            sse_docs_endpoint_path,
            streamable_docs_endpoint_path,
            docs_message_path,
        )

    allow_env_credentials = os.getenv(ALLOW_ENV_CREDENTIALS_ENV, "").lower() == "true"
    if allow_env_credentials and host not in LOOPBACK_HOSTS:
        raise click.UsageError(
            f"{ALLOW_ENV_CREDENTIALS_ENV}=true lends the server's own Juspay credentials "
            f"to every caller, so it is only allowed when bound to loopback "
            f"(got --host {host})."
        )
    if allow_env_credentials:
        logger.warning(
            "%s=true: requests without credential headers will use the environment's "
            "Juspay credentials. Local use only.",
            ALLOW_ENV_CREDENTIALS_ENV,
        )
    middleware = [
        Middleware(
            JuspayHeaderAuthMiddleware,
            skip_path_prefixes=docs_skip_prefixes,
            allow_env_credentials=allow_env_credentials,
        ),
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
    elif JUSPAY_MCP_TYPE in AI_STUDIO_MCP_TYPES:
        logger.info("Starting MCP server (AI_STUDIO mode) on:")
        logger.info(f"  AI Studio SSE endpoint:        http://{host}:{port}{sse_ai_studio_endpoint_path}")
        logger.info(f"  AI Studio Streamable endpoint: http://{host}:{port}{streamable_ai_studio_endpoint_path}")
        logger.info(f"  Docs SSE endpoint:             http://{host}:{port}{sse_docs_endpoint_path}")
        logger.info(f"  Docs Streamable endpoint:      http://{host}:{port}{streamable_docs_endpoint_path}")
    else:
        logger.info("Starting MCP server on:")
        logger.info(f"  SSE endpoint:                  http://{host}:{port}{sse_endpoint_path}")
        logger.info(f"  StreamableHTTP endpoint:       http://{host}:{port}{streamable_endpoint_path}")

    uvicorn.run(starlette_app, host=host, port=port, lifespan="on", access_log=False)


if __name__ == "__main__":
    main()
