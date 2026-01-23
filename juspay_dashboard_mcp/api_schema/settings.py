# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from typing import Optional
from pydantic import BaseModel, Field

from juspay_dashboard_mcp.api_schema.headers import WithHeaders

class JuspayConflictSettingsPayload(WithHeaders):
    """Schema for conflict settings API."""
    merchantId: Optional[str] = Field(
        None, 
        description="Merchant ID for which to retrieve conflict settings (admin only, optional)."
    )

class JuspayGeneralSettingsPayload(WithHeaders):
    """Schema for general settings API."""
    merchantId: Optional[str] = Field(
        None, 
        description="Merchant ID for which to retrieve general settings (admin only, optional)."
    )

class JuspayMandateSettingsPayload(WithHeaders):
    merchantId: Optional[str] = Field(
        None, 
        description="Optional merchant ID to retrieve mandate settings for."
    )

class JuspayPriorityLogicSettingsPayload(WithHeaders):
    """Schema for priority logic settings API."""
    merchantId: Optional[str] = Field(
        None, 
        description="Merchant ID for which to retrieve priority logic settings (admin only, optional)."
    )

class JuspayRoutingSettingsPayload(WithHeaders):
    """Schema for routing settings API."""
    merchantId: Optional[str] = Field(
        None, 
        description="Merchant ID for which to retrieve routing settings (admin only, optional)."
    )

class JuspayWebhookSettingsPayload(WithHeaders):
    """Schema for webhook settings API."""
    merchantId: Optional[str] = Field(
        None, 
        description="Merchant ID for which to retrieve webhook settings (admin only, optional)."
    )
