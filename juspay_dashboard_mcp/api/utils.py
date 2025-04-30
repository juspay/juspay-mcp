import httpx
from juspay_dashboard_mcp.config import get_common_headers

async def call(api_url: str, additional_headers: dict = None) -> dict:
    headers = get_common_headers({})
    
    if additional_headers:
        headers.update(additional_headers)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print(f"Calling Juspay API at: {api_url}")
            response = await client.get(api_url, headers=headers)
            print(response)
            response.raise_for_status()
            response_data = response.json()
            print(f"Get API Response Data: {response_data}")
            return response_data
        except httpx.HTTPStatusError as e:
            error_content = e.response.text if e.response else "Unknown error"
            print(f"HTTP error: {e.response.status_code if e.response else 'No response'} - {error_content}")
            raise Exception(f"Juspay API HTTPError ({e.response.status_code if e.response else 'Unknown status'}): {error_content}") from e
        except Exception as e:
            print(f"Error during Juspay API call: {e}")
            raise Exception(f"Failed to call Juspay API: {e}") from e

async def post(api_url: str, payload: dict,additional_headers: dict = None) -> dict:
    headers = get_common_headers(payload) 

    if additional_headers:
        headers.update(additional_headers)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print(f"Calling Juspay API at: {api_url} with body: {payload} and headers: {headers}")
            response = await client.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()
            # print(f"API Response Data: {response_data}")
            return response_data
        except httpx.HTTPStatusError as e:
            error_content = e.response.text if e.response else "Unknown error"
            print(f"HTTP error: {e.response.status_code if e.response else 'No response'} - {error_content}")
            raise Exception(f"Juspay API HTTPError ({e.response.status_code if e.response else 'Unknown status'}): {error_content}") from e
        except Exception as e:
            print(f"Error during Juspay API call: {e}")
            raise Exception(f"Failed to call Juspay API: {e}") from e
        

async def get_juspay_host_from_api(token: str = None, headers: dict = None) -> str:
    """
    Returns the appropriate Juspay host URL based on the environment.
    
    Note: Previously this validated the token, but now uses JUSPAY_WEB_LOGIN_TOKEN 
    environment variable directly. The token parameter is kept for backward compatibility.

    Returns:
        str: The Juspay host URL.
    """
    return "https://portal.juspay.in/"
