# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from typing import Optional
from pydantic import BaseModel, Field
from juspay_dashboard_mcp.api_schema.headers import WithHeaders


class JuspayListPayoutOrdersPayload(WithHeaders):
    dateFrom: str = Field(
        ...,
        description="Start date/time in ISO 8601 format (e.g., '2025-03-28T14:16:00Z'). Specifies the beginning of the time range for retrieving payout orders.",
    )
    dateTo: str = Field(
        ...,
        description="End date/time in ISO 8601 format (e.g., '2025-03-28T15:16:00Z'). Specifies the end of the time range for retrieving payout orders.",
    )
    limit: Optional[int] = Field(
        100,
        description="Number of payout orders to retrieve. Optional, defaults to 100. Maximum allowed value is 100.",
        ge=1,
        le=100
    )
    offset: Optional[int] = Field(
        0, 
        description="Pagination offset for retrieving payout orders. Optional, defaults to 0. Used to skip a specific number of records for pagination.",
        ge=0
    )


class JuspayGetPayoutOrderDetailsPayload(WithHeaders):
    order_id: str = Field(
        ..., 
        description="Unique payout order ID for which details are to be fetched. Can also be a fulfillment ID or transaction ID, which will be automatically processed to extract the base order ID if the initial request fails."
    )
