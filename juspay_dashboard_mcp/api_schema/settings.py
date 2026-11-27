# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from typing import Optional
from pydantic import BaseModel, Field

from juspay_dashboard_mcp.api_schema.headers import WithHeaders

class ConflictSettingsPayload(WithHeaders):
    """Schema for conflict settings API."""
    pass  # No specific fields required beyond the common headers

class GeneralSettingsPayload(WithHeaders):
    """Schema for general settings API."""
    pass  # No specific fields required beyond the common headers

class MandateSettingsPayload(WithHeaders):
    merchantId: Optional[str] = Field(
        None, 
        description="Optional merchant ID to retrieve mandate settings for."
    )

class PriorityLogicSettingsPayload(WithHeaders):
    """Schema for priority logic settings API."""
    limit: Optional[int] = Field(
        5, description="Maximum number of priority logics to return, most recently updated first. Defaults to 5.", ge=1, le=50
    )
    offset: Optional[int] = Field(
        0, description="Number of priority logics to skip before returning results. Defaults to 0.", ge=0
    )
    include_gateways: Optional[bool] = Field(
        False,
        description="Include the merchant's full configured-gateway catalog in the response. "
        "Omitted by default since it's unrelated to which priority logics are returned and can be "
        "large — call list_configured_gateway directly instead unless you specifically need it here.",
    )

class RoutingSettingsPayload(WithHeaders):
    """Schema for routing settings API."""
    pass  # No specific fields required beyond the common headers

class WebhookSettingsPayload(WithHeaders):
    """Schema for webhook settings API."""
    pass  # No specific fields required beyond the common headers
