# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from typing import Optional
from pydantic import BaseModel, Field

from juspay_dashboard_mcp.api_schema.headers import WithHeaders

class JuspayListConfiguredGatewaysPayload(WithHeaders):
    merchantId: Optional[str] = Field(
        default=None,
        description="Merchant identifier for which to list configured payment gateways."
    )

class JuspayGetGatewaySchemePayload(WithHeaders):
    gateway: str = Field(
        ...,
        description="Gateway code (e.g., 'TATA_PA') for which to fetch detailed configuration information."
    )
    merchantId: Optional[str] = Field(
        None,
        description="Merchant identifier (optional, but recommended for context)."
    )

class JuspayGetGatewayDetailsPayload(WithHeaders):
    mga_id: int = Field(
        ...,
        description="The MGA ID of the gateway (from list_configured_gateways)."
    )
    merchantId: str = Field(
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
