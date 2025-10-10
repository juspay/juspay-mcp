# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from pydantic import Field
from typing import Optional
from juspay_mcp.api_schema.routing import WithRoutingId


class JuspayCreateTxnPayload(WithRoutingId):
    order_order_id: str = Field(..., alias="order.order_id", description="Unique identifier for the order (max 21 alphanumeric chars).")
    order_amount: str = Field(..., alias="order.amount", description="The order amount (e.g., '100.00').")
    order_currency: str = Field(..., alias="order.currency", description="Currency code (e.g., 'INR').")
    order_customer_id: str = Field(..., alias="order.customer_id", description="Merchant's identifier for the customer.")
    order_customer_email: Optional[str] = Field(None, alias="order.customer_email", description="Customer's email address.")
    order_customer_phone: Optional[str] = Field(None, alias="order.customer_phone", description="Customer's phone number.")
    order_return_url: str = Field(..., alias="order.return_url", description="URL to redirect after payment.")
    merchant_id: str = Field(..., description="Your merchant ID provided by Juspay.")
    payment_method_type: str = Field(..., description="Type of payment method.", enum=["CARD", "NB", "WALLET", "UPI", "EMI"])
    payment_method: Optional[str] = Field(None, description="Specific payment method (e.g., 'VISA', 'MASTERCARD').")
    card_number: Optional[str] = Field(None, description="Card number (for CARD payment method).")
    card_exp_month: Optional[str] = Field(None, description="Card expiry month (e.g., '05').")
    card_exp_year: Optional[str] = Field(None, description="Card expiry year (e.g., '25').")
    name_on_card: Optional[str] = Field(None, description="Name as printed on the card.")
    card_security_code: Optional[str] = Field(None, description="Card CVV/security code.")
    save_to_locker: Optional[bool] = Field(None, description="Whether to save card details for future use.")
    redirect_after_payment: Optional[bool] = Field(None, description="Whether to redirect to return URL after payment.")
    format: Optional[str] = Field(None, description="Response format, typically 'json'.", enum=["json"])

    class Config:
        validate_by_name = True
        extra = "allow"


class JuspayCreateMotoTxnPayload(WithRoutingId):
    order_order_id: str = Field(..., alias="order.order_id", description="Unique identifier for the order.")
    order_amount: str = Field(..., alias="order.amount", description="The order amount (e.g., '100.00').")
    order_currency: str = Field(..., alias="order.currency", description="Currency code (e.g., 'INR').")
    order_customer_id: str = Field(..., alias="order.customer_id", description="Merchant's identifier for the customer.")
    order_return_url: str = Field(..., alias="order.return_url", description="URL to redirect after payment.")
    merchant_id: str = Field(..., description="Your merchant ID provided by Juspay.")
    payment_method_type: str = Field(..., description="Type of payment method (only CARD for MOTO).", enum=["CARD"])
    payment_method: Optional[str] = Field(None, description="Specific payment method (e.g., 'VISA', 'MASTERCARD').")
    card_number: Optional[str] = Field(None, description="Card number (masked or full).")
    card_exp_month: Optional[str] = Field(None, description="Card expiry month (e.g., '05').")
    card_exp_year: Optional[str] = Field(None, description="Card expiry year (e.g., '26').")
    redirect_after_payment: Optional[bool] = Field(None, description="Whether to redirect to return URL after payment.")
    format: Optional[str] = Field(None, description="Response format, typically 'json'.", enum=["json"])
    auth_type: str = Field(..., description="Authentication type, must be 'MOTO'.", enum=["MOTO"])
    tavv: Optional[str] = Field(None, description="Transaction Authentication Verification Value for MOTO transactions.")

    class Config:
        validate_by_name = True
        extra = "allow"


class JuspayCashTxnPayload(WithRoutingId):
    order_id: str = Field(..., description="Unique identifier for the order.")
    merchant_id: Optional[str] = Field(None, description="Your merchant ID provided by Juspay. If not provided, will be taken from meta_info.")
    payment_method_type: Optional[str] = Field(None, description="Type of payment method. Will be automatically set to 'CASH'.")
    payment_method: Optional[str] = Field(None, description="Specific payment method. Will be automatically set to 'CASH'.")
    redirect_after_payment: Optional[bool] = Field(True, description="Whether to redirect after payment completion.")
    format: Optional[str] = Field("json", description="Response format.", enum=["json"])

    class Config:
        validate_by_name = True
        extra = "allow"
