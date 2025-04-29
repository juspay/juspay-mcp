import httpx
from juspay_mcp.config import ENDPOINTS
from juspay_mcp.api.utils import call, post

async def list_wallets(payload: dict) -> dict:
    """
    Retrieves the list of wallets associated with a customer.

    This function sends an HTTP GET request to the Juspay List Wallets API endpoint.

    Args:
        payload (dict): Must include:
            - customer_id (str): Unique identifier of the customer.
        May include:
            - routing_id (str): Optional custom routing ID.

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

    return await call(api_url, routing_id)
