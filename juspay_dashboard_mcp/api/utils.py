# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import os
import httpx
import logging
from contextvars import ContextVar
from juspay_dashboard_mcp.config import get_common_headers, JUSPAY_BASE_URL
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Context variable to store Juspay credentials for the current request
juspay_credentials: ContextVar[dict | None] = ContextVar('juspay_credentials', default=None)

def set_juspay_credentials(creds: dict | None):
    """Set Juspay credentials for the current context."""
    juspay_credentials.set(creds)

def get_juspay_credentials() -> dict | None:
    """Get Juspay credentials from the current context."""
    return juspay_credentials.get()

async def call(api_url: str, additional_headers: dict = None, meta_info: dict = None) -> dict:
    # Get Juspay credentials from context or use meta_info for backward compatibility
    juspay_creds = get_juspay_credentials()
    if not juspay_creds and meta_info:
        juspay_creds = meta_info.get("juspay_credentials")
    
    headers = get_common_headers({}, meta_info, juspay_creds)
    
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
    # Get Juspay credentials from context or use meta_info for backward compatibility
    juspay_creds = get_juspay_credentials()
    if not juspay_creds and meta_info:
        juspay_creds = meta_info.get("juspay_credentials")
    
    headers = get_common_headers(payload, meta_info, juspay_creds) 

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

    # Get token from header credentials context first, then fallback to other sources
    juspay_creds = get_juspay_credentials()
    token_to_use = token
    if not token_to_use and juspay_creds:
        token_to_use = juspay_creds.get("dashboard_token")
    if not token_to_use:
        token_to_use = os.environ.get("JUSPAY_WEB_LOGIN_TOKEN")
    if not token_to_use and meta_info:
        token_to_use = meta_info.get("x-web-logintoken")
        
    logger.info(f"Using token for validation: {token_to_use}")  
    if not token_to_use:
        raise Exception("Juspay token not provided.")

    try:
        json_payload = {"token": token_to_use}
        juspay_creds = get_juspay_credentials()
        request_api_headers = get_common_headers(json_payload, meta_info, juspay_creds)
        if headers: # headers from function signature
            request_api_headers.update(headers)

        async with httpx.AsyncClient(timeout=30.0) as client:
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

    # Get token from header credentials context first, then fallback to other sources
    juspay_creds = get_juspay_credentials()
    token_to_use = token
    if not token_to_use and juspay_creds:
        token_to_use = juspay_creds.get("dashboard_token")
    if not token_to_use:
        token_to_use = os.environ.get("JUSPAY_WEB_LOGIN_TOKEN")
    if not token_to_use and meta_info:
        token_to_use = meta_info.get("x-web-logintoken")
        
    if not token_to_use:
        raise Exception("Juspay token not provided.")

    try:
        json_payload = {"token": token_to_use}
        # Pass juspay_creds to get_common_headers to avoid environment variable verification
        juspay_creds = get_juspay_credentials()
        request_api_headers = get_common_headers(json_payload, meta_info, juspay_creds)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                validate_url,
                headers=request_api_headers,
                json=json_payload
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
    
def ist_to_utc(ist_time_string, format="%Y-%m-%dT%H:%M:%SZ"):
    """Convert IST time to UTC time.

    Args:
        ist_time_string: Can be either a string in format "%Y-%m-%dT%H:%M:%SZ" or a datetime object
        format: Output format for the returned timestamp

    Returns:
        A string in the specified format
    """
    try:
        # Handle both string and datetime inputs
        if isinstance(ist_time_string, datetime):
            ist_time = ist_time_string
        else:
            ist_time = datetime.strptime(ist_time_string, "%Y-%m-%dT%H:%M:%SZ")

        ist_offset = timedelta(hours=5, minutes=30)
        utc_time = ist_time - ist_offset

        # Check if the UTC time is exactly 18:29:00 and adjust if necessary
        if utc_time.time() == datetime.strptime("18:29:00", "%H:%M:%S").time():
            utc_time += timedelta(seconds=59)

        return utc_time.strftime(format)
    except Exception as e:
        logging.error(f"Error converting ist to utc: {str(e)}")
        # If it's already a datetime, try to return a formatted string
        if isinstance(ist_time_string, datetime):
            return ist_time_string.strftime(format)
        return str(ist_time_string)
    

def utc_to_ist(utc_time_string: str) -> str:
    try:
        # Try parsing with T separator first
        try:
            utc_time = datetime.strptime(utc_time_string, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            # If that fails, try parsing with space separator
            utc_time = datetime.strptime(utc_time_string, "%Y-%m-%d %H:%M:%S")

        ist_offset = timedelta(hours=5, minutes=30)
        ist_time = utc_time + ist_offset
        return ist_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception as e:
        logging.error(f"Error converting utc to ist: {str(e)}")
        return utc_time_string
