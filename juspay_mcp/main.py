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

# Load .env BEFORE any os.getenv() so JUSPAY_MCP_TYPE / OAUTH_ENABLED etc.
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

from juspay_mcp.auth import config as auth_config
from juspay_mcp.auth.middleware import BearerAuthMiddleware
from juspay_mcp.auth.portal_client import PortalClient
from juspay_mcp.auth.routes import build_routes as build_oauth_routes
from juspay_mcp.auth.state_store import MemoryStateStore
from juspay_mcp.analytics.context import (
    clear_current_context as clear_analytics_context,
    from_request as analytics_context_from_request,
    set_current_context as set_analytics_context,
)
from juspay_mcp.analytics.client import shutdown as shutdown_analytics
from juspay_mcp.analytics.config import warm as warm_analytics

# Determine which MCP app to use based on JUSPAY_MCP_TYPE
JUSPAY_MCP_TYPE = os.getenv("JUSPAY_MCP_TYPE", "").upper()
AI_STUDIO_MCP_TYPES = {"PP_AI_STUDIO", "AI_STUDIO"}

MCP_APPS = {}

if JUSPAY_MCP_TYPE == "DASHBOARD":
    from juspay_dashboard_mcp.tools import app as dashboard_app
    from juspay_docs_mcp.server import app as docs_app

    MCP_APPS["dashboard"] = dashboard_app
    MCP_APPS["docs"] = docs_app
