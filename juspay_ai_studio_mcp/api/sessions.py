# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import logging
from urllib.parse import quote, urlencode

import httpx

from juspay_ai_studio_mcp.api.utils import get_ai_studio_credentials
from juspay_ai_studio_mcp.config import PP_AI_STUDIO_BASE_URL, get_common_headers

logger = logging.getLogger(__name__)


def _url(path: str) -> str:
    return f"{PP_AI_STUDIO_BASE_URL}{path}"


def _session_path(session_id: str, suffix: str = "") -> str:
    return f"/api/sessions/{quote(session_id, safe='')}{suffix}"


def _load_path(session_id: str, suffix: str = "") -> str:
    return f"/api/load/{quote(session_id, safe='')}{suffix}"


def _headers_payload(payload: dict | None) -> dict:
    payload = dict(payload or {})
    return {
        key: payload[key]
        for key in (
            "tenant_id",
            "tenant_host",
            "x-tenant-id",
            "x-tenant-host",
            "x-source-id",
        )
        if payload.get(key)
    }


async def _request(
    method: str,
    path: str,
    *,
    body: dict | None = None,
    query: dict | None = None,
    header_payload: dict | None = None,
    meta_info: dict | None = None,
) -> dict:
    juspay_creds = get_ai_studio_credentials()
    if not juspay_creds and meta_info:
        juspay_creds = meta_info.get("juspay_credentials")

    header_source = _headers_payload(header_payload)
    headers = get_common_headers(header_source, meta_info, juspay_creds)
    url = _url(path)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info(f"{method.upper()} {url}")
            response = await client.request(
                method,
                url,
                headers=headers,
                json=body,
                params=query,
            )
            response.raise_for_status()
            if not response.content:
                return {}
            try:
                return response.json()
            except ValueError:
                return {"text": response.text}
        except httpx.HTTPStatusError as e:
            error_content = e.response.text if e.response else "Unknown error"
            logger.error(
                f"HTTP error: {e.response.status_code if e.response else 'No response'} - {error_content}"
            )
            raise Exception(
                f"PP Studio AI API HTTPError ({e.response.status_code if e.response else 'Unknown status'}): {error_content}"
            ) from e
        except Exception as e:
            logger.error(f"Error during PP Studio AI API call: {e}")
            raise Exception(f"Failed to call PP Studio AI API: {e}") from e


async def create_session(payload: dict, meta_info: dict = None) -> dict:
    body = {
        key: payload[key]
        for key in ("client_id", "requirement", "platforms", "model", "approved_version")
        if payload.get(key) is not None
    }
    return await _request(
        "POST",
        "/api/sessions",
        body=body,
        header_payload=payload,
        meta_info=meta_info,
    )


async def resume_session(payload: dict, meta_info: dict = None) -> dict:
    body = {
        "session_id": payload["session_id"],
        "input": payload["input"],
    }
    return await _request(
        "POST",
        "/api/sessions",
        body=body,
        header_payload=payload,
        meta_info=meta_info,
    )


async def list_session(payload: dict = None, meta_info: dict = None) -> dict:
    payload = payload or {}
    query = {
        key: payload[key]
        for key in ("status", "client_id")
        if payload.get(key) is not None
    }
    return await _request(
        "GET",
        "/api/sessions",
        query=query,
        header_payload=payload,
        meta_info=meta_info,
    )


async def get_session(payload: dict, meta_info: dict = None) -> dict:
    return await _request(
        "GET",
        _session_path(payload["session_id"]),
        header_payload=payload,
        meta_info=meta_info,
    )


async def stop_session(payload: dict, meta_info: dict = None) -> dict:
    return await _request(
        "POST",
        _session_path(payload["session_id"], "/stop"),
        body={},
        header_payload=payload,
        meta_info=meta_info,
    )


async def payment_page_link(payload: dict, meta_info: dict = None) -> dict:
    session_id = payload["session_id"]
    query = {}
    if payload.get("viewport"):
        query["viewport"] = payload["viewport"]

    path = _load_path(session_id, "/payment-page")
    review_url = _url(path)
    if query:
        review_url = f"{review_url}?{urlencode(query)}"

    return {
        "session_id": session_id,
        "review_url": review_url,
        "payment_page_url": review_url,
        "preview_bootstrap_url": _url(_load_path(session_id, "/preview-bootstrap")),
        "config_version_url": _url(_load_path(session_id, "/config-version")),
    }


async def download_configs(payload: dict, meta_info: dict = None) -> dict:
    session_id = payload["session_id"]
    config_zip_url = _url(_load_path(session_id, "/config.zip"))
    result = {
        "session_id": session_id,
        "config_zip_url": config_zip_url,
        "download_url": config_zip_url,
    }

    try:
        version_response = await _request(
            "GET",
            _load_path(session_id, "/config-version"),
            header_payload=payload,
            meta_info=meta_info,
        )
        result["config_version"] = version_response.get("configVersion")
    except Exception as e:
        result["config_version"] = None
        result["warning"] = str(e)

    return result

