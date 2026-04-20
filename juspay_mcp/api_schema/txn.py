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


class JuspayCardTxnPayload(WithRoutingId):
    order_id: str = Field(..., description="Unique identifier for the order.")
    card_token: str = Field(..., description="A valid card token obtained using /card/list API. If you send this parameter, then card_number, name_on_card, card_exp_year, card_exp_month fields are not required.")
    merchant_id: Optional[str] = Field(None, description="Your merchant ID provided by Juspay. If not provided, will be taken from meta_info.")
    payment_method_type: str = Field(..., description="Type of payment method (e.g., 'CARD', 'NB', 'UPI').")
    payment_method: Optional[str] = Field(None, description="One of VISA/MASTERCARD/MAESTRO/AMEX/RUPAY. This is usually inferred from the card number itself.")
    gateway_id: Optional[str] = Field(None, description="Gateway identifier. If not provided, will be taken from meta_info.")
    card_number: Optional[str] = Field(None, description="A valid credit/debit card number. Not required when using card_token.")
    name_on_card: Optional[str] = Field(None, description="Card holder name. Should contain alphabetical characters only.")
    card_exp_year: Optional[str] = Field(None, description="Represent the expiry year of the card as YY (two digits only). Not required when using card_token.")
    card_exp_month: Optional[str] = Field(None, description="Represent the expiry month of the card as MM (two digits only). Not required when using card_token.")
    card_security_code: Optional[str] = Field(None, description="CVV of the card. Usually three digits. Optional when CVV-less transactions are supported.")
    save_to_locker: Optional[bool] = Field(None, description="This is a boolean variable and accepts true/false. If set to true, then the card will be saved in locker when the transaction is successful. Only applicable for international cards. Defaults to true if not provided.")
    tokenize: Optional[bool] = Field(None, description="This is a boolean variable and accepts true/false. If set to true, then the card will be tokenised when the transaction is successful. Only applicable for domestic cards. Defaults to true if not provided.")
    redirect_after_payment: Optional[bool] = Field(None, description="This is a boolean variable and accepts true/false. We recommend that you set this to true and use the redirection flow. Defaults to true if not provided.")
    format: Optional[str] = Field(None, description="If it is set to json, then the response will be HTTP 200 with a JSON formatted text. Otherwise, the response is HTTP 302 with the Location attribute having the destination URL. Defaults to 'json' if not provided.", enum=["json"])
    offers: Optional[str] = Field(None, description="Array of offer IDs to apply to the transaction (e.g., '[3a8fc1dc-2ace-4f15-8bae-16b376785692]').")

    class Config:
        validate_by_name = True
        extra = "allow"
