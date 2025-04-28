import httpx
from juspay_tools.config import ENDPOINTS 
from juspay_tools.api.utils import call, post

async def get_customer_juspay(payload: dict) -> dict:
    """
    Retrieves customer details from Juspay using the customer_id.

    This function sends an HTTP GET request to the Juspay Get Customer endpoint.
    The 'customer_id' from the payload is used both in the URL and as the routing_id header.

    Args:
        payload (dict): Must include:
            - customer_id (str): Unique identifier of the customer.

    Returns:
        dict: Parsed JSON response from the Juspay Get Customer API, typically containing
              customer details.

    Raises:
        ValueError: If 'customer_id' is missing in the payload.
        Exception: If the API call fails (e.g., HTTP error, network issue).
    """
    customer_id = payload.get("customer_id")
    if not customer_id:
        raise ValueError("The payload must include 'customer_id'.")

    api_url = ENDPOINTS["customer"].format(customer_id=customer_id)
    await call(api_url, customer_id)

async def create_customer_juspay(payload: dict) -> dict:
    """
    Creates a new customer in Juspay.
    
    This function sends an HTTP POST request to the Juspay Create Customer endpoint.
    The payload should contain customer details like email, phone, name, etc.
    
    Args:
        payload (dict): Must include:
            - object_reference_id (str): Unique identifier for the customer (e.g., email).
            - mobile_number (str): Customer's mobile number.
            - email_address (str): Customer's email address.
            - first_name (str): Customer's first name.
            - last_name (str): Customer's last name.
            - mobile_country_code (str): Mobile country code without '+' (e.g., '91').
            
    Returns:
        dict: Parsed JSON response containing the newly created customer details.
        
    Raises:
        ValueError: If any required field is missing.
        Exception: If the API call fails.
    """
    required_fields = ["object_reference_id", "mobile_number", "email_address"]
    for field in required_fields:
        if not payload.get(field):
            raise ValueError(f"The payload must include '{field}'.")
    
    routing_id = payload.get("routing_id", payload.get("object_reference_id"))
    
    api_url = ENDPOINTS["create_customer"]
    
    if payload.get("get_client_auth_token"):
        payload["options.get_client_auth_token"] = "true"
    
    await post(api_url, payload, routing_id)

async def update_customer_juspay(payload: dict) -> dict:
    """
    Updates an existing customer in Juspay.
    
    This function sends an HTTP POST request to the Juspay Update Customer endpoint.
    The customer_id is used in the URL path, and other fields are sent in the payload.
    
    Args:
        payload (dict): Must include:
            - customer_id (str): Juspay ID of the customer to update.
        May include:
            - mobile_number (str): Updated mobile number.
            - email_address (str): Updated email address.
            - first_name (str): Updated first name.
            - last_name (str): Updated last name.
            - mobile_country_code (str): Updated mobile country code.
            
    Returns:
        dict: Parsed JSON response containing the updated customer details.
        
    Raises:
        ValueError: If customer_id is missing or no update fields are provided.
        Exception: If the API call fails.
    """
    customer_id = payload.get("customer_id")
    if not customer_id:
        raise ValueError("The payload must include 'customer_id'.")
    
    update_data = {k: v for k, v in payload.items() if k != "customer_id"}
    
    if not update_data:
        raise ValueError("At least one field must be provided for update.")
    
    routing_id = payload.get("routing_id", customer_id)
    
    api_url = ENDPOINTS["update_customer"].format(customer_id=customer_id)
    await post(api_url, update_data, routing_id)