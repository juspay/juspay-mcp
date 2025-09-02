# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import httpx
from juspay_mcp.config import get_json_headers
import logging 
from contextvars import ContextVar

logger = logging.getLogger(__name__)

# Context variable to store Juspay credentials for the current request
juspay_credentials: ContextVar[dict | None] = ContextVar('juspay_credentials', default=None)

def set_juspay_credentials(creds: dict | None):
    """Set Juspay credentials for the current context."""
    juspay_credentials.set(creds)

def get_juspay_credentials() -> dict | None:
    """Get Juspay credentials from the current context."""
    return juspay_credentials.get()

async def call(api_url: str, customer_id: str | None = None, additional_headers: dict = None) -> dict:
    # Get Juspay credentials from context
    juspay_creds = get_juspay_credentials()
    headers = get_json_headers(routing_id=customer_id, juspay_creds=juspay_creds)
    
    if additional_headers:
        headers.update(additional_headers)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            safe_headers = ["x-request-id"]
            logger.info(
                f"Calling Juspay API at: {api_url} with permitted headers: {safe_headers if safe_headers else 'None'}"
            )
            response = await client.get(api_url, headers=headers)
            logger.info(f"Response: {response}")
            response.raise_for_status()
            response_data = response.json()
            logger.info(f"Get API Response Data: {response_data}")
            return response_data
        except httpx.HTTPStatusError as e:
            error_content = e.response.text if e.response else "Unknown error"
            logger.error(f"HTTP error: {e.response.status_code if e.response else 'No response'} - {error_content}")
            raise Exception(f"Juspay API HTTPError ({e.response.status_code if e.response else 'Unknown status'}): {error_content}") from e
        except Exception as e:
            logger.error(f"Error during Juspay API call: {e}")
            raise Exception(f"Failed to call Juspay API: {e}") from e

async def post(api_url: str, payload: dict, routing_id: str | None = None) -> dict:
    effective_routing_id = routing_id or payload.get("customer_id")
    # Get Juspay credentials from context
    juspay_creds = get_juspay_credentials()
    headers = get_json_headers(routing_id=effective_routing_id, juspay_creds=juspay_creds) 

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info(f"Calling Juspay API at: {api_url} with body: {payload}")
            response = await client.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()
            logger.info(f"API Response Data: {response_data}")
            return response_data
        except httpx.HTTPStatusError as e:
            error_content = e.response.text if e.response else "Unknown error"
            logger.error(f"HTTP error: {e.response.status_code if e.response else 'No response'} - {error_content}")
            raise Exception(f"Juspay API HTTPError ({e.response.status_code if e.response else 'Unknown status'}): {error_content}") from e
        except Exception as e:
            logger.error(f"Error during Juspay API call: {e}")
            raise Exception(f"Failed to call Juspay API: {e}") from e
