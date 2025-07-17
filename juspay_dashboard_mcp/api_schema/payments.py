# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
from juspay_dashboard_mcp.api_schema.headers import WithHeaders


class JuspayListPaymentLinksV1Payload(WithHeaders):
    qFilters: Optional[Dict[str, Any]] = Field(
        None,
        description="""Q API filters for payment links. Can be:
        1. Simple filter: {"field": "order_source_object", "condition": "Equals", "val": "PAYMENT_LINK"}
        2. Complex nested filter with AND/OR logic: {"and": {"left": {...}, "right": {...}}}
        3. Null (will default to payment link filter)
        
        Supports fields like: order_source_object, payment_status, order_type, currency, txn_id, udf1-10, customer_id, order_amount, payment_method_type, payment_gateway, merchant_id, etc.""",
    )
    date_from: str = Field(
        ...,
        description="Start date/time in ISO 8601 format (e.g., 'YYYY-MM-DDTHH:MM:SSZ').",
    )
    date_to: str = Field(
        ...,
        description="End date/time in ISO 8601 format (e.g., 'YYYY-MM-DDTHH:MM:SSZ').",
    )
    offset: Optional[int] = Field(0, description="Pagination offset (default: 0)")
    
class PaymentMethodOption(BaseModel):
    paymentMethodType: str = Field(
        ...,
        description="Payment method type (UPI, WALLET, CARD, NB, OTC, VIRTUAL_ACCOUNT, CONSUMER_FINANCE)",
    )
    enable: bool = Field(..., description="Whether this payment method is enabled")


class CardTypeOption(BaseModel):
    enable: bool = Field(..., description="Whether this card type is enabled")


class EmiOption(BaseModel):
    enable: bool = Field(..., description="Whether this EMI option is enabled")
    credit: CardTypeOption = Field(..., description="Credit card configuration")
    debit: CardTypeOption = Field(..., description="Debit card configuration")
    cardless: CardTypeOption = Field(..., description="Cardless configuration")


class EmiOptions(BaseModel):
    standardEmi: EmiOption = Field(..., description="Standard EMI configuration")
    lowCostEmi: EmiOption = Field(..., description="Low cost EMI configuration")
    noCostEmi: EmiOption = Field(..., description="No cost EMI configuration")
    showOnlyEmi: bool = Field(
        default=False, description="Whether to show only EMI options"
    )


class PaymentFilter(BaseModel):
    allowDefaultOptions: bool = Field(
        default=True, description="Whether to allow default payment options"
    )
    options: List[PaymentMethodOption] = Field(
        ..., description="List of payment method options"
    )
    emiOptions: EmiOptions = Field(..., description="EMI options configuration")


class Options(BaseModel):
    create_mandate: Optional[str] = Field(
        None, description="Mandate creation option (e.g., 'REQUIRED')"
    )


