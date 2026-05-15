"""End-to-end OAuth flow including PKCE round-trip with a stubbed Portal.

Stubs out PortalClient.exchange_code / refresh / validate so we can assert the
full authorize -> callback -> token -> authed-mcp path without touching the
real Portal.
"""

from __future__ import annotations

import asyncio
import os
import sys

os.environ["OAUTH_ENABLED"] = "true"
os.environ["JUSPAY_MCP_TYPE"] = "DASHBOARD"
os.environ.setdefault("MCP_SERVER_URL", "http://localhost:8080")
os.environ.setdefault("PORTAL_BASE_URL", "https://portal.juspay.in")
os.environ.setdefault("OAUTH_CLIENT_ID", "test-client")
os.environ.setdefault("OAUTH_CLIENT_SECRET", "test-secret")

import httpx
from httpx import ASGITransport
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Route

from juspay_mcp.auth import config as auth_config
from juspay_mcp.auth.context import PortalUserInfo
from juspay_mcp.auth.middleware import BearerAuthMiddleware
from juspay_mcp.auth.portal_client import PortalClient, TokenResponse
from juspay_mcp.auth.routes import build_routes
from juspay_mcp.auth.state_store import MemoryStateStore


CODE_VERIFIER = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
CODE_CHALLENGE = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
ISSUED_TOKEN = "portal-access-token-xyz"
ISSUED_REFRESH = "portal-refresh-token-xyz"


class StubPortal:
    """Replaces PortalClient methods used by routes/middleware."""

    def __init__(self):
        self.exchange_calls = 0
        self.refresh_calls = 0
        self.validate_calls = 0
        self.revoke_calls: list[tuple[str, str]] = []
        # When set, validate() returns None for `revoked_tokens` to simulate
        # Portal rejecting the revoked bearer on subsequent re-validation.
        self.revoked_tokens: set[str] = set()

    async def exchange_code(self, client_id, client_secret, code):
        self.exchange_calls += 1
        return TokenResponse(
            access_token=ISSUED_TOKEN,
            refresh_token=ISSUED_REFRESH,
            expires_in=3600,
            token_type="Bearer",
        )

    async def refresh(self, client_id, client_secret, refresh_token):
        self.refresh_calls += 1
        return TokenResponse(
            access_token="portal-access-token-NEW",
            refresh_token="portal-refresh-token-NEW",
            expires_in=3600,
            token_type="Bearer",
        )

    async def validate(self, token):
        self.validate_calls += 1
        if token in self.revoked_tokens:
            return None
        if token == ISSUED_TOKEN or token == "portal-access-token-NEW":
            return PortalUserInfo(
                merchant_id="STUB_MERCHANT",
                user_id="42",
                email="t@example.com",
                context="MERCHANT",
                username="t",
                tenant_account_id=None,
                valid_host="portal.juspay.in",
            )
        return None

    async def revoke_token(self, client_id, token):
        self.revoke_calls.append((client_id, token))
        self.revoked_tokens.add(token)
        return True

    async def aclose(self):
        pass


async def fake_dashboard(request):
    from starlette.responses import JSONResponse
    ctx = getattr(request.state, "oauth_context", None)
    return JSONResponse({"merchant_id": ctx.user_info.merchant_id if ctx else None})


PASS = "[OK]"
FAIL = "[FAIL]"
failures = 0


def check(label, cond, detail=""):
    global failures
    print(f"{PASS if cond else FAIL} {label}" + (f"  — {detail}" if detail else ""))
    if not cond:
        failures += 1


