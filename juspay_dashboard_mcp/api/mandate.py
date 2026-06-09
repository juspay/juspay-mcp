# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import logging
from juspay_dashboard_mcp.api.utils import call, get_admin_host

logger = logging.getLogger(__name__)

# Fields visible in the Mandate Details screen (screenshot)
# Field names match the actual API response keys inside `mandateDetails`
MANDATE_DETAIL_FIELDS = {
    "mandateId",          # Mandate ID
    "status",             # e.g. REVOKED
    "gateway",            # e.g. YES_BIZ
    "frequency",          # e.g. ASPRESENTED
    "maxAmount",          # e.g. 15000
    "currency",           # e.g. INR
    "paymentMethod",      # e.g. PAY
    "paymentMethodType",  # e.g. UPI
    "mandateType",        # e.g. EMANDATE
    "merchantCustomerId", # Customer Id shown on screen
    "startDate",
    "endDate",
    "dateCreated",
    "lastModified",
    "orderId",            # Mandate Register Order Id shown on screen
    "mandateRevokeSource",
}


async def get_mandate_details_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves details for a specific mandate by mandate ID.

    The API endpoint is:
        https://portal.juspay.in/ec/v1/mandateDetails/{mandate_id} (for admin users)
        https://portal.juspay.in/api/ec/v1/mandateDetails/{mandate_id} (for non-admin users)

    Headers include:
        - x-tenant-id from payload (optional)
        - x-web-logintoken from credentials

    Args:
        payload (dict): A dictionary with the following required key:
            - mandate_id: The mandate identifier to fetch details for.

    Returns:
        dict: Filtered response containing only the fields shown in the Mandate Details screen:
            mandateId, status, gateway, frequency, maxAmount, currency,
            paymentMethod, paymentMethodType, mandateType, customerId,
            startDate, endDate, dateCreated, lastModified,
            mandateRegisterOrderId, mandateRevokeSource.

    Raises:
        ValueError: If mandate_id is missing from the payload.
        Exception: If the API call fails.
    """
    mandate_id = payload.pop("mandate_id", None)
    if not mandate_id:
        raise ValueError("The payload must include 'mandate_id'.")

    host, isadmin = await get_admin_host(meta_info=meta_info)

    if isadmin:
        api_url = f"{host}/ec/v1/mandateDetails/{mandate_id}"
    else:
        api_url = f"{host}/api/ec/v1/mandateDetails/{mandate_id}"

    logger.info(f"Fetching mandate details for mandate_id={mandate_id}, url={api_url}")

    response = await call(api_url, None, meta_info)

    # The API wraps data inside a "mandateDetails" key — unwrap it first
    if isinstance(response, dict):
        details = response.get("mandateDetails", response)
        filtered = {k: v for k, v in details.items() if k in MANDATE_DETAIL_FIELDS}
        logger.info(f"Filtered mandate response: {filtered}")
        return filtered

    return response
