# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from pydantic import Field
from typing import Optional, Literal
from juspay_mcp.api_schema.routing import WithRoutingId


class JuspayOrderStatusPayload(WithRoutingId):
    order_id: str = Field(..., description="Unique identifier for the order to check its status.")
    customer_id: Optional[str] = Field(None, description="Customer identifier for routing purposes.")


class JuspayOrderFulfillmentPayload(WithRoutingId):
    order_id: str = Field(..., description="Unique identifier of the order to update fulfillment status.")
    fulfillment_status: Literal["SUCCESS", "FAILURE", "PENDING"] = Field(
        ..., 
        description="Status of the fulfillment (SUCCESS, FAILURE, PENDING)."
    )
    fulfillment_command: Literal["NO_ACTION", "RELEASE_HOLD", "HOLD"] = Field(
        ..., 
        description="Command for the fulfillment action."
    )
    fulfillment_time: str = Field(
        ..., 
        description="Time of fulfillment in ISO format (e.g., '2024-07-08T16:30:33')."
    )
    fulfillment_id: str = Field(..., description="Unique identifier for this fulfillment action.")
    fulfillment_data: Optional[str] = Field(None, description="Optional metadata for the fulfillment.")


class JuspayCreateOrderPayload(WithRoutingId):
    order_id: Optional[str] = Field(None, description="Unique identifier for the order (max 21 alphanumeric chars). If not provided, will be auto-generated.")
    amount: str = Field(..., description="The order amount (e.g., '100.00').")
    currency: str = Field(..., description="Currency code (e.g., 'INR').")
    customer_id: Optional[str] = Field(None, description="Merchant's identifier for the customer. If not provided, will be taken from meta_info.")
    customer_email: Optional[str] = Field(None, description="Customer's email address. If not provided, will be taken from meta_info.")
    customer_phone: Optional[str] = Field(None, description="Customer's phone number. If not provided, will be taken from meta_info.")
    return_url: str = Field(..., description="URL to redirect after payment.")
    
    description: Optional[str] = Field(None, description="Description of the order.")
    product_id: Optional[str] = Field(None, description="Product identifier.")
    get_client_auth_token: Optional[bool] = Field(False, description="Whether to get client auth token in response.")
    
    # Billing address fields
    billing_address_first_name: Optional[str] = Field(None, description="Billing first name")
    billing_address_last_name: Optional[str] = Field(None, description="Billing last name")
    billing_address_line1: Optional[str] = Field(None, description="Billing address line 1")
    billing_address_line2: Optional[str] = Field(None, description="Billing address line 2")
    billing_address_line3: Optional[str] = Field(None, description="Billing address line 3")
    billing_address_city: Optional[str] = Field(None, description="Billing city")
    billing_address_state: Optional[str] = Field(None, description="Billing state")
    billing_address_country: Optional[str] = Field(None, description="Billing country")
    billing_address_postal_code: Optional[str] = Field(None, description="Billing postal code")
    billing_address_phone: Optional[str] = Field(None, description="Billing phone")
    billing_address_country_code_iso: Optional[str] = Field(None, description="Billing country ISO code")
    
    # Shipping address fields
    shipping_address_first_name: Optional[str] = Field(None, description="Shipping first name")
    shipping_address_last_name: Optional[str] = Field(None, description="Shipping last name")
    shipping_address_line1: Optional[str] = Field(None, description="Shipping address line 1")
    shipping_address_line2: Optional[str] = Field(None, description="Shipping address line 2")
    shipping_address_line3: Optional[str] = Field(None, description="Shipping address line 3")
    shipping_address_city: Optional[str] = Field(None, description="Shipping city")
    shipping_address_state: Optional[str] = Field(None, description="Shipping state")
    shipping_address_country: Optional[str] = Field(None, description="Shipping country")
    shipping_address_postal_code: Optional[str] = Field(None, description="Shipping postal code")
    shipping_address_phone: Optional[str] = Field(None, description="Shipping phone")
    shipping_address_country_code_iso: Optional[str] = Field(None, description="Shipping country ISO code")

    class Config:
        extra = "allow"


class JuspayUpdateOrderPayload(WithRoutingId):
    order_id: str = Field(..., description="Juspay order ID to update.")
    amount: Optional[str] = Field(None, description="Updated order amount (e.g., '90.00').")
    currency: Optional[str] = Field(None, description="Updated currency code.")

    class Config:
        extra = "allow"
