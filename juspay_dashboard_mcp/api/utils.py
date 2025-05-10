# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import httpx
import logging
from juspay_dashboard_mcp.config import get_common_headers, JUSPAY_BASE_URL

logger = logging.getLogger(__name__)

async def call(api_url: str, additional_headers: dict = None, meta_info: dict = None) -> dict:
    headers = get_common_headers({}, meta_info)
    
    if additional_headers:
        headers.update(additional_headers)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info(f"Calling Juspay API at: {api_url} with headers: {headers}")
            response = await client.get(api_url, headers=headers)
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

async def post(api_url: str, payload: dict,additional_headers: dict = None, meta_info: dict= None) -> dict:
    headers = get_common_headers(payload, meta_info) 

    if additional_headers:
        headers.update(additional_headers)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info(f"Calling Juspay API at: {api_url} with body: {payload} and headers: {headers}")
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
        

async def get_juspay_host_from_api(token: str = None, headers: dict = None) -> str:
    """
    Returns the appropriate Juspay host URL based on the environment.
    
    Note: Previously this validated the token, but now uses JUSPAY_WEB_LOGIN_TOKEN 
    environment variable directly. The token parameter is kept for backward compatibility.

    Returns:
        str: The Juspay host URL.
    """
    return JUSPAY_BASE_URL
