import logging
import os
import dotenv

dotenv.load_dotenv()

from juspay_dashboard_mcp.api.utils import post, get_juspay_host_from_api

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def fetch_feature_details_juspay(payload: dict) -> dict:
    """
    Provides comprehensive information for a specific feature ID, including overview, description, FAQs, usage by other merchants, supported PGs/PMTs/platforms, and related features.

    Args:
        payload (dict): Must contain 'merchant_id' and 'feature_id'. 'client_id' is optional.

    Returns:
        dict: The parsed JSON response from the Juspay Fetch Feature Details API.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api()

    api_url = f"{host}stein/feature-description/fetch"
    return await post(
        api_url,
        payload,
        {
            "juspay_token": os.getenv("LOGIN_TOKEN"),
            "original_token": os.getenv("LOGIN_TOKEN"),
        },
    )


async def fetch_feature_list_juspay(payload: dict) -> dict:
    """
    Calls the Juspay Marketplace API to retrieve a list of available features.

    Args:
        payload (dict): A dictionary containing:
            - merchantId: Merchant ID to retrieve marketplace features for
            - clientId: Optional client ID (nullable)

    Returns:
        dict: The parsed JSON response containing marketplace features.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api()
    api_url = f"{host}stein/feature-list/fetch"

    return await post(
        api_url,
        payload,
        {
            "juspay_token": os.getenv("LOGIN_TOKEN"),
            "original_token": os.getenv("LOGIN_TOKEN"),
        },
    )
