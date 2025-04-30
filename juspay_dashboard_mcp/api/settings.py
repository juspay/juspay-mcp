import logging

from juspay_dashboard_mcp.api.utils import post, get_juspay_host_from_api

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def get_conflict_settings_juspay(payload: dict) -> dict:
    """
    Retrieves conflict settings configuration.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/conflict

    The call uses an empty request body.

    Headers include:
        - x-tenant-id from payload
        - content-type: application/json

    Args:
        payload (dict): No specific parameters required.

    Returns:
        dict: The parsed JSON response containing conflict settings.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api()
    api_url = f"{host}/api/ec/v1/conflict"
    return await post(api_url, {})

async def get_general_settings_juspay(payload: dict) -> dict:
    """
    Retrieves general configuration settings.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/general

    The call uses an empty request body.

    Headers include:
        - x-tenant-id from payload     
        - content-type: application/json

    Args:
        payload (dict): No specific parameters required.

    Returns:
        dict: The parsed JSON response containing general merchant settings.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api()
    api_url = f"{host}/api/ec/v1/general"
    return await post(api_url, {})

async def get_mandate_settings_juspay(payload: dict) -> dict:
    """
    Retrieves mandate-related settings.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/mandate

    The call can include optional JSON data:
        - merchantId: Optional merchant ID

    Headers include:
        - x-tenant-id from payload       
        - content-type: application/json

    Args:
        payload (dict): May include:
            - merchantId: Optional merchant ID to retrieve mandate settings for.

    Returns:
        dict: The parsed JSON response containing mandate settings.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api()
    api_url = f"{host}/api/ec/v1/mandate"
    
    request_data = {}
    if payload.get("merchantId"):
        request_data["merchantId"] = payload["merchantId"]
        
    return await post(api_url, request_data)

async def get_priority_logic_settings_juspay(payload: dict) -> dict:
    """
    Fetches a list of all configured priority logic rules, including their current 
    status and full logic definition.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/priorityLogic

    The call uses an empty request body.

    Headers include:
        - x-tenant-id from payload    
        - content-type: application/json

    Args:
        payload (dict): No specific parameters required.

    Returns:
        dict: The parsed JSON response from the Juspay Priority Logic Settings API.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api()
    api_url = f"{host}/api/ec/v1/priorityLogic"
    return await post(api_url, {})

async def get_routing_settings_juspay(payload: dict) -> dict:
    """
    Provides details of success rate–based routing thresholds defined by the merchant, 
    including enablement status and downtime-based switching thresholds.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/routing

    The call uses an empty request body.

    Headers include:
        - x-tenant-id from payload        
        - content-type: application/json

    Args:
        payload (dict): No specific parameters required.

    Returns:
        dict: The parsed JSON response from the Juspay Routing Settings API.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api()
    api_url = f"{host}/api/ec/v1/routing"
    return await post(api_url, {})

async def get_webhook_settings_juspay(payload: dict) -> dict:
    """
    Retrieves webhook configuration settings.

    The API endpoint is:
        https://portal.juspay.in/api/ec/v1/webhook

    The call uses an empty request body.

    Headers include:
        - x-tenant-id from payload     
        - content-type: application/json

    Args:
        payload (dict): No specific parameters required.

    Returns:
        dict: The parsed JSON response containing webhook settings.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api()
    api_url = f"{host}/api/ec/v1/webhook"
    return await post(api_url, {})
