# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt
"""Thin async wrapper around the Juspay Portal OAuth endpoints.

We use Portal as the upstream identity provider. The wire shapes (paths, body
schema, `resource` query trick on /authorize) are taken from the
juspay-genius/genius-mcp-app reference implementation so behaviour matches
across both MCP servers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from .config import OAuthConfig
from .context import PortalUserInfo

logger = logging.getLogger(__name__)

# Portal is byte-strict about this query string. It MUST be emitted exactly as:
#     resource={%22COMMON%22%20%3A%20%22R%22}
# with literal `{` `}` (not %7B / %7D) and `%20` for spaces (not `+`). Anything
# else — including RFC-equivalent encodings — gets a 400. This matches the form
# used by genius-mcp-app/main.ts:225 and by the working curl example Portal
# documents. We pass the URL as a complete string to httpx (httpx preserves
# query bytes when given a URL string) — passing via params= triggers httpx's
# QueryParams encoder, which produces the wrong form.
_PORTAL_VALIDATE_QUERY = "resource={%22COMMON%22%20%3A%20%22R%22}"


@dataclass(frozen=True)
class TokenResponse:
    access_token: str
    refresh_token: str | None
    expires_in: int
    token_type: str


class PortalClient:
    def __init__(self, cfg: OAuthConfig, http: httpx.AsyncClient | None = None) -> None:
        self._cfg = cfg
        self._http = http or httpx.AsyncClient(timeout=30.0)
        self._owns_http = http is None

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def exchange_code(
        self, client_id: str, client_secret: str, code: str
    ) -> TokenResponse | None:
        try:
            resp = await self._http.post(
                f"{self._cfg.portal_base_url}/ec/v2/token",
                json={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "action": "generate_token",
                    "code": code,
                },
                headers={"Content-Type": "application/json"},
            )
        except httpx.HTTPError as e:
            logger.error("portal token exchange failed: %s", e)
            return None

        if resp.status_code >= 400:
            logger.error(
                "portal token exchange returned %d: %s",
                resp.status_code,
                resp.text[:500],
            )
            return None

        body = resp.json()
        return TokenResponse(
            access_token=body["access_token"],
            refresh_token=body.get("refresh_token"),
            expires_in=int(body.get("expires_in", 3600)),
            token_type=body.get("token_type", "Bearer"),
        )

    async def refresh(
        self, client_id: str, client_secret: str, refresh_token: str
    ) -> TokenResponse | None:
        try:
            resp = await self._http.post(
                f"{self._cfg.portal_base_url}/ec/v2/token",
                json={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "action": "refresh_token",
                    "refresh_token": refresh_token,
                },
                headers={"Content-Type": "application/json"},
            )
        except httpx.HTTPError as e:
            logger.error("portal refresh failed: %s", e)
            return None

        if resp.status_code >= 400:
            logger.error(
                "portal refresh returned %d: %s",
                resp.status_code,
                resp.text[:500],
            )
            return None

        body = resp.json()
        return TokenResponse(
            access_token=body["access_token"],
            refresh_token=body.get("refresh_token"),
            expires_in=int(body.get("expires_in", 3600)),
            token_type=body.get("token_type", "Bearer"),
        )

    async def revoke_token(self, client_id: str, token: str) -> bool:
        """Tell Portal to invalidate the OAuth session backing this bearer.

        Mirrors the dashboard's logout call:
            DELETE /ec/v1/token/revoke/entity
            Headers: Content-Type + x-web-logintoken (the bearer being revoked)
            Body:    {"client_id": "...", "scope": "user_access"}

        Best-effort: returns True on 2xx, False otherwise. The /oauth/revoke
        endpoint must always reply 200 to its caller per RFC 7009 §2.2, even
        if Portal rejects — so we just log on failure.
        """
        url = f"{self._cfg.portal_base_url}/ec/v1/token/revoke/entity"
        headers = {
            "Content-Type": "application/json",
            "x-web-logintoken": token,
        }
        body = {"client_id": client_id, "scope": "user_access"}
        try:
            resp = await self._http.request(
                "DELETE", url, json=body, headers=headers, timeout=10.0
            )
        except httpx.HTTPError as e:
            logger.error("portal revoke failed: %s", e)
            return False
        if resp.status_code >= 400:
            logger.warning(
                "portal revoke returned %d: %s",
                resp.status_code,
                resp.text[:300],
            )
            return False
        logger.info("portal revoke OK: %d", resp.status_code)
        return True

    async def validate(self, token: str) -> PortalUserInfo | None:
        # Build the URL as a string so httpx preserves the query verbatim.
        # See the comment on _PORTAL_VALIDATE_QUERY for why this matters.
        url = f"{self._cfg.portal_base_url}/ec/v2/authorize?{_PORTAL_VALIDATE_QUERY}"
        try:
            resp = await self._http.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
            )
        except httpx.HTTPError as e:
            logger.error("portal validate failed: %s", e)
            return None

        if resp.status_code >= 400:
            logger.warning(
                "portal validate returned %d: %s",
                resp.status_code,
                resp.text[:300],
            )
            return None

        body = resp.json()
        # Portal returns camelCase. Be defensive: tolerate either case.
        merchant_id = body.get("merchantId") or body.get("merchant_id") or ""
        user_id = body.get("userId") or body.get("user_id") or ""
        return PortalUserInfo(
            merchant_id=str(merchant_id),
            user_id=str(user_id),
            email=body.get("email", ""),
            context=body.get("context", "MERCHANT"),
            username=body.get("username"),
            tenant_account_id=body.get("tenantAccountId") or body.get("tenant_account_id"),
            valid_host=body.get("validHost") or body.get("valid_host"),
        )
