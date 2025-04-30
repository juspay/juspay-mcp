from typing import Optional
from pydantic import BaseModel, Field

from juspay_dashboard_mcp.api_schema.headers import WithHeaders

class JuspayGetOfferDetailsPayload(WithHeaders):
    offerId: str = Field(
        ...,
        description="The unique identifier of the offer to retrieve details for."
    )
    merchantId: str = Field(
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