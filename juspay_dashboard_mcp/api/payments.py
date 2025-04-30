import logging
from juspay_dashboard_mcp.api.utils import post, get_juspay_host_from_api

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def list_payment_links_v1_juspay(payload: dict) -> dict:
    """
    Calls the Juspay Portal API to retrieve a list of payment links within a specified time range.

    Args:
        payload (dict): Should contain 'qFilters' and 'filters' as required by the API.
            - qFilters: Query filters for the API (dict)
            - filters: Additional filters for the API (dict)
            - offset: Pagination offset (optional, default 0)

    Returns:
        dict: The parsed JSON response from the List Payment Links API.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api()
    api_url = f"{host}/api/ec/v1/paymentLinks/list"

    # Build request_data directly from payload, only including expected keys
    request_data = {}
    if "qFilters" in payload:
        request_data["qFilters"] = payload["qFilters"]
    if "filters" in payload:
        request_data["filters"] = payload["filters"]
    if "offset" in payload:
        request_data["offset"] = payload["offset"]

    return await post(api_url, request_data)
