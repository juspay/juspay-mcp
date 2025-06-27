# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import os
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
        

async def get_juspay_host_from_api(token: str = None, headers: dict = None, meta_info: dict = None) -> str:
    """
    Returns the Juspay host URL based on token validation.
    Calls the validate API and uses the 'validHost' field from the response.
    """
    validate_url = f"{JUSPAY_BASE_URL}/api/ec/v1/validate/token"

    token_to_use = token or (meta_info.get("x-web-logintoken") if meta_info else None) or os.environ.get("JUSPAY_WEB_LOGIN_TOKEN")
    logger.info(f"Using token for validation: {token_to_use}")  
    if not token_to_use:
        raise Exception("Juspay token not provided.")

    try:
        json_payload = {"token": token_to_use}
        request_api_headers = get_common_headers(json_payload, meta_info)
        if headers: # headers from function signature
            request_api_headers.update(headers)

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                validate_url,
                headers=request_api_headers,
                json=json_payload
            )
            resp.raise_for_status()
            data = resp.json()
            valid_host = data.get("validHost")
            if not valid_host:
                raise Exception("validHost not found in Juspay token validation response.")
            if not valid_host.startswith("http"):
                valid_host = f"https://{valid_host}"
            return valid_host
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        raise

async def get_admin_host(token: str = None, headers: dict = None ,meta_info: dict = None) -> tuple[str, bool]:
    """
    Returns the Juspay host URL based on token validation and a boolean indicating if context is JUSPAY.
    Calls the validate API and uses the 'validHost' field from the response.
    
    Returns:
        tuple: (valid_host, isadmin)
            - valid_host: The host URL string
            - isadmin: True if context is "JUSPAY", False otherwise
    """
    validate_url = f"{JUSPAY_BASE_URL}/api/ec/v1/validate/token"

    token_to_use = token or (meta_info.get("x-web-logintoken") if meta_info else None) or os.environ.get("JUSPAY_WEB_LOGIN_TOKEN")
    if not token_to_use:
        raise Exception("Juspay token not provided.")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                validate_url,
                headers={
                    "accept": "*/*",
                    "accept-language": "en-US,en;q=0.9",
                    "content-type": "application/json"
                },
                json={"token": token_to_use}
            )
            resp.raise_for_status()
            data = resp.json()
            context = data.get("context")
            # Check if context is JUSPAY
            isadmin = context == "JUSPAY" 
            
            valid_host = data.get("validHost")
            if not valid_host:
                raise Exception("validHost not found in Juspay token validation response.")
            if not valid_host.startswith("http"):
                valid_host = f"https://{valid_host}"
            
            return valid_host, isadmin
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        raise