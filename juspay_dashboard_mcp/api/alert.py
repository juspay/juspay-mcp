import logging
from juspay_dashboard_mcp.api.utils import post, get_juspay_host_from_api,call

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def alert_details_juspay(payload: dict) -> dict:
    """
    Provides detailed information for a specific alert ID, including source, monitored metrics, and applied filters.

    Args:
        payload (dict): Must contain 'task_uid' and 'user_name'.

    Returns:
        dict: The parsed JSON response from the Juspay Alert Details API.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api()
    api_url = f"{host}api/monitoring/task?task_uid={payload['task_uid']}&user_name={payload['user_name']}"
    return await call(api_url, {})

async def list_alerts_juspay(payload: dict) -> dict:
    """
    Calls the Juspay Monitoring API to retrieve a list of configured alerts.

    Args:
        payload (dict): A dictionary containing:
            - merchantId: Optional merchant ID to retrieve alerts for
            - taskType: Optional task type filter, typically 'alert'

    Returns:
        dict: The parsed JSON response containing alert configurations.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api()
    api_url = f"{host}api/monitoring/task/list"
    request_data = {
        "task_type": payload.get("taskType", "alert")
    }
    if payload.get("merchantId"):
        request_data["merchantId"] = payload["merchantId"]
    return await post(api_url, request_data)