# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from juspay_dashboard_mcp.api.utils import call, get_juspay_host_from_api, make_payout_additional_headers

async def get_payout_configs_juspay(meta_info: dict = None) -> dict:
    """
    Retrieves the payout system configuration settings for the merchant's account.
    This API returns various configuration parameters that control payout processing
    behavior, including operational settings, feature flags, processing limits,
    and other configurable aspects of the payout system.

    This endpoint provides access to merchant-specific payout configurations that
    determine how payout operations are processed, validated, and executed within
    the merchant's environment.

    The API endpoint is:
        https://portal.juspay.in/api/payout/batch/dashboard/v1/config

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json
        - authorization : login token
        - x-token-type: Euler

    Returns:
        dict: The parsed JSON response containing payout system configuration settings
              including operational parameters, feature flags, and processing limits.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    additional_headers = make_payout_additional_headers(meta_info)
    api_url = f"{host}/api/payout/batch/dashboard/v1/config"
    return await call(api_url, additional_headers=additional_headers, meta_info=meta_info)

async def get_payout_ecnryption_or_ssl_keys_juspay(meta_info: dict = None) -> dict:
    """
    Retrieves encryption and SSL keys used for secure payout operations. This API
    returns cryptographic keys and certificates that are used for data encryption,
    secure communication, and digital signatures in payout processing workflows.

    This endpoint provides access to security credentials including public keys,
    SSL certificates, and other cryptographic materials necessary for secure
    payout transaction processing and communication with gateway providers.

    The API endpoint is:
        https://portal.juspay.in/api/payout/batch/dashboard/v1/keys

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json
        - authorization : login token
        - x-token-type: Euler

    Returns:
        dict: The parsed JSON response containing encryption keys, SSL certificates,
              and other cryptographic materials used for secure payout operations.

    Raises:
        Exception: If the API call fails.
    """

    host = await get_juspay_host_from_api(meta_info=meta_info)
    additional_headers = make_payout_additional_headers(meta_info)
    api_url = f"{host}/api/payout/batch/dashboard/v1/keys"

    return await call(api_url, additional_headers=additional_headers, meta_info=meta_info)

async def get_payout_outages_juspay(meta_info: dict = None) -> dict:
    """
    Retrieves a list of current payout system outages and service disruptions.
    This API returns information about ongoing outages, maintenance windows, and
    service interruptions affecting payout operations across different gateways
    and payment methods.

    This endpoint provides real-time visibility into payout system health and
    availability, helping merchants understand service disruptions that may
    impact payout processing and disbursement operations.

    The API endpoint is:
        https://portal.juspay.in/api/payout/batch/dashboard/v1/listOutage

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json
        - authorization : login token
        - x-token-type: Euler

    Returns:
        dict: The parsed JSON response containing current outages and service disruptions
              affecting payout operations, including affected services and estimated resolution times.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    additional_headers = make_payout_additional_headers(meta_info)
    api_url = f"{host}/api/payout/batch/dashboard/v1/listOutage"
    return await call(api_url, additional_headers=additional_headers, meta_info=meta_info)