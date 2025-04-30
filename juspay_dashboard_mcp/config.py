import os
import base64
import dotenv

dotenv.load_dotenv()

JUSPAY_ENV = os.getenv("JUSPAY_ENV", "sandbox").lower() 
JUSPAY_WEB_LOGIN_TOKEN = os.getenv("JUSPAY_WEB_LOGIN_TOKEN")

if JUSPAY_ENV == "production":
    JUSPAY_BASE_URL = os.getenv("JUSPAY_PROD_BASE_URL", "https://portal.juspay.in")
    print("Using Juspay Production Environment")
else:
    JUSPAY_BASE_URL = os.getenv("JUSPAY_SANDBOX_BASE_URL", "https://sandbox.portal.juspay.in")
    print("Using Juspay Sandbox Environment")

def verify_env_vars():
    """ 
    Verifies that all required environment variables are set.
    """

    if not JUSPAY_WEB_LOGIN_TOKEN:
        raise ValueError("JUSPAY_WEB_LOGIN_TOKEN environment variable must be set.")
    
def get_base64_auth():
    """Returns the base64 encoded auth string."""
    pass
    
def get_common_headers(payload: dict):
    """
    Returns common headers used by all API calls.
    Uses the provided routing_id, or defaults to JUSPAY_MERCHANT_ID if None.
    """
    verify_env_vars()

    default_headers = {
         "Content-Type": "application/json",
        "accept": "*/*",
        "x-request-id": f"mcp-tool-{os.urandom(6).hex()}",
        "x-web-logintoken": f"{JUSPAY_WEB_LOGIN_TOKEN}",
    }

    if payload.get("tenant_id"):
        default_headers["x-tenant-id"] = payload.pop("tenant_id")

    if payload.get("cookie"):
        default_headers["cookie"] = payload.pop("cookie")
        
    return default_headers
