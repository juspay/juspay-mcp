import httpx
from juspay_dashboard_mcp.config import get_common_headers

async def call(api_url: str, additional_headers: dict = None) -> dict:
    headers = get_common_headers()
    
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

async def post(api_url: str, payload: dict) -> dict:
    headers = get_common_headers(payload) 

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print(f"Calling Juspay API at: {api_url} with body: {payload}")
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
        

async def get_juspay_host_from_api(token: str, headers: dict = None) -> str:
    """
    Calls the Juspay validate token API, checks the parentEntityContext in the response,
    and returns the appropriate host URL.

    Args:
        token (str): The token to validate.

    Returns:
        str: The selected host URL based on parentEntityContext.
    """
    return "https://portal.juspay.in/"
    # api_url = "https://portal.juspay.in/api/ec/v1/validate/token"
    # request_data = {"token": token}
    # print(f"calling with token {request_data}")
    # # Use default headers if not provided
    # if headers is None:
    #     headers = {
    #         "Content-Type": "application/json",
    #         "Referer": "https://portal.juspay.in/",
    #     }
    # async with httpx.AsyncClient(timeout=30.0) as client:
    #     response = await client.post(api_url, headers=headers, json=request_data)
    #     response.raise_for_status()
    #     resp_json = response.json()
    #     parent_entity_context = resp_json.get("parentEntityContext")
    #     if parent_entity_context and parent_entity_context.upper() == "JUSPAY":
    #         return "https://euler-x.internal.svc.k8s.mum.juspay.net/"
    #     return "https://portal.juspay.in/"
