# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from typing import List, Optional, Union
from pydantic import BaseModel, Field
from juspay_mcp.api_schema.routing import WithRoutingId

class OrderInfo(BaseModel):
    order_id: str = Field(..., description="Unique identifier for the order.")
    amount: Union[str, int, float] = Field(..., description="Order amount as a string, int, or float (e.g., '12000', 12000, 12000.50).")
    currency: str = Field(..., description="Currency code (e.g., 'INR').")


class PaymentMethodInfoItem(BaseModel):
    payment_method_type: Optional[str] = Field(None, description="Type of payment method (e.g., 'CARD', 'UPI').")
    payment_method_reference: Optional[str] = Field(None, description="Reference identifier for the payment method.")
    payment_method: Optional[str] = Field(None, description="Specific payment method (e.g., 'VISA', 'UPI').")
    card_number: Optional[str] = Field(None, description="Card number (for CARD payment method).")
    bank_code: Optional[str] = Field(None, description="Bank code (for CARD payment method).")
    card_type: Optional[str] = Field(None, description="Type of card (e.g., 'CREDIT', 'DEBIT').")
    card_token: Optional[str] = Field(None, description="Card token for saved cards.")
    upi_vpa: Optional[str] = Field(None, description="UPI Virtual Payment Address (for UPI payment method).")
    upi_app: Optional[str] = Field(None, description="UPI app package name (for UPI_PAY).")
    txn_type: Optional[str] = Field(None, description="Transaction type (e.g., 'UPI_COLLECT', 'UPI_PAY').")
    is_emi: Optional[str] = Field(None, description="Whether this is an EMI payment.")
    emi_bank: Optional[str] = Field(None, description="Bank offering EMI.")
    emi_tenure: Optional[str] = Field(None, description="EMI tenure in months.")


class CustomerInfo(BaseModel):
    id: Optional[str] = Field(None, description="Customer identifier.")
    email: Optional[str] = Field(None, description="Customer email address.")
    mobile: Optional[str] = Field(None, description="Customer mobile number.")


class JuspayListOffersPayload(WithRoutingId):
    order: OrderInfo
    payment_method_info: List[PaymentMethodInfoItem]
    customer: Optional[CustomerInfo] = Field(None, description="Customer details (optional).")
    offer_code: Optional[str] = Field(None, description="Coupon or offer code to apply.")
    routing_id: Optional[str] = Field(
        None,
        description=(
            "Optional custom routing ID for the API request. "
            "We recommend passing the customer_id as the x-routing-id. "
            "If the customer is checking out as a guest, you can pass an alternative ID "
            "that helps track the payment session lifecycle (e.g., Order ID or Cart ID)."
        )
    )


class JuspayOfferOrderStatusPayload(WithRoutingId):
    order_id: str = Field(..., description="Unique identifier for the order to check status with offer details.")
    routing_id: Optional[str] = Field(
        None,
        description=(
            "Optional custom routing ID for the API request. "
            "We recommend passing the customer_id as the x-routing-id. "
            "If the customer is checking out as a guest, you can pass an alternative ID "
            "that helps track the payment session lifecycle (e.g., Order ID or Cart ID)."
        )
    )
