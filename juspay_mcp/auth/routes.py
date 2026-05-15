# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt
"""Starlette routes for OAuth discovery + endpoints.

Endpoint inventory (all mounted on the same Starlette app as the MCP transport
endpoints):

  GET  /.well-known/oauth-protected-resource
  GET  /<mount>/.well-known/oauth-protected-resource     (per-mount alias)
  GET  /.well-known/oauth-authorization-server
  GET  /.well-known/openid-configuration                 (RFC 8414 alias)
  GET  /.well-known/jwks.json
  POST /oauth/register                                   (RFC 7591 DCR)
  GET  /oauth/authorize
  GET  /oauth/callback
  POST /oauth/token
  POST /oauth/revoke
"""

from __future__ import annotations

import base64
import logging
import secrets
import time
from urllib.parse import urlencode, urlparse

from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette.routing import Route

from .config import OAuthConfig
from .metadata import authorization_server_metadata, protected_resource_metadata
from .pkce import validate_s256
from .portal_client import PortalClient
from .state_store import MemoryStateStore, StateData

logger = logging.getLogger(__name__)


def _bad_request(error: str, description: str) -> JSONResponse:
    return JSONResponse(
        {"error": error, "error_description": description}, status_code=400
    )


def _unauthorized_client(description: str) -> JSONResponse:
    return JSONResponse(
        {"error": "invalid_client", "error_description": description}, status_code=401
    )


def _parse_client_credentials(request: Request, body: dict) -> tuple[str | None, str | None]:
    """Pull client_id / client_secret from either the body or a Basic auth header."""
    client_id = body.get("client_id")
    client_secret = body.get("client_secret")

    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("basic "):
        try:
            decoded = base64.b64decode(auth_header[6:].encode("ascii")).decode("utf-8")
            cid, csec = decoded.split(":", 1)
            client_id = cid or client_id
            client_secret = csec or client_secret
        except Exception:
            logger.warning("invalid Basic auth header on token endpoint")

    return client_id, client_secret


async def _read_form_or_json(request: Request) -> dict:
    """Token endpoint accepts both x-www-form-urlencoded and JSON."""
    content_type = (request.headers.get("content-type") or "").lower()
    if "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        return {k: form[k] for k in form.keys()}
    if "application/json" in content_type:
        try:
            return await request.json()
        except Exception:
            return {}
    # Fall back to form, then JSON.
    try:
        form = await request.form()
        if form:
            return {k: form[k] for k in form.keys()}
    except Exception:
        pass
    try:
        return await request.json()
    except Exception:
        return {}


def _resource_is_acceptable(cfg: OAuthConfig, resource: str | None) -> bool:
    if not resource:
        # Per spec we SHOULD require resource, but during DCR-only smoke tests
        # some clients omit it. Accept None for now and tighten in phase 2.
        return True
    try:
        parsed = urlparse(resource)
    except Exception:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    issuer_host = urlparse(cfg.mcp_server_url).netloc
    return parsed.netloc == issuer_host or parsed.netloc in cfg.extra_resource_hostnames


# ---- Handlers ----------------------------------------------------------------


