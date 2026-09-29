import base64
import os

from juspay_dashboard_mcp.api.utils import post, get_juspay_credentials
from juspay_dashboard_mcp.config import JUSPAY_WEB_LOGIN_TOKEN


async def query_rag_tool(payload: dict, meta_info: dict = None) -> dict:
    """
    Queries the RAG Tool API with the given payload and returns the response.

    The API endpoint is:
        https://genius.juspay.in/api/v3/rag/query

    Auth is `Authorization: Basic base64(token)` — confirmed correct against
    a live genius instance. The original bug was the token source: it only
    checked meta_info/env, skipping the request-scoped credential context
    every other dashboard tool checks first (`get_juspay_credentials()`),
    so it could pick up a stale/wrong token in some auth flows.

    Args:
        payload (dict): The request payload containing the query and similarity_top_k.
        meta_info (dict, optional): Additional metadata for the request.

    Returns:
        dict: The parsed JSON response from the RAG Tool API.

    Raises:
        Exception: If the API call fails or if no authentication token is available.
    """
    juspay_creds = get_juspay_credentials()
    token = None
    if juspay_creds:
        token = juspay_creds.get("dashboard_token")
    if not token and meta_info:
        token = meta_info.get("x-web-logintoken")
    if not token:
        token = JUSPAY_WEB_LOGIN_TOKEN or os.environ.get("JUSPAY_WEB_LOGIN_TOKEN")

    if not token:
        raise Exception("Authentication token is required.")

    encoded_token = base64.b64encode(token.encode()).decode()
    auth_header = f"Basic {encoded_token}"

    api_url = "https://genius.juspay.in/api/v3/rag/query"
    return await post(api_url, payload, {"Authorization": auth_header}, meta_info)
