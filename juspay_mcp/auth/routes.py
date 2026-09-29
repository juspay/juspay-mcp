# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt
"""Starlette routes for OAuth discovery + endpoints.

Endpoint inventory (all mounted on the same Starlette app as the MCP transport
endpoints):

  GET  /.well-known/oauth-protected-resource
  GET  /.well-known/oauth-protected-resource/<mount>     (per-mount, reverse)
  GET  /<mount>/.well-known/oauth-protected-resource     (per-mount, forward)
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

from .client_store import ClientData, MemoryClientStore
from .config import OAuthConfig
from .metadata import authorization_server_metadata, protected_resource_metadata
from .tenant import resolve as resolve_tenant
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
    client_store: MemoryClientStore,
    validation_cache: dict | None = None,
) -> list[Route]:
    """Construct the OAuth/discovery route list.

    `validation_cache` (optional) is the same dict shared with
    `BearerAuthMiddleware`. When provided, the `/oauth/revoke` handler evicts
    revoked bearers from it so the next request can't sneak past the cache
    TTL window.
    """

    # ---------- well-known ----------------------------------------------------
    async def prm_root(request: Request) -> Response:
        return JSONResponse(protected_resource_metadata(resolve_tenant(cfg, request)))

    async def prm_for_mount(request: Request) -> Response:
        # Forward-form: /{mount}/.well-known/oauth-protected-resource
        # mount is a single path segment, e.g. "juspay-dashboard-stream"
        tcfg = resolve_tenant(cfg, request)
        mount = request.path_params["mount"]
        resource_url = f"{tcfg.mcp_server_url}/{mount}"
        return JSONResponse(protected_resource_metadata(tcfg, resource_url=resource_url))

    async def prm_reverse_form(request: Request) -> Response:
        # Reverse-form (RFC 9728 §4): /.well-known/oauth-protected-resource/{full_path}
        # full_path may span multiple segments, e.g. "dashboard/juspay-dashboard-stream"
        # The resource URL is reconstructed from the host origin, not mcp_server_url,
        # because the reverse-form encodes the full absolute path from the host root.
        tcfg = resolve_tenant(cfg, request)
        full_path = request.path_params["full_path"]
        parsed = urlparse(tcfg.mcp_server_url)
        host_origin = f"{parsed.scheme}://{parsed.netloc}"
        resource_url = f"{host_origin}/{full_path}"
        return JSONResponse(protected_resource_metadata(tcfg, resource_url=resource_url))

    async def asm(request: Request) -> Response:
        return JSONResponse(authorization_server_metadata(resolve_tenant(cfg, request)))

    async def jwks(_: Request) -> Response:
        return JSONResponse({"keys": []})

    # ---------- RFC 7591 dynamic client registration --------------------------
    async def register(request: Request) -> Response:
        try:
            body = await request.json()
        except Exception:
            body = {}

        redirect_uris = body.get("redirect_uris") or []
        if not isinstance(redirect_uris, list) or not redirect_uris:
            return _bad_request(
                "invalid_client_metadata", "redirect_uris is required and must be a non-empty list"
            )
        for uri in redirect_uris:
            parsed = urlparse(uri) if isinstance(uri, str) else None
            if not parsed or parsed.scheme not in ("http", "https") or not parsed.netloc:
                return _bad_request(
                    "invalid_redirect_uri", f"redirect_uri {uri!r} is not a valid absolute URL"
                )

        client_id = f"mcp_{secrets.token_hex(16)}"
        client_secret = secrets.token_hex(32)
        client_name = body.get("client_name", "MCP Client")

        await client_store.put_client(
            client_id,
            ClientData(
                client_secret=client_secret,
                redirect_uris=redirect_uris,
                client_name=client_name,
                created_at=time.time(),
            ),
        )

        return JSONResponse(
            {
                "client_id": client_id,
                "client_secret": client_secret,
                "client_id_issued_at": int(time.time()),
                "client_secret_expires_at": 0,
                "redirect_uris": redirect_uris,
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "client_secret_post",
                "client_name": client_name,
            },
            status_code=201,
        )

    # ---------- /oauth/authorize ---------------------------------------------
    async def authorize(request: Request) -> Response:
        tcfg = resolve_tenant(cfg, request)
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
        if not client_id:
            return _bad_request("invalid_request", "client_id is required")
        if not code_challenge or code_challenge_method != "S256":
            return _bad_request(
                "invalid_request",
                "PKCE (code_challenge with S256 code_challenge_method) is required",
            )
        if not _resource_is_acceptable(tcfg, resource):
            return _bad_request("invalid_target", f"resource {resource!r} is not served by this server")

        client_data = await client_store.get_client(client_id)
        if client_data is None:
            return _bad_request("invalid_client", "Unknown client_id")
        if redirect_uri not in client_data.redirect_uris:
            return _bad_request(
                "invalid_request", "redirect_uri does not match a URI registered for this client"
            )

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
            # Portal only knows our own real client_id, never the per-MCP-client one.
            "client_id": tcfg.upstream_client_id,
            "redirect_uri": f"{tcfg.mcp_server_url}/oauth/callback",
            "scope": "user_access",
            "state": state,
        }
        portal_url = f"{tcfg.portal_base_url}?{urlencode(portal_params)}"
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
        tcfg = resolve_tenant(cfg, request)
        body = await _read_form_or_json(request)
        grant_type = body.get("grant_type")
        client_id, client_secret = _parse_client_credentials(request, body)

        if not client_id or not client_secret:
            return _unauthorized_client("Client credentials required")

        # Authenticate the caller against its own registered credential only.
        client_data = await client_store.get_client(client_id)
        if client_data is None or not secrets.compare_digest(client_data.client_secret, client_secret):
            return _unauthorized_client("Invalid client credentials")

        if grant_type == "authorization_code":
            code = body.get("code")
            code_verifier = body.get("code_verifier")
            redirect_uri = body.get("redirect_uri")
            if not code:
                return _bad_request("invalid_request", "Missing authorization code")
            if not redirect_uri:
                return _bad_request("invalid_request", "redirect_uri is required")

            bound_state = await store.lookup_state_by_code(code)
            state_data = await store.get_state(bound_state) if bound_state else None
            if state_data is None:
                return _bad_request("invalid_grant", "Unknown or expired authorization code")
            if redirect_uri != state_data.redirect_uri:
                return _bad_request("invalid_grant", "redirect_uri does not match the authorize request")

            if not code_verifier:
                return _bad_request("invalid_request", "code_verifier is required for PKCE")
            if not state_data.code_challenge or not validate_s256(
                code_verifier, state_data.code_challenge
            ):
                return _bad_request("invalid_grant", "Invalid code_verifier")

            # Portal only recognizes our own real credential, not the per-client one.
            token_resp = await portal.exchange_code(
                tcfg.upstream_client_id,
                tcfg.upstream_client_secret,
                code,
                portal_base_url=tcfg.portal_base_url,
            )
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
                    "scope": " ".join(tcfg.scopes_supported),
                }
            )

        if grant_type == "refresh_token":
            refresh_token = body.get("refresh_token")
            if not refresh_token:
                return _bad_request("invalid_request", "Missing refresh_token")
            token_resp = await portal.refresh(
                tcfg.upstream_client_id,
                tcfg.upstream_client_secret,
                refresh_token,
                portal_base_url=tcfg.portal_base_url,
            )
            if token_resp is None:
                return _bad_request("invalid_grant", "Portal refresh failed")
            return JSONResponse(
                {
                    "access_token": token_resp.access_token,
                    "refresh_token": token_resp.refresh_token,
                    "expires_in": token_resp.expires_in,
                    "token_type": "Bearer",
                    "scope": " ".join(tcfg.scopes_supported),
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
        tcfg = resolve_tenant(cfg, request)

        revoked = False
        if token:
            revoked = await portal.revoke_token(
                tcfg.upstream_client_id, token, portal_base_url=tcfg.portal_base_url
            )
            # Evict the validated-token cache so subsequent requests are forced
            # to re-validate via Portal (which will now return 4xx). The cache is
            # keyed per portal, so drop every tenant's entry for this token.
            if validation_cache is not None:
                validation_cache.pop(token, None)
                suffix = f"\n{token}"
                for key in [
                    k for k in list(validation_cache)
                    if isinstance(k, str) and k.endswith(suffix)
                ]:
                    validation_cache.pop(key, None)
        elif not token:
            logger.warning("/oauth/revoke called without a `token` body field")

        return JSONResponse({"revoked": revoked})

    # ---------- assemble ------------------------------------------------------
    _WELL_KNOWN_METHODS = ["GET", "OPTIONS"]

    routes: list[Route] = [
        Route("/.well-known/oauth-protected-resource", endpoint=prm_root, methods=_WELL_KNOWN_METHODS),
        Route(
            "/.well-known/oauth-protected-resource/{full_path:path}",
            endpoint=prm_reverse_form,
            methods=_WELL_KNOWN_METHODS,
        ),
        Route(
            "/{mount:str}/.well-known/oauth-protected-resource",
            endpoint=prm_for_mount,
            methods=_WELL_KNOWN_METHODS,
        ),
        Route("/.well-known/oauth-authorization-server", endpoint=asm, methods=_WELL_KNOWN_METHODS),
        Route("/.well-known/openid-configuration", endpoint=asm, methods=_WELL_KNOWN_METHODS),
        Route("/.well-known/jwks.json", endpoint=jwks, methods=_WELL_KNOWN_METHODS),
        Route("/oauth/register", endpoint=register, methods=["POST"]),
        Route("/oauth/authorize", endpoint=authorize, methods=["GET"]),
        Route("/oauth/callback", endpoint=callback, methods=["GET"]),
        Route("/oauth/token", endpoint=token, methods=["POST"]),
        Route("/oauth/revoke", endpoint=revoke, methods=["POST"]),
    ]
    return routes
