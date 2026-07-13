# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import logging
import os
from contextvars import ContextVar

import httpx

from juspay_ai_studio_mcp.config import JUSPAY_BASE_URL, get_common_headers

logger = logging.getLogger(__name__)

ai_studio_credentials: ContextVar[dict | None] = ContextVar(
    "ai_studio_credentials",
    default=None,
)


def set_ai_studio_credentials(creds: dict | None):
    """Set Juspay credentials for the current AI Studio request context."""
    ai_studio_credentials.set(creds)


def get_ai_studio_credentials() -> dict | None:
    """Get Juspay credentials from the current AI Studio request context."""
    return ai_studio_credentials.get()


async def call(api_url: str, additional_headers: dict = None, meta_info: dict = None) -> dict:
    juspay_creds = get_ai_studio_credentials()
    if not juspay_creds and meta_info:
        juspay_creds = meta_info.get("juspay_credentials")

    headers = get_common_headers({}, meta_info, juspay_creds)
    if additional_headers:
        headers.update(additional_headers)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info(f"GET {api_url}")
            response = await client.get(api_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_content = e.response.text if e.response else "Unknown error"
            logger.error(f"HTTP error: {e.response.status_code if e.response else 'No response'} - {error_content}")
            raise Exception(
                f"Juspay AI Studio API HTTPError ({e.response.status_code if e.response else 'Unknown status'}): {error_content}"
            ) from e
        except Exception as e:
            logger.error(f"Error during Juspay AI Studio API call: {e}")
            raise Exception(f"Failed to call Juspay AI Studio API: {e}") from e


async def post(api_url: str, payload: dict, additional_headers: dict = None, meta_info: dict = None) -> dict:
    juspay_creds = get_ai_studio_credentials()
    if not juspay_creds and meta_info:
        juspay_creds = meta_info.get("juspay_credentials")

    headers = get_common_headers(payload, meta_info, juspay_creds)
    if additional_headers:
        headers.update(additional_headers)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info(f"POST {api_url}")
            response = await client.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_content = e.response.text if e.response else "Unknown error"
            logger.error(f"HTTP error: {e.response.status_code if e.response else 'No response'} - {error_content}")
            raise Exception(
                f"Juspay AI Studio API HTTPError ({e.response.status_code if e.response else 'Unknown status'}): {error_content}"
            ) from e
        except Exception as e:
            logger.error(f"Error during Juspay AI Studio POST call: {e}")
            raise Exception(f"Failed to call Juspay AI Studio API: {e}") from e


async def put(api_url: str, payload: dict, additional_headers: dict = None, meta_info: dict = None):
    juspay_creds = get_ai_studio_credentials()
    if not juspay_creds and meta_info:
        juspay_creds = meta_info.get("juspay_credentials")

    headers = get_common_headers(payload, meta_info, juspay_creds)
    if additional_headers:
        headers.update(additional_headers)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info(f"PUT {api_url}")
            response = await client.put(api_url, headers=headers, json=payload)
            response.raise_for_status()
            try:
                return response.json()
            except ValueError:
                return response.text
        except httpx.HTTPStatusError as e:
            error_content = e.response.text if e.response else "Unknown error"
            logger.error(f"HTTP error: {e.response.status_code if e.response else 'No response'} - {error_content}")
            raise Exception(
                f"Juspay AI Studio API HTTPError ({e.response.status_code if e.response else 'Unknown status'}): {error_content}"
            ) from e
        except Exception as e:
            logger.error(f"Error during Juspay AI Studio PUT call: {e}")
            raise Exception(f"Failed to call Juspay AI Studio API: {e}") from e


async def get_ai_studio_host(token: str = None, headers: dict = None, meta_info: dict = None) -> str:
    """Return the host that should be used for AI Studio API calls."""
    juspay_creds = get_ai_studio_credentials()
    token_to_use = token
    if not token_to_use and juspay_creds:
        token_to_use = (
            juspay_creds.get("ai_studio_token")
            or juspay_creds.get("dashboard_token")
            or juspay_creds.get("api_key")
        )
    if not token_to_use:
        token_to_use = os.environ.get("JUSPAY_AI_STUDIO_TOKEN") or os.environ.get("JUSPAY_WEB_LOGIN_TOKEN")
    if not token_to_use and meta_info:
        token_to_use = meta_info.get("x-web-logintoken") or meta_info.get("ai_studio_token")
    if not token_to_use:
        raise Exception("Juspay AI Studio token not provided.")

    token_response = (meta_info or {}).get("token_response") or {}
    auth_type = token_response.get("auth_type")
    if not auth_type and juspay_creds:
        auth_type = juspay_creds.get("auth_type")

    if auth_type == "oauth":
        resource_param = '{%22COMMON%22%20%3A%20%22R%22}'
        url = f"{JUSPAY_BASE_URL}/ec/v2/authorize?resource={resource_param}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers={"Authorization": token_to_use})
            resp.raise_for_status()
            return JUSPAY_BASE_URL

    validate_url = f"{JUSPAY_BASE_URL}/api/ec/v1/validate/token"
    json_payload = {"token": token_to_use}
    request_headers = get_common_headers(json_payload, meta_info, juspay_creds)
    if headers:
        request_headers.update(headers)

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(validate_url, headers=request_headers, json=json_payload)
        resp.raise_for_status()
        data = resp.json()
        valid_host = data.get("validHost")
        if not valid_host:
            raise Exception("validHost not found in Juspay token validation response.")
        if not valid_host.startswith("http"):
            valid_host = f"https://{valid_host}"
        return valid_host

