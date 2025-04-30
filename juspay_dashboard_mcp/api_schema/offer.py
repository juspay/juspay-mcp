from typing import Optional, List
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
    isBatch: Optional[bool] = Field(
        False,
        description="Whether this is a batch offer (default: False)."
    )

class JuspayListOffersPayload(WithHeaders):
    merchant_id: str = Field(
        ...,
        description="Merchant identifier for which to list offers."
    )
    start_time: str = Field(
        ...,
        description="Start time for filtering offers (ISO format)."
    )
    end_time: str = Field(
        ...,
        description="End time for filtering offers (ISO format)."
    )
