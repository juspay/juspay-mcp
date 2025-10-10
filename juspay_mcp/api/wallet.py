# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import httpx
from juspay_mcp.config import ENDPOINTS
from juspay_mcp.api.utils import call, post

async def list_wallets(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves the list of wallets associated with a customer.

    This function sends an HTTP GET request to the Juspay List Wallets API endpoint.

    Args:
        payload (dict): Must include:
            - customer_id (str): Unique identifier of the customer.
        May include:
            - routing_id (str): Optional custom routing ID.
        meta_info (dict, optional): Authentication credentials override.

    Returns:
        dict: Parsed JSON response containing wallet details.

    Raises:
        ValueError: If customer_id is missing.
        Exception: If the API call fails.
    """
    customer_id = payload.get("customer_id")
    if not customer_id:
        raise ValueError("The payload must include 'customer_id'")

    routing_id = payload.get("routing_id", customer_id)
    api_url = f"https://api.juspay.in/customers/{customer_id}/wallets"

    return await call(api_url, routing_id, meta_info=meta_info)
