# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from pydantic import BaseModel, Field
from typing import Optional
from juspay_dashboard_mcp.api_schema.headers import WithHeaders


class JuspayListOutagesPayload(WithHeaders):
    """Returns a list of outages within a specified time range, optionally filtered by merchant ID."""
    
    startTime: str = Field(
        ...,
        description="Start time in ISO format (e.g., '2025-05-22T18:30:00Z')"
    )
    
    endTime: str = Field(
        ...,
        description="End time in ISO format (e.g., '2025-05-23T10:30:12Z')"
    )
    
    merchantId: Optional[str] = Field(
        None,
        description="Merchant ID to filter outages (optional). If not provided, returns all outages including global ones."
    )