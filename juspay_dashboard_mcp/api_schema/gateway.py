from typing import Optional
from pydantic import BaseModel, Field

from juspay_dashboard_mcp.api_schema.headers import WithHeaders

class JuspayListConfiguredGatewaysPayload(WithHeaders):
    merchant_id: str = Field(
        ...,
        description="Merchant identifier for which to list configured payment gateways."
    )

class JuspayGetGatewaySchemePayload(WithHeaders):
    gateway: str = Field(
        ...,
        description="Gateway code (e.g., 'TATA_PA') for which to fetch detailed configuration information."
    )
    merchant_id: Optional[str] = Field(
        None,
        description="Merchant identifier (optional, but recommended for context)."
    )

class JuspayGetGatewayDetailsPayload(WithHeaders):
    mga_id: int = Field(
        ...,
        description="The MGA ID of the gateway (from list_configured_gateways)."
    )
    merchant_id: str = Field(
        ...,
        description="Merchant identifier for which to get gateway details."
    )

class JuspayListGatewaySchemePayload(WithHeaders):
    """
    No input required. Returns a list of all available payment gateways that can be configured on PGCC.
    """
    pass


class JuspayGetMerchantGatewaysPmDetailsPayload(WithHeaders):
    """
    Fetches all gateways and their supported payment methods for the merchant.
    No input required.
    """
    pass