def build_routes(
    cfg: OAuthConfig,
    portal: PortalClient,
    store: MemoryStateStore,
    validation_cache: dict | None = None,
) -> list[Route]:
    """Construct the OAuth/discovery route list.

    `validation_cache` (optional) is the same dict shared with
    `BearerAuthMiddleware`. When provided, the `/oauth/revoke` handler evicts
    revoked bearers from it so the next request can't sneak past the cache
    TTL window.
    """

    # ---------- well-known ----------------------------------------------------
    async def prm_root(_: Request) -> Response:
        return JSONResponse(protected_resource_metadata(cfg))

    async def prm_for_mount(request: Request) -> Response:
        # `mount_path` arrives via path templating, e.g. /juspay-dashboard-stream
        mount = request.path_params["mount"]
        resource_url = f"{cfg.mcp_server_url}/{mount}"
        return JSONResponse(protected_resource_metadata(cfg, resource_url=resource_url))

    async def asm(_: Request) -> Response:
        return JSONResponse(authorization_server_metadata(cfg))

    async def jwks(_: Request) -> Response:
        return JSONResponse({"keys": []})

    # ---------- RFC 7591 dynamic client registration --------------------------
    async def register(request: Request) -> Response:
        try:
            body = await request.json()
        except Exception:
            body = {}

        client_id = body.get("client_id") or cfg.upstream_client_id or f"client_{int(time.time())}"
        client_secret = (
            body.get("client_secret") or cfg.upstream_client_secret or secrets.token_hex(32)
        )
        return JSONResponse(
            {
                "client_id": client_id,
                "client_secret": client_secret,
                "client_id_issued_at": int(time.time()),
                "client_secret_expires_at": 0,
                "redirect_uris": body.get("redirect_uris", []),
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "client_secret_post",
                "client_name": body.get("client_name", "MCP Client"),
            }
        )

    # ---------- /oauth/authorize ---------------------------------------------
    async def authorize(request: Request) -> Response:
        q = request.query_params
        redirect_uri = q.get("redirect_uri")
        state = q.get("state")
        code_challenge = q.get("code_challenge")
        code_challenge_method = q.get("code_challenge_method")
        scope = q.get("scope")
        client_id = q.get("client_id")
        resource = q.get("resource")

        if not redirect_uri:
            return _bad_request("invalid_request", "redirect_uri is required")
        if not state:
            return _bad_request("invalid_request", "state is required")
        if code_challenge and code_challenge_method and code_challenge_method != "S256":
            return _bad_request(
                "invalid_request",
                "Only S256 PKCE challenge method is supported",
            )
        if not _resource_is_acceptable(cfg, resource):
            return _bad_request("invalid_target", f"resource {resource!r} is not served by this server")

        await store.put_state(
            state,
            StateData(
                redirect_uri=redirect_uri,
                client_id=client_id,
                scope=scope,
                resource=resource,
                code_challenge=code_challenge,
                code_challenge_method=code_challenge_method,
                created_at=time.time(),
            ),
        )

        # Redirect the user-agent to Portal SSO. Portal will eventually
        # redirect back to /oauth/callback on THIS server, which then bounces
        # to the client-supplied redirect_uri.
        portal_params = {
            "client_id": client_id or cfg.upstream_client_id,
            "redirect_uri": f"{cfg.mcp_server_url}/oauth/callback",
            "scope": "user_access",
            "state": state,
        }
        portal_url = f"{cfg.portal_base_url}?{urlencode(portal_params)}"
        return RedirectResponse(portal_url, status_code=302)

    # ---------- /oauth/callback ----------------------------------------------
    async def callback(request: Request) -> Response:
        q = request.query_params
        code = q.get("code")
        state = q.get("state")
        error = q.get("error")
        error_description = q.get("error_description")

        if not state:
            return _bad_request("invalid_request", "state is required")

        state_data = await store.get_state(state)
        if state_data is None:
            return _bad_request("invalid_request", "Invalid or expired state")

        target = state_data.redirect_uri
        params: dict[str, str] = {"state": state}
        if error:
            params["error"] = error
            if error_description:
                params["error_description"] = error_description
            await store.delete_state(state)
        elif code:
            params["code"] = code
            await store.bind_code(code, state)
        else:
            return _bad_request("invalid_request", "Missing both code and error in callback")

        sep = "&" if "?" in target else "?"
        return RedirectResponse(f"{target}{sep}{urlencode(params)}", status_code=302)

    # ---------- /oauth/token --------------------------------------------------
    async def token(request: Request) -> Response:
        body = await _read_form_or_json(request)
        grant_type = body.get("grant_type")
        client_id, client_secret = _parse_client_credentials(request, body)

        if not client_id or not client_secret:
            # Fall back to the server-side configured upstream client. This
            # makes the flow work for Claude Code's "none" auth method clients
            # that registered via DCR without persisting a real secret.
            client_id = client_id or cfg.upstream_client_id
            client_secret = client_secret or cfg.upstream_client_secret

        if not client_id or not client_secret:
            return _unauthorized_client("Client credentials required")

        if grant_type == "authorization_code":
            code = body.get("code")
            code_verifier = body.get("code_verifier")
            if not code:
                return _bad_request("invalid_request", "Missing authorization code")

            bound_state = await store.lookup_state_by_code(code)
            state_data = await store.get_state(bound_state) if bound_state else None

            if state_data and state_data.code_challenge:
                if not code_verifier:
                    return _bad_request("invalid_request", "code_verifier is required for PKCE")
                if not validate_s256(code_verifier, state_data.code_challenge):
                    return _bad_request("invalid_grant", "Invalid code_verifier")

            token_resp = await portal.exchange_code(client_id, client_secret, code)
            if token_resp is None:
                return _bad_request("invalid_grant", "Portal token exchange failed")

            if bound_state:
                await store.delete_state(bound_state)
                await store.delete_code(code)

            return JSONResponse(
                {
                    "access_token": token_resp.access_token,
                    "refresh_token": token_resp.refresh_token,
                    "expires_in": token_resp.expires_in,
                    "token_type": "Bearer",
                    "scope": " ".join(cfg.scopes_supported),
                }
            )

        if grant_type == "refresh_token":
            refresh_token = body.get("refresh_token")
            if not refresh_token:
                return _bad_request("invalid_request", "Missing refresh_token")
            token_resp = await portal.refresh(client_id, client_secret, refresh_token)
            if token_resp is None:
                return _bad_request("invalid_grant", "Portal refresh failed")
            return JSONResponse(
                {
                    "access_token": token_resp.access_token,
                    "refresh_token": token_resp.refresh_token,
                    "expires_in": token_resp.expires_in,
                    "token_type": "Bearer",
                    "scope": " ".join(cfg.scopes_supported),
                }
            )

        return _bad_request(
            "unsupported_grant_type", f"Grant type {grant_type!r} is not supported"
        )

    # ---------- /oauth/revoke -------------------------------------------------
    async def revoke(request: Request) -> Response:
        """RFC 7009 revocation endpoint.

        Forwards to Portal's session-revoke API so the OAuth grant is
        actually invalidated upstream (powers Claude Code's `/mcp` →
        "Clear authentication" and re-auth flows). Always returns 200 per
        RFC 7009 §2.2, even when Portal fails or the token is unknown —
        the response body is informational only.
        """
        body = await _read_form_or_json(request)
        token = body.get("token")
        # token_type_hint can be 'access_token' | 'refresh_token' per RFC 7009.
        # Portal revokes the whole entity (user session) regardless so we
        # don't need to differentiate.
        client_id, _client_secret = _parse_client_credentials(request, body)
        client_id = client_id or cfg.upstream_client_id

        revoked = False
        if token and client_id:
            revoked = await portal.revoke_token(client_id, token)
            # Evict the validated-token cache so subsequent requests are forced
            # to re-validate via Portal (which will now return 4xx).
            if validation_cache is not None:
                validation_cache.pop(token, None)
        elif not token:
            logger.warning("/oauth/revoke called without a `token` body field")

        return JSONResponse({"revoked": revoked})

    # ---------- assemble ------------------------------------------------------
    routes: list[Route] = [
        Route("/.well-known/oauth-protected-resource", endpoint=prm_root, methods=["GET"]),
        Route(
            "/{mount:str}/.well-known/oauth-protected-resource",
            endpoint=prm_for_mount,
            methods=["GET"],
        ),
        Route("/.well-known/oauth-authorization-server", endpoint=asm, methods=["GET"]),
        Route("/.well-known/openid-configuration", endpoint=asm, methods=["GET"]),
        Route("/.well-known/jwks.json", endpoint=jwks, methods=["GET"]),
        Route("/oauth/register", endpoint=register, methods=["POST"]),
        Route("/oauth/authorize", endpoint=authorize, methods=["GET"]),
        Route("/oauth/callback", endpoint=callback, methods=["GET"]),
        Route("/oauth/token", endpoint=token, methods=["POST"]),
        Route("/oauth/revoke", endpoint=revoke, methods=["POST"]),
    ]
    return routes
