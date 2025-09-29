# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from juspay_dashboard_mcp.api.utils import call, get_juspay_host_from_api, make_payout_additional_headers

async def list_beneficiaries_per_customerId_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves a list of all beneficiaries associated with a specific customer ID.
    This API returns beneficiary details including account information, verification
    status, and configuration details for all beneficiaries linked to the provided
    customer for payout operations.

    This endpoint provides comprehensive information about beneficiaries registered
    under a particular customer, enabling merchants to view and manage beneficiary
    relationships for payout disbursements.

    The API endpoint is:
        https://portal.juspay.in/api/payout/batch/dashboard/v2/benedetails/{customerId}

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json
        - authorization : login token
        - x-token-type: Euler

    Args:
        payload (dict): A dictionary with the following required key:
            - customerId: Unique identifier for the customer whose beneficiaries are to be retrieved.

    Returns:
        dict: The parsed JSON response containing a list of beneficiaries associated
              with the customer, including account details and verification status.

    Raises:
        ValueError: If required 'customerId' parameter is missing.
        Exception: If the API call fails.
    """

    customerId = payload.pop("customerId", None)
    if not customerId:
        raise ValueError("The payload must include 'customerId'.")

    host = await get_juspay_host_from_api(meta_info=meta_info)
    additional_headers = make_payout_additional_headers(meta_info)
    api_url = f"{host}/api/payout/batch/dashboard/v2/benedetails/{customerId}"

    return await call(api_url, additional_headers=additional_headers, meta_info=meta_info)

async def get_beneficiary_details_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves detailed information for a specific beneficiary identified by customer ID
    and beneficiary ID. This API returns comprehensive beneficiary details including
    account information, verification status, configuration parameters, and operational
    settings for the specified beneficiary.

    This endpoint provides detailed view of a particular beneficiary's information,
    enabling merchants to access specific beneficiary data for payout operations
    and account management purposes.

    The API endpoint is:
        https://portal.juspay.in/api/payout/batch/dashboard/v2/benedetails/{customerId}/{beneId}

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json
        - authorization : login token
        - x-token-type: Euler

    Args:
        payload (dict): A dictionary with the following required keys:
            - customerId: Unique identifier for the customer.
            - beneId: Unique identifier for the beneficiary.

    Returns:
        dict: The parsed JSON response containing detailed beneficiary information
              including account details, verification status, and configuration parameters.

    Raises:
        ValueError: If required 'customerId' or 'beneId' parameters are missing.
        Exception: If the API call fails.
    """

    customerId = payload.pop("customerId", None)
    beneId = payload.pop("beneId", None)
    if not customerId or not beneId:
        raise ValueError("The payload must include 'customerId' and 'beneId'.")

    host = await get_juspay_host_from_api(meta_info=meta_info)
    additional_headers = make_payout_additional_headers(meta_info)
    api_url = f"{host}/api/payout/batch/dashboard/v2/benedetails/{customerId}/{beneId}"
    return await call(api_url, additional_headers=additional_headers, meta_info=meta_info)