class JuspayCreatePaymentLinkPayload(WithHeaders):
    amount: Union[int, float] = Field(..., description="Payment amount (required)")
    payment_page_client_id: str = Field(
        ..., description="Client ID for payment page (required)"
    )

    currency: Optional[str] = Field(default="INR", description="Payment currency")
    mobile_country_code: Optional[str] = Field(
        default="+91", description="Mobile country code"
    )
    customer_email: Optional[str] = Field(None, description="Customer email address")
    customer_phone: Optional[str] = Field(None, description="Customer phone number")
    customer_id: Optional[str] = Field(None, description="Unique customer identifier")
    order_id: Optional[str] = Field(None, description="Unique order identifier")
    return_url: Optional[str] = Field(None, description="URL to redirect after payment")
    gateway_id: Optional[str] = Field(None, description="Gateway identifier")
    merchant_id: Optional[str] = Field(None, description="Merchant identifier")

    walletCheckBox: Optional[bool] = Field(
        default=False, description="Enable wallet payment option"
    )
    cardsCheckBox: Optional[bool] = Field(
        default=True, description="Enable cards payment option"
    )
    netbankingCheckBox: Optional[bool] = Field(
        default=False, description="Enable netbanking payment option"
    )
    upiCheckBox: Optional[bool] = Field(
        default=False, description="Enable UPI payment option"
    )
    consumerFinanceCheckBox: Optional[bool] = Field(
        default=False, description="Enable consumer finance option"
    )
    otcCheckBox: Optional[bool] = Field(
        default=False, description="Enable OTC payment option"
    )
    virtualAccountCheckBox: Optional[bool] = Field(
        default=False, description="Enable virtual account option"
    )

    shouldSendMail: Optional[bool] = Field(
        default=True, description="Whether to send email notification"
    )
    shouldSendSMS: Optional[bool] = Field(
        default=True, description="Whether to send SMS notification"
    )
    shouldSendWhatsapp: Optional[bool] = Field(
        default=True, description="Whether to send WhatsApp notification"
    )

    showEmiOption: Optional[bool] = Field(
        default=True, description="Whether to show EMI options"
    )
    standardEmi: Optional[bool] = Field(default=True, description="Enable standard EMI")
    standard_credit: Optional[bool] = Field(
        default=True, description="Enable standard credit EMI"
    )
    standard_debit: Optional[bool] = Field(
        default=False, description="Enable standard debit EMI"
    )
    standard_cardless: Optional[bool] = Field(
        default=False, description="Enable standard cardless EMI"
    )
    lowCostEmi: Optional[bool] = Field(default=False, description="Enable low cost EMI")
    low_cost_credit: Optional[bool] = Field(
        default=False, description="Enable low cost credit EMI"
    )
    low_cost_debit: Optional[bool] = Field(
        default=False, description="Enable low cost debit EMI"
    )
    low_cost_cardless: Optional[bool] = Field(
        default=False, description="Enable low cost cardless EMI"
    )
    noCostEmi: Optional[bool] = Field(default=False, description="Enable no cost EMI")
    no_cost_credit: Optional[bool] = Field(
        default=False, description="Enable no cost credit EMI"
    )
    no_cost_debit: Optional[bool] = Field(
        default=False, description="Enable no cost debit EMI"
    )
    no_cost_cardless: Optional[bool] = Field(
        default=False, description="Enable no cost cardless EMI"
    )
    showOnlyEmiOption: Optional[bool] = Field(
        default=False, description="Show only EMI options"
    )

    mandate_max_amount: Optional[str] = Field(
        None, description="Maximum mandate amount"
    )
    mandate_frequency: Optional[str] = Field(None, description="Mandate frequency")
    mandate_start_date: Optional[str] = Field(None, description="Mandate start date")

    mandate_revokable_by_customer: Optional[bool] = Field(
        None,
        alias="mandate.revokable_by_customer",
        description="Whether mandate is revokable by customer",
    )
    mandate_block_funds: Optional[bool] = Field(
        None,
        alias="mandate.block_funds",
        description="Whether to block funds for mandate",
    )
    mandate_dot_frequency: Optional[str] = Field(
        None, alias="mandate.frequency", description="Mandate frequency (dot notation)"
    )
    mandate_dot_start_date: Optional[str] = Field(
        None,
        alias="mandate.start_date",
        description="Mandate start date (dot notation)",
    )
    mandate_dot_end_date: Optional[str] = Field(
        None, alias="mandate.end_date", description="Mandate end date (dot notation)"
    )

    subventionAmount: Optional[Union[str, int, None]] = Field(
        None, description="Subvention amount"
    )
    selectUDF: Optional[List[str]] = Field(None, description="Selected UDF fields")
    offer_details: Optional[Union[Dict[str, Any], None]] = Field(
        None, description="Offer details"
    )

    options_create_mandate: Optional[str] = Field(
        None,
        alias="options.create_mandate",
        description="Mandate creation option (dot notation)",
    )

    options: Optional[Options] = Field(None, description="Options configuration")
    payment_filter: Optional[PaymentFilter] = Field(
        None, description="Payment filter configuration"
    )
    metaData: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    class Config:
        allow_population_by_field_name = True
        extra = "allow"