elif JUSPAY_MCP_TYPE in AI_STUDIO_MCP_TYPES:
    from juspay_ai_studio_mcp.tools import app as ai_studio_app
    from juspay_docs_mcp.server import app as docs_app

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
        pp_ai_studio_api_key = request.headers.get("PP_AI_STUDIO_API_KEY")
        pp_ai_studio_token = (
            request.headers.get("PP_AI_STUDIO_TOKEN")
            or request.headers.get("JUSPAY_AI_STUDIO_TOKEN")
        )
        
        base_url_override = request.headers.get("x-base-url")
        tenant_id_override = request.headers.get("x-tenant-id")

        juspay_credentials = {}
        if api_key:
            juspay_credentials["api_key"] = api_key
        if merchant_id:
            juspay_credentials["merchant_id"] = merchant_id
        if dashboard_token:
            juspay_credentials["dashboard_token"] = dashboard_token
        if base_url_override:
            juspay_credentials["base_url"] = base_url_override
        if tenant_id_override:
            juspay_credentials["tenant_id"] = tenant_id_override
        if JUSPAY_MCP_TYPE in AI_STUDIO_MCP_TYPES:
            if pp_ai_studio_api_key:
                juspay_credentials["pp_ai_studio_api_key"] = pp_ai_studio_api_key
            if pp_ai_studio_token:
                juspay_credentials["pp_ai_studio_token"] = pp_ai_studio_token
            
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
    warm_analytics()  # resolve (and KMS-decrypt if configured) the analytics token once, at startup
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
    
    oauth_cfg = auth_config.load()
    portal_client = None
    oauth_state_store = None
    oauth_routes_list: list = []
    oauth_validation_cache: dict = {}
    if oauth_cfg.enabled:
        portal_client = PortalClient(oauth_cfg)
        oauth_state_store = MemoryStateStore(ttl_seconds=oauth_cfg.state_ttl_seconds)
        oauth_routes_list = build_oauth_routes(
            oauth_cfg, portal_client, oauth_state_store, validation_cache=oauth_validation_cache
        )
        logger.info("Running with OAuth bearer authentication")
    else:
        logger.info("Running with header-based authentication")
        logger.info("Expected headers: JUSPAY_API_KEY, JUSPAY_MERCHANT_ID, JUSPAY_WEB_LOGIN_TOKEN")

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
                f"New SSE connection from: {request.client} - {request.method} {request.url.path}"
            )

            if JUSPAY_MCP_TYPE == "DASHBOARD" and active_app_key in ("dashboard", "docs"):
                set_analytics_context(analytics_context_from_request(request, active_app_key))

            try:
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
            finally:
                clear_analytics_context()

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
                f"New StreamableHTTP request from: {request.client} - {request.method} {request.url.path}"
            )

            if JUSPAY_MCP_TYPE == "DASHBOARD" and active_app_key in ("dashboard", "docs"):
                set_analytics_context(analytics_context_from_request(request, active_app_key))

            try:
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
            finally:
                clear_analytics_context()
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

    # Prepend OAuth discovery + /oauth/* routes before the MCP transport
    # routes so they win the longest-prefix match.
    if oauth_routes_list:
        routes = oauth_routes_list + routes

    # In DASHBOARD mode the docs endpoints are public. Prepend literal
    # well-known routes for docs mounts AFTER the OAuth list so they sit
    # first in the final route table and beat the OAuth per-mount template
    # route (/{mount}/.well-known/oauth-protected-resource).
    if JUSPAY_MCP_TYPE == "DASHBOARD":
        _WELL_KNOWN_METHODS = ["GET", "OPTIONS"]
        docs_public_routes: list = []
        for _docs_mount_path in (sse_docs_endpoint_path, streamable_docs_endpoint_path):
            _mount = _docs_mount_path.lstrip("/")
            _resource_url = (
                f"{oauth_cfg.mcp_server_url}/{_mount}"
                if oauth_cfg.enabled
                else f"http://{host}:{port}/{_mount}"
            )

            async def _docs_prm(request: Request, _url: str = _resource_url) -> Response:
                return JSONResponse({"resource": _url})

            docs_public_routes.append(
                Route(
                    f"/{_mount}/.well-known/oauth-protected-resource",
                    endpoint=_docs_prm,
                    methods=_WELL_KNOWN_METHODS,
                )
            )
        routes = docs_public_routes + routes
    elif JUSPAY_MCP_TYPE in AI_STUDIO_MCP_TYPES:
        _WELL_KNOWN_METHODS = ["GET", "OPTIONS"]
        docs_public_routes: list = []
        for _docs_mount_path in (sse_docs_endpoint_path, streamable_docs_endpoint_path):
            _mount = _docs_mount_path.lstrip("/")
            _resource_url = (
                f"{oauth_cfg.mcp_server_url}/{_mount}"
                if oauth_cfg.enabled
                else f"http://{host}:{port}/{_mount}"
            )

            async def _docs_prm(request: Request, _url: str = _resource_url) -> Response:
                return JSONResponse({"resource": _url})

            docs_public_routes.append(
                Route(
                    f"/{_mount}/.well-known/oauth-protected-resource",
                    endpoint=_docs_prm,
                    methods=_WELL_KNOWN_METHODS,
                )
            )
        routes = docs_public_routes + routes

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
            try:
                async with contextlib.AsyncExitStack() as stack:
                    await stack.enter_async_context(dashboard_session_mgr.run())
                    logger.info("Dashboard StreamableHTTP session manager started")
                    await stack.enter_async_context(docs_session_mgr.run())
                    logger.info("Docs StreamableHTTP session manager started")
                    logger.info("All StreamableHTTP session managers started successfully")
                    yield
            finally:
                await shutdown_analytics()
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
            async with contextlib.AsyncExitStack() as stack:
                await stack.enter_async_context(ai_studio_session_mgr.run())
                logger.info("AI Studio StreamableHTTP session manager started")
                await stack.enter_async_context(docs_session_mgr.run())
                logger.info("Docs StreamableHTTP session manager started")
                logger.info("All StreamableHTTP session managers started successfully")
                yield
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
                if oauth_state_store is not None:
                    await oauth_state_store.start()
                    logger.info("OAuth state store sweeper started")
                try:
                    yield
                finally:
                    if oauth_state_store is not None:
                        await oauth_state_store.stop()
                    if portal_client is not None:
                        await portal_client.aclose()
            logger.info("StreamableHTTP session manager stopped")

    # Authentication middleware — OAuth bearer when enabled, else legacy header path.
    # In DASHBOARD mode the docs endpoints are public (no auth required).
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

    if oauth_cfg.enabled and portal_client is not None:
        middleware = [
            Middleware(
                BearerAuthMiddleware,
                cfg=oauth_cfg,
                portal=portal_client,
                validation_cache=oauth_validation_cache,
                skip_path_prefixes=docs_skip_prefixes,
            ),
        ]
    else:
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

    if oauth_cfg.enabled:
        logger.info("OAuth discovery + endpoints:")
        logger.info(f"  Issuer (MCP_SERVER_URL):       {oauth_cfg.mcp_server_url}")
        logger.info(f"  Protected-resource metadata:   {oauth_cfg.mcp_server_url}/.well-known/oauth-protected-resource")
        logger.info(f"  Authorization-server metadata: {oauth_cfg.mcp_server_url}/.well-known/oauth-authorization-server")
        logger.info(f"  Dynamic client registration:   {oauth_cfg.mcp_server_url}/oauth/register")
        logger.info(f"  Authorize:                     {oauth_cfg.mcp_server_url}/oauth/authorize")
        logger.info(f"  Token:                         {oauth_cfg.mcp_server_url}/oauth/token")
        logger.info(f"  Portal IdP:                    {oauth_cfg.portal_base_url}")

    uvicorn.run(starlette_app, host=host, port=port, lifespan="on")


if __name__ == "__main__":
    main()
