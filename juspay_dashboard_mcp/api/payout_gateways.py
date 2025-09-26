# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from juspay_dashboard_mcp.config import make_auth_header
from juspay_dashboard_mcp.api.utils import get, get_juspay_host_from_api

async def list_configured__payout_gateways_juspay(meta_info: dict = None) -> dict:
    """
    Retrieves a list of all payout gateway credentials configured for a merchant's 
    payout operations. This API returns gateway configuration details including 
    credential references, setup status, and operational parameters for batch 
    payout processing.

    This is specifically for payout gateways (not payment gateways) and provides
    information about which payout providers are configured and available for 
    disbursement operations.

    The API endpoint is:
        https://portal.juspay.in/api/payout/batch/dashboard/v1/gatewaycredential

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json
        - authorization : login token
        - x-token-type: Euler

    Returns:
        dict: The parsed JSON response containing configured payout gateway credentials,
              including gateway reference IDs, configuration status, and operational details.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    auth_header = make_auth_header(meta_info)
    api_url = f"{host}/api/payout/batch/dashboard/v1/gatewaycredential"
    return await get(api_url, additional_headers=auth_header, meta_info=meta_info)

async def get_payout_gateways_juspay(meta_info: dict = None) -> dict:
    """
    Retrieves a list of all available payout gateway types.
    This API provides information about gateway types that can be configured
    for payout operations.

    This endpoint returns the available gateway schemas without requiring specific
    gateway selection, providing a comprehensive overview of all payout gateway
    options available for configuration.

    The API endpoint is:
        https://portal.juspay.in/api/payout/batch/dashboard/v1/gateway

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json
        - authorization : login token
        - x-token-type: Euler

    Returns:
        dict: The parsed JSON response containing available payout gateway types
              and their configuration schemas, including supported fields and requirements.

    Raises:
        Exception: If the API call fails.
    """

    host = await get_juspay_host_from_api(meta_info=meta_info)
    auth_header = make_auth_header(meta_info)
    api_url = f"{host}/api/payout/batch/dashboard/v1/gateway"

    return await get(api_url, additional_headers=auth_header, meta_info=meta_info)

async def get_payout_gateway_details_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Retrieves detailed configuration information for a specific payout gateway
    credential identified by gateway type and rail. This API provides comprehensive
    details about a particular gateway setup including configuration parameters,
    status, and operational settings.

    This endpoint requires both gateway identifier and rail information to fetch
    the specific gateway credential details configured for the merchant's payout
    operations.

    The API endpoint is:
        https://portal.juspay.in/api/payout/batch/dashboard/v1/gatewaycredential/{gateway}/{rail}

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json
        - authorization : login token
        - x-token-type: Euler

    Args:
        payload (dict): A dictionary with the following required keys:
            - gateway: Gateway identifier/type (e.g., "RAZORPAY", "PAYU").
            - rail: Rail identifier for the gateway configuration.

    Returns:
        dict: The parsed JSON response containing detailed gateway credential information
              including configuration parameters, status, and operational settings.

    Raises:
        ValueError: If required 'gateway' or 'rail' parameters are missing.
        Exception: If the API call fails.
    """

    gateway = payload.pop("gateway", None)
    rail = payload.pop("rail", None)

    if not gateway or not rail:
        raise ValueError("The payload must include 'gateway' and 'rail'.")

    host = await get_juspay_host_from_api(meta_info=meta_info)
    auth_header = make_auth_header(meta_info)
    api_url = f"{host}/api/payout/batch/dashboard/v1/gatewaycredential/{gateway}/{rail}"

    return await get(api_url, payload, additional_headers=auth_header, meta_info=meta_info)

async def get_active_payout_gateways_juspay(meta_info: dict = None) -> dict:
    """
    Retrieves a list of active payout methods available for the merchant based on
    priority logic configuration. This API returns currently enabled payout methods
    and their operational status, helping determine which payout options are
    actively available for processing disbursements.

    This endpoint provides real-time information about which payout methods are
    currently active and can be used for processing payout transactions based on
    the merchant's priority logic settings.

    The API endpoint is:
        https://portal.juspay.in/api/payout/dashboard/v1/prioritylogic/activemethods

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json
        - authorization : login token
        - x-token-type: Euler

    Returns:
        dict: The parsed JSON response containing active payout methods and their
              operational status based on priority logic configuration.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    auth_header = make_auth_header(meta_info)
    api_url = f"{host}/api/payout/dashboard/v1/prioritylogic/activemethods"
    return await get(api_url, additional_headers=auth_header, meta_info=meta_info)

async def get_payout_priority_logics_juspay(meta_info: dict = None) -> dict:
    """
    Retrieves the priority logic configuration for payout routing and gateway
    selection. This API returns the configured rules and priorities that determine
    how payout transactions are routed across different gateways and payment methods
    based on various criteria and conditions.

    This endpoint provides information about the merchant's payout routing strategy,
    including priority rules, fallback mechanisms, and gateway selection logic
    configured for optimal payout processing.

    The API endpoint is:
        https://portal.juspay.in/api/payout/batch/dashboard/v1/prioritylogic

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json
        - authorization : login token
        - x-token-type: Euler

    Returns:
        dict: The parsed JSON response containing priority logic configuration
              including routing rules, gateway priorities, and selection criteria.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    auth_header = make_auth_header(meta_info)
    api_url = f"{host}/api/payout/batch/dashboard/v1/prioritylogic"
    return await get(api_url, additional_headers=auth_header, meta_info=meta_info)

async def get_payout_weblabs_juspay(meta_info: dict = None) -> dict:
    """
    Retrieves the WebLab configuration settings for payout operations. This API
    returns A/B testing configurations, feature flags, and experimental settings
    that control various aspects of the payout processing behavior and user
    experience within the payout system.

    This endpoint provides access to dynamic configuration parameters that can be
    used to enable/disable features, control behavior variations, and manage
    experimental rollouts for payout-related functionality.

    The API endpoint is:
        https://portal.juspay.in/api/payout/batch/dashboard/v1/weblabConfig

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json
        - authorization : login token
        - x-token-type: Euler

    Returns:
        dict: The parsed JSON response containing WebLab configuration settings
              including feature flags, A/B test parameters, and experimental configurations.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    auth_header = make_auth_header(meta_info)
    api_url = f"{host}/api/payout/batch/dashboard/v1/weblabConfig"
    return await get(api_url, additional_headers=auth_header, meta_info=meta_info)

async def get_payout_balance_juspay(isForce: str = "false", meta_info: dict = None) -> dict:
    """
    Retrieves the current balance information from all configured payout gateways.
    This API returns real-time or cached balance data for each gateway, providing
    visibility into available funds across different payout providers configured
    for the merchant's disbursement operations.

    This endpoint can force refresh the balance data from gateways when the force
    parameter is set to true, ensuring the most up-to-date balance information
    is retrieved directly from the gateway providers.

    The API endpoint is:
        https://portal.juspay.in/api/payout/batch/dashboard/v1/getways/balance?force={isForce}

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json
        - authorization : login token
        - x-token-type: Euler

    Args:
        isForce (str): Force refresh balance from gateways. Defaults to "false".
                      Set to "true" to fetch real-time balance data.

    Returns:
        dict: The parsed JSON response containing balance information from configured
              payout gateways, including available funds and account details.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    auth_header = make_auth_header(meta_info)
    api_url = f"{host}/api/payout/batch/dashboard/v1/getways/balance?force={isForce}"
    return await get(api_url, additional_headers=auth_header, meta_info=meta_info)