class JuspayCreateAutopayLinkPayload(WithHeaders):
    amount: Union[int, float] = Field(
        ..., description="One-time payment amount (required)"
    )
    payment_page_client_id: str = Field(
        ..., description="Client ID for payment page (required)"
    )
    mandate_max_amount: str = Field(
        ..., description="Max mandate amount for future payments (required)"
    )
    mandate_start_date: str = Field(..., description="Mandate creation date (required)")
    mandate_end_date: str = Field(
        ..., description="Future date after which mandate stops (required)"
    )
    mandate_frequency: str = Field(
        ...,
        description="Payment frequency - ONETIME, DAILY, WEEKLY, FORTNIGHTLY, BIMONTHLY, MONTHLY, QUARTERLY, HALFYEARLY, YEARLY, ASPRESENTED (required)",
    )

    currency: Optional[str] = Field(default="INR", description="Payment currency")
    mobile_country_code: Optional[str] = Field(
        default="+91", description="Mobile country code"
    )
    customer_email: Optional[str] = Field(None, description="Customer email address")
    customer_phone: Optional[str] = Field(None, description="Customer phone number")
    customer_id: Optional[str] = Field(None, description="Unique customer identifier")
    order_id: Optional[str] = Field(None, description="Unique order identifier")
    return_url: Optional[str] = Field(None, description="URL to redirect after payment")
    gateway_id: Optional[str] = Field(None, description="Gateway identifier")
    merchant_id: Optional[str] = Field(None, description="Merchant identifier")

    walletCheckBox: Optional[bool] = Field(
        default=False, description="Enable wallet payment option"
    )
    cardsCheckBox: Optional[bool] = Field(
        default=True, description="Enable cards payment option"
    )
    netbankingCheckBox: Optional[bool] = Field(
        default=False, description="Enable netbanking payment option"
    )
    upiCheckBox: Optional[bool] = Field(
        default=False, description="Enable UPI payment option"
    )
    consumerFinanceCheckBox: Optional[bool] = Field(
        default=False, description="Enable consumer finance option"
    )
    otcCheckBox: Optional[bool] = Field(
        default=False, description="Enable OTC payment option"
    )
    virtualAccountCheckBox: Optional[bool] = Field(
        default=False, description="Enable virtual account option"
    )

    shouldSendMail: Optional[bool] = Field(
        default=True, description="Whether to send email notification"
    )
    shouldSendSMS: Optional[bool] = Field(
        default=True, description="Whether to send SMS notification"
    )
    shouldSendWhatsapp: Optional[bool] = Field(
        default=True, description="Whether to send WhatsApp notification"
    )

    showEmiOption: Optional[bool] = Field(
        default=True, description="Whether to show EMI options"
    )
    standardEmi: Optional[bool] = Field(default=True, description="Enable standard EMI")
    standard_credit: Optional[bool] = Field(
        default=True, description="Enable standard credit EMI"
    )
    standard_debit: Optional[bool] = Field(
        default=False, description="Enable standard debit EMI"
    )
    standard_cardless: Optional[bool] = Field(
        default=False, description="Enable standard cardless EMI"
    )
    lowCostEmi: Optional[bool] = Field(default=False, description="Enable low cost EMI")
    low_cost_credit: Optional[bool] = Field(
        default=False, description="Enable low cost credit EMI"
    )
    low_cost_debit: Optional[bool] = Field(
        default=False, description="Enable low cost debit EMI"
    )
    low_cost_cardless: Optional[bool] = Field(
        default=False, description="Enable low cost cardless EMI"
    )
    noCostEmi: Optional[bool] = Field(default=False, description="Enable no cost EMI")
    no_cost_credit: Optional[bool] = Field(
        default=False, description="Enable no cost credit EMI"
    )
    no_cost_debit: Optional[bool] = Field(
        default=False, description="Enable no cost debit EMI"
    )
    no_cost_cardless: Optional[bool] = Field(
        default=False, description="Enable no cost cardless EMI"
    )
    showOnlyEmiOption: Optional[bool] = Field(
        default=False, description="Show only EMI options"
    )

    mandate_revokable_by_customer: Optional[bool] = Field(
        None,
        alias="mandate.revokable_by_customer",
        description="Whether mandate is revokable by customer",
    )
    mandate_block_funds: Optional[bool] = Field(
        None,
        alias="mandate.block_funds",
        description="Whether to block funds for mandate",
    )
    mandate_dot_frequency: Optional[str] = Field(
        None, alias="mandate.frequency", description="Mandate frequency (dot notation)"
    )
    mandate_dot_start_date: Optional[str] = Field(
        None,
        alias="mandate.start_date",
        description="Mandate start date (dot notation)",
    )
    mandate_dot_end_date: Optional[str] = Field(
        None, alias="mandate.end_date", description="Mandate end date (dot notation)"
    )

    subventionAmount: Optional[Union[str, int, None]] = Field(
        None, description="Subvention amount"
    )
    selectUDF: Optional[List[str]] = Field(None, description="Selected UDF fields")
    offer_details: Optional[Union[Dict[str, Any], None]] = Field(
        None, description="Offer details"
    )

    options_create_mandate: Optional[str] = Field(
        default="REQUIRED",
        alias="options.create_mandate",
        description="Mandate creation option (dot notation) - defaults to REQUIRED for autopay",
    )

    options: Optional[Options] = Field(None, description="Options configuration")
    payment_filter: Optional[PaymentFilter] = Field(
        None, description="Payment filter configuration"
    )
    metaData: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    class Config:
        allow_population_by_field_name = True
        extra = "allow"    
