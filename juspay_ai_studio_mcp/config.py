# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import logging
import os

import dotenv

logger = logging.getLogger(__name__)

dotenv.load_dotenv()

JUSPAY_ENV = os.getenv("JUSPAY_ENV", "production").lower()
PP_AI_STUDIO_BASE_URL = (
    os.getenv("PP_AI_STUDIO_BASE_URL")
    or os.getenv("JUSPAY_AI_STUDIO_BASE_URL")
    or "http://localhost:8001"
).rstrip("/")
JUSPAY_AI_STUDIO_TOKEN = (
    os.getenv("PP_AI_STUDIO_API_KEY")
    or os.getenv("PP_AI_STUDIO_TOKEN")
    or os.getenv("JUSPAY_AI_STUDIO_TOKEN")
    or os.getenv("JUSPAY_WEB_LOGIN_TOKEN")
)

if JUSPAY_ENV == "production":
    JUSPAY_BASE_URL = os.getenv(
        "JUSPAY_AI_STUDIO_PROD_BASE_URL",
        os.getenv("JUSPAY_PROD_BASE_URL", "https://portal.juspay.in"),
    )
    logger.info("Using Juspay AI Studio Production Environment")
else:
    JUSPAY_BASE_URL = os.getenv(
        "JUSPAY_AI_STUDIO_SANDBOX_BASE_URL",
        os.getenv("JUSPAY_SANDBOX_BASE_URL", "https://sandbox.portal.juspay.in"),
    )
    logger.info("Using Juspay AI Studio Sandbox Environment")


def verify_env_vars():
    """Verifies that required AI Studio environment variables are set."""
    if not JUSPAY_AI_STUDIO_TOKEN:
        raise ValueError(
            "PP_AI_STUDIO_API_KEY, PP_AI_STUDIO_TOKEN, JUSPAY_AI_STUDIO_TOKEN, or JUSPAY_WEB_LOGIN_TOKEN environment variable must be set."
        )


def _token_from_credentials(juspay_creds: dict | None) -> str | None:
    if not juspay_creds:
        return None
    return (
        juspay_creds.get("pp_ai_studio_api_key")
        or juspay_creds.get("pp_ai_studio_token")
        or juspay_creds.get("ai_studio_token")
        or juspay_creds.get("dashboard_token")
        or juspay_creds.get("api_key")
    )


def verify_dynamic_credentials(juspay_creds: dict):
    """Verifies that required AI Studio credentials are present in the auth context."""
    if not juspay_creds:
        raise ValueError("No Juspay credentials found in authentication context")

    if not _token_from_credentials(juspay_creds):
        raise ValueError("Missing PP Studio AI token/API key in Juspay credentials")


def get_common_headers(payload: dict | None = None, meta_info: dict = None, juspay_creds: dict = None):
    """
    Returns common headers used by AI Studio API calls.
    Request-scoped credentials win over meta_info and environment variables.
    """
    payload = payload or {}
    token = None

    if juspay_creds:
        verify_dynamic_credentials(juspay_creds)
        token = _token_from_credentials(juspay_creds)
    elif meta_info:
        token = (
            meta_info.get("pp_ai_studio_api_key")
            or meta_info.get("pp_ai_studio_token")
            or meta_info.get("x-web-logintoken")
            or meta_info.get("ai_studio_token")
            or JUSPAY_AI_STUDIO_TOKEN
        )
    else:
        verify_env_vars()
        token = JUSPAY_AI_STUDIO_TOKEN

    if not token:
        raise ValueError(
            "PP_AI_STUDIO_API_KEY, PP_AI_STUDIO_TOKEN, JUSPAY_AI_STUDIO_TOKEN, JUSPAY_WEB_LOGIN_TOKEN, or request token must be set."
        )

    default_headers = {
        "Content-Type": "application/json",
        "accept": "*/*",
        "Authorization": f"Bearer {token}",
        "juspay_token": token,
        "x-api-key": token,
        "x-request-id": f"mcp-ai-studio-{os.urandom(6).hex()}",
    }

    if isinstance(payload, dict):
        if payload.get("tenant_id"):
            default_headers["x-tenant-id"] = payload.pop("tenant_id")

        if payload.get("tenant_host"):
            default_headers["x-tenant-host"] = payload.pop("tenant_host")

        if payload.get("x-tenant-id"):
            default_headers["x-tenant-id"] = payload.pop("x-tenant-id")

        if payload.get("x-tenant-host"):
            default_headers["x-tenant-host"] = payload.pop("x-tenant-host")

        if payload.get("cookie"):
            default_headers["cookie"] = payload.pop("cookie")

        if payload.get("x-source-id"):
            default_headers["x-source-id"] = payload.pop("x-source-id")
        else:
            default_headers["x-source-id"] = "juspay-ai-studio-mcp"
    else:
        default_headers["x-source-id"] = "juspay-ai-studio-mcp"

    return default_headers
