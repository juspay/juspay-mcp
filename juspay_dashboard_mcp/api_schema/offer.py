# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from juspay_dashboard_mcp.api_schema.headers import WithHeaders

class JuspayGetOfferDetailsPayload(WithHeaders):
    offer_ids: List[str] = Field(
        ...,
        description="List of unique identifiers of the offers to retrieve details for."
    )
    merchant_id: str = Field(
        ...,
        description="Merchant ID associated with the offer."
    )
    is_batch: Optional[bool] = Field(
        False,
        description="Whether this is a batch offer (default: False)."
    )

class JuspayListOffersPayload(WithHeaders):
    merchant_id: str = Field(
        ...,
        description="Merchant identifier for which to list offers."
    )
    created_at: Dict[str, str] = Field(
        ...,
        description="Created at filter with 'lte' and 'gte' string timestamps (ISO 8601 format)."
    )
    start_time: str = Field(
        ...,
        description="Start time for filtering offers (ISO format)."
    )
    end_time: str = Field(
        ...,
        description="End time for filtering offers (ISO format)."
    )
    limit: Optional[int] = Field(
        default=None,
        description="Limit for number of offers to fetch."
    )
    sort_offers: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Sorting options for offers."
    )
