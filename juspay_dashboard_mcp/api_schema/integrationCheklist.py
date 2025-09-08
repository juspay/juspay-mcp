# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from typing import Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime
from juspay_dashboard_mcp.api_schema.headers import WithHeaders


class JuspayIntegrationMonitoringPayload(WithHeaders):
    platform: Literal["Backend", "Web", "Android", "IOS"] = Field(
        ...,
        description="Platform type. Use 'Backend' for agnostic API, or 'Web'/'Android'/'IOS' for nonagnostic API."
    )
    product_integrated: Literal["Payment Page Signature", "Payment Page Session", "EC + SDK", "EC Only"] = Field(
        ...,
        description="Product integration type ('Payment Page Signature', 'EC + SDK', 'Payment Page Session', 'EC Only')"
    )
    merchant_id: str = Field(
        ...,
        description="Merchant identifier (e.g., 'A23Games', '1mgtech')"
    )
    start_time: str = Field(
        ...,
        description="Start time in ISO format: YYYY-MM-DDTHH:MM:SSZ (e.g., '2025-08-03T00:00:00Z')"
    )
    end_time: str = Field(
        ...,
        description="End time in ISO format: YYYY-MM-DDTHH:MM:SSZ (e.g., '2025-09-01T12:50:00Z')"
    )
    
    @validator('start_time', 'end_time')
    def validate_datetime_format(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError('Time must be in ISO format: YYYY-MM-DDTHH:MM:SSZ')
