# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from juspay_dashboard_mcp.api_schema.headers import WithHeaders

class JuspayListUnifiedAlertsPayload(WithHeaders):
    """Payload for listing unified alerts with flexible filtering options."""
    
    merchantId: str = Field(
        ...,
        description="Merchant ID to filter alerts (required)."
    )
    
    startTime: str = Field(
        None,
        description="Start time in format 'YYYY-MM-DD HH:MM:SS' (e.g., '2025-10-05 13:45:00') (required)."
    )
    
    endTime: str = Field(
        None,
        description="End time in format 'YYYY-MM-DD HH:MM:SS' (e.g., '2025-10-06 14:45:00') (required)."
    )
    
    name: Optional[str] = Field(
        None,
        description="Optional alert name/type to filter by (e.g., 'Api Availability Drop')."
    )
    
    dimensions: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional dictionary for filtering alerts by specific dimensions (e.g., {'api': 'TRANSACTION', 'merchant_id': 'specific_merchant'})."
    )
