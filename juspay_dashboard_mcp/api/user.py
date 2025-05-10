# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from juspay_dashboard_mcp.api.utils import post, get_juspay_host_from_api

async def get_user_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Fetches details for a specific user, identified by user ID.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/user

    The call uses URL parameters:
        - userId: The unique identifier for the user

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json

    Args:
        payload (dict): A dictionary with the following required key:
            - userId: Unique identifier for the user.

    Returns:
        dict: The parsed JSON response from the Juspay Get User API.

    Raises:
        ValueError: If the userId is missing.
        Exception: If the API call fails.
    """
    if "userId" not in payload:
        raise ValueError("Payload must contain 'userId'.")

    host = await get_juspay_host_from_api()
    api_url = f"{host}/api/ec/v1/user?userId={payload['userId']}"
    return await post(api_url, {}, None, meta_info)

async def get_user_details_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves detailed information for a specific user.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v2/user/{userId}

    The call is a GET request with the userId as part of the path.

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json

    Args:
        payload (dict): A dictionary with the following required key:
            - userId: Unique identifier for the user.

    Returns:
        dict: The parsed JSON response containing detailed user information.

    Raises:
        ValueError: If the userId is missing.
        Exception: If the API call fails.
    """
    if not payload.get("userId"):
        raise ValueError("'userId' is required in the payload")

    host = await get_juspay_host_from_api()
    api_url = f"{host}/api/ec/v2/user/{payload['userId']}"
    return await post(api_url, {}, None, meta_info)

async def list_users_v2_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves a list of users associated with a merchant, with optional pagination.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v2/user/list

    The call uses JSON data containing:
        - offset: Pagination offset (optional, default 0)

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json

    Args:
        payload (dict): A dictionary that may contain:
            - offset: Pagination offset (optional, default 0)

    Returns:
        dict: The parsed JSON response containing a list of users.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api()
    api_url = f"{host}/api/ec/v2/user/list"
    
    request_data = {
        "offset": payload.get("offset", 0)
    }
    
    return await post(api_url, request_data, None, meta_info)
