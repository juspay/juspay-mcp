# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from pydantic import Field
from typing import List, Optional
from juspay_mcp.api_schema.routing import WithRoutingId

class JuspaySavedPaymentMethodsPayload(WithRoutingId):
    customer_id: Optional[str] = Field(None, description="Unique identifier of the customer whose payment methods to retrieve.")
    payment_method: Optional[List[str]] = Field(["UPI_COLLECT"], description="List of payment method types to retrieve.", enum=["UPI_COLLECT"])


class JuspayUpiCollectPayload(WithRoutingId):
    order_id: str = Field(..., description="Unique identifier for the order.")
    merchant_id: str = Field(..., description="Merchant identifier.")
    upi_vpa: str = Field(..., description="UPI Virtual Payment Address of the customer.")
    redirect_after_payment: bool = Field(True, description="Whether to redirect after payment.")


class JuspayVerifyVpaPayload(WithRoutingId):
    vpa: str = Field(..., description="UPI Virtual Payment Address to verify.")
    merchant_id: str = Field(..., description="Merchant identifier.")


class JuspayUpiIntentPayload(WithRoutingId):
    order_id: str = Field(..., description="Unique identifier for the order.")
    merchant_id: str = Field(..., description="Merchant identifier.")
    upi_app: Optional[str] = Field(None, description="Specific UPI app to open (e.g., 'com.phonepe.app').")
    sdk_params: bool = Field(True, description="Whether to include SDK parameters in the response.")
    redirect_after_payment: bool = Field(True, description="Whether to redirect after payment.")