async def run():
    cfg = auth_config.load()
    stub = StubPortal()
    store = MemoryStateStore(ttl_seconds=cfg.state_ttl_seconds)
    validation_cache: dict = {}

    routes = build_routes(cfg, stub, store, validation_cache=validation_cache) + [
        Route(
            "/juspay-dashboard-stream",
            endpoint=fake_dashboard,
            methods=["GET", "POST", "DELETE"],
        ),
    ]
    middleware = [
        Middleware(
            BearerAuthMiddleware,
            cfg=cfg,
            portal=stub,
            validation_cache=validation_cache,
        )
    ]
    app = Starlette(routes=routes, middleware=middleware)

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost:8080") as c:
        # 1. /authorize stores state + PKCE
        state = "state-abc"
        r = await c.get(
            "/oauth/authorize",
            params={
                "client_id": "test-client",
                "redirect_uri": "http://localhost:33418/callback",
                "state": state,
                "code_challenge": CODE_CHALLENGE,
                "code_challenge_method": "S256",
                "resource": "http://localhost:8080/juspay-dashboard-stream",
            },
            follow_redirects=False,
        )
        check("authorize -> 302 portal", r.status_code == 302)

        # Verify state was persisted
        sd = await store.get_state(state)
        check("state persisted with PKCE", sd is not None and sd.code_challenge == CODE_CHALLENGE)

        # 2. /callback with code -> 302 back to client redirect_uri
        portal_code = "portal-auth-code-xxx"
        r = await c.get(
            "/oauth/callback",
            params={"code": portal_code, "state": state},
            follow_redirects=False,
        )
        check("callback -> 302", r.status_code == 302)
        loc = r.headers.get("location", "")
        check("callback redirect to client", loc.startswith("http://localhost:33418/callback"), loc)
        check("redirect carries code+state", "code=" in loc and "state=" in loc, loc)
        check("code bound to state in store", (await store.lookup_state_by_code(portal_code)) == state)

        # 3. /token with bad PKCE -> invalid_grant
        r = await c.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": "test-client",
                "client_secret": "test-secret",
                "code": portal_code,
                "code_verifier": "WRONG_VERIFIER",
            },
        )
        check("bad PKCE -> 400 invalid_grant", r.status_code == 400 and r.json().get("error") == "invalid_grant")

        # 4. /token with correct PKCE -> 200 with access_token
        r = await c.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": "test-client",
                "client_secret": "test-secret",
                "code": portal_code,
                "code_verifier": CODE_VERIFIER,
            },
        )
        check("good PKCE -> 200", r.status_code == 200, r.text)
        tok = r.json()
        check("token body has access_token", tok.get("access_token") == ISSUED_TOKEN)
        check("token body has refresh_token", tok.get("refresh_token") == ISSUED_REFRESH)
        check("Portal.exchange_code called once", stub.exchange_calls == 1)
        # code+state should be evicted
        check("state evicted after success", (await store.get_state(state)) is None)
        check("code evicted after success", (await store.lookup_state_by_code(portal_code)) is None)

        # 5. authed MCP call with the new bearer
        r = await c.post(
            "/juspay-dashboard-stream",
            headers={"Authorization": f"Bearer {ISSUED_TOKEN}"},
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        )
        check("authed call -> 200", r.status_code == 200)
        check("merchant_id from Portal", r.json().get("merchant_id") == "STUB_MERCHANT")

        # 6. validate cache: second call should NOT bump validate counter
        prev = stub.validate_calls
        await c.post(
            "/juspay-dashboard-stream",
            headers={"Authorization": f"Bearer {ISSUED_TOKEN}"},
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        )
        check("validate cache prevents repeat Portal hit", stub.validate_calls == prev)

        # 7. refresh_token grant
        r = await c.post(
            "/oauth/token",
            data={
                "grant_type": "refresh_token",
                "client_id": "test-client",
                "client_secret": "test-secret",
                "refresh_token": ISSUED_REFRESH,
            },
        )
        check("refresh -> 200", r.status_code == 200)
        check("refresh issued new access_token", r.json().get("access_token") == "portal-access-token-NEW")
        check("Portal.refresh called once", stub.refresh_calls == 1)

        # 8. invalid bearer -> 401 with invalid_token
        r = await c.post(
            "/juspay-dashboard-stream",
            headers={"Authorization": "Bearer not-a-real-token"},
            json={"jsonrpc": "2.0", "id": 3, "method": "tools/list"},
        )
        check("invalid token -> 401", r.status_code == 401)
        wwa = r.headers.get("www-authenticate", "")
        check("invalid token WWW-Authenticate has error=invalid_token", 'error="invalid_token"' in wwa, wwa)

        # 9. resource mismatch -> invalid_target
        r = await c.get(
            "/oauth/authorize",
            params={
                "client_id": "x",
                "redirect_uri": "http://localhost/cb",
                "state": "s2",
                "code_challenge": CODE_CHALLENGE,
                "code_challenge_method": "S256",
                "resource": "https://evil.example.com/mcp",
            },
            follow_redirects=False,
        )
        check("foreign resource -> 400 invalid_target", r.status_code == 400 and r.json().get("error") == "invalid_target")

        # 10. revoke — calls Portal, evicts validation cache, subsequent
        # /juspay-dashboard-stream with the revoked bearer must 401.
        # First prime the cache with one authed call.
        r = await c.post(
            "/juspay-dashboard-stream",
            headers={"Authorization": f"Bearer {ISSUED_TOKEN}"},
            json={"jsonrpc": "2.0", "id": 10, "method": "tools/list"},
        )
        check("pre-revoke authed call -> 200", r.status_code == 200)
        check("token is in validation cache", ISSUED_TOKEN in validation_cache)

        prev_revoke_calls = len(stub.revoke_calls)
        r = await c.post(
            "/oauth/revoke",
            data={
                "token": ISSUED_TOKEN,
                "client_id": "test-client",
                "client_secret": "test-secret",
            },
        )
        check("revoke -> 200", r.status_code == 200, r.text)
        check("revoke body says revoked=true", r.json().get("revoked") is True, r.text)
        check(
            "Portal.revoke_token called with correct args",
            stub.revoke_calls[-1] == ("test-client", ISSUED_TOKEN),
        )
        check(
            "Portal.revoke_token called exactly once for this revoke",
            len(stub.revoke_calls) == prev_revoke_calls + 1,
        )
        check("validation cache evicted", ISSUED_TOKEN not in validation_cache)

        # 11. Post-revoke: same bearer must now 401 because Portal validation
        # is forced (cache miss) and the stub marks the token as revoked.
        r = await c.post(
            "/juspay-dashboard-stream",
            headers={"Authorization": f"Bearer {ISSUED_TOKEN}"},
            json={"jsonrpc": "2.0", "id": 11, "method": "tools/list"},
        )
        check("post-revoke call -> 401", r.status_code == 401)

        # 12. /oauth/revoke without a token still 200 per RFC 7009 §2.2.
        r = await c.post("/oauth/revoke", data={"client_id": "test-client"})
        check("revoke without token still 200", r.status_code == 200)
        check("revoke without token revoked=false", r.json().get("revoked") is False, r.text)

    print()
    if failures:
        print(f"{FAIL} {failures} assertion(s) failed")
        sys.exit(1)
    print(f"{PASS} all flow checks passed")


if __name__ == "__main__":
    asyncio.run(run())
