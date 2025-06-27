# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from typing import Optional, Dict, Any, List, Literal, Union
from pydantic import BaseModel, Field, model_validator
from juspay_dashboard_mcp.api_schema.headers import WithHeaders

# Import the flat filter types
FilterFieldDimensionEnum = Literal[
    "customer_id",
    "business_region",
    "actual_order_status",
    "ord_currency",
    "order_refunded_entirely",
    "order_source_object",
    "order_source_object_id",
    "order_status",
    "order_type",
    "is_retargeted_order",
    "is_retried_order",
    "industry",
    "prev_order_status",
    "order_created_at",
    "merchant_id",
    "full_udf1",
    "full_udf2",
    "full_udf3",
    "full_udf4",
    "full_udf5",
    "full_udf6",
    "full_udf7",
    "full_udf8",
    "full_udf9",
    "full_udf10",
    "order_amount",
    "card_brand",
    "auth_type",
    "is_cvv_less_txn",
    "is_emi",
    "emi_bank",
    "emi_type",
    "emi_tenure",
    "payment_method_type",
    "payment_method_subtype",
    "error_code",
    "error_message",
    "error_category",
    "gateway_reference_id",
    "payment_gateway",
    "bank",
    "date_created",
]

FilterCondition = Literal[
    "In", "NotIn", "Greater", "GreaterThanEqual", "LessThanEqual", "Less"
]


class Clause(BaseModel):
    """Single predicate applied to a dimension."""

    field: FilterFieldDimensionEnum
    condition: FilterCondition
    val: Union[str, bool, float, None, List[Union[str, bool, None]]]


class FlatFilter(BaseModel):
    """Flat representation of the boolean filter tree."""

    clauses: List[Clause] = Field(..., min_items=1, max_items=10)
    logic: str = Field(
        ...,
        description="Expression referencing clause indices, e.g. '(0 AND (1 OR 2))'",
    )

    @model_validator(mode="after")
    def _check_logic_indices(self) -> "FlatFilter":
        """Sanity check: make sure logic only references valid indices."""
        import re

        if self.logic:
            max_idx = len(self.clauses) - 1
            for idx in map(int, re.findall(r"\d+", self.logic)):
                if idx > max_idx:
                    raise ValueError(f"logic references non-existent clause #{idx}")
        return self


class JuspayListOrdersV4Payload(WithHeaders):
    dateFrom: str = Field(
        ...,
        description="Start date/time in ISO 8601 format (e.g., 'YYYY-MM-DDTHH:MM:SSZ').",
    )
    dateTo: str = Field(
        ...,
        description="End date/time in ISO 8601 format (e.g., 'YYYY-MM-DDTHH:MM:SSZ').",
    )
    offset: Optional[int] = Field(
        0, description="Offset for pagination (optional, default is 0)."
    )
    limit: Optional[int] = Field(
        None,
        description="Limit for the number of orders to fetch (optional).",
    )
    status: Optional[List[str]] = Field(
        None,
        description="Optional list of order statuses to filter by (e.g., ['SUCCESS'], ['AUTHENTICATION_FAILED', 'AUTHORIZATION_FAILED']).",
    )
    order: Optional[List[List[str]]] = Field(
        None,
        description="Optional sort order specification as array of [field, direction] pairs (e.g., [['date_created', 'DESC']]).",
    )

    flatFilters: Optional[FlatFilter] = Field(
        None,
        description="""SIMPLIFIED FILTERS: Use this field instead of qFilters. Provide a flat list of filter conditions with simple logic.
        
        NOTE: Time range filters are automatically added by the handler - DO NOT include them manually.
        
        SUPPORTED CONDITIONS:
        - "In": value is in the provided list
        - "NotIn": value is not in the provided list  
        - "Greater", "GreaterThanEqual", "LessThanEqual", "Less": comparison operators
        
        SUPPORTED FIELDS BY DOMAIN:
        
        For 'ordersELS' domain:
        - customer_id: unique identifier for the customer
        - business_region: business region information
        - actual_order_status: granular order status. Values: 'COD_INITIATED', 'AUTHORIZED', 'AUTO_REFUNDED', 'AUTHENTICATION_FAILED', 'CAPTURE_INITIATED', 'CAPTURE_FAILED', 'AUTHORIZING', 'VOIDED', 'NEW', 'SUCCESS', 'PENDING_AUTHENTICATION', 'AUTHORIZATION_FAILED', 'PARTIAL_CHARGED', 'JUSPAY_DECLINED', 'TO_BE_CHARGED'
        - ord_currency: order currency
        - order_refunded_entirely: boolean, true if order is refunded entirely
        - order_source_object: source object information
        - order_source_object_id: source object ID
        - order_status: high-level order status. Values: 'SUCCESS', 'FAILURE', 'PENDING'
        - order_type: type of order. Values: 'MANDATE_PAYMENT', 'ORDER_PAYMENT', 'TPV_MANDATE_REGISTER', 'TPV_PAYMENT', 'MOTO_PAYMENT', 'VAN_PAYMENT', 'MANDATE_REGISTER', 'TPV_MANDATE_PAYMENT'
        - is_retargeted_order: boolean, true if order is retargeted
        - is_retried_order: boolean, true if order is retried
        - industry: industry of the merchant
        - prev_order_status: previous order status. Values: 'SUCCESS', 'FAILURE', 'PENDING'
        - order_created_at: order created timestamp (epoch seconds)
        - merchant_id: unique identifier for the merchant (lowercase, no spaces)
        - full_udf1 through full_udf10: user-defined fields for additional order information
        
        For 'txnsELS' domain:
        - order_amount: order amount for filtering by amount
        - card_brand: card brand for filtering by card brand
        - auth_type: type of authentication used
        - is_cvv_less_txn: boolean, true if CVV-less transaction
        - is_emi: boolean, true if EMI transaction
        - emi_bank: bank used for EMI transactions
        - emi_type: EMI type. Values: 'STANDARD_EMI', 'NO_COST_EMI', 'LOW_COST_EMI'
        - emi_tenure: EMI tenure in months
        - payment_method_type: payment method type. Values: 'CARD', 'UPI', 'WALLET', 'NB', 'CONSUMER_FINANCE', 'REWARD', 'CASH', 'RTP', 'MERCHANT_CONTAINER', 'AADHAAR'
        - payment_method_subtype: payment method subtype (e.g., 'UPI_COLLECT', 'UPI_INTENT', 'UPI_QR')
        - error_code: error code during order processing
        - error_message: error message during order processing
        - error_category: error category based on error code
        - gateway_reference_id: payment gateway reference ID
        - payment_gateway: payment gateway name
        - bank: payment method used (also stores UPI handles, wallet names)
        - date_created: transaction created timestamp (epoch seconds)
        
        IMPORTANT FILTERING RULES:
        - ALWAYS filter out null values when querying top values: use "condition": "NotIn", "val": [null]
        - When asked to filter on order success/failure, always use "order_status" by default. If the user wants more fine grained filtering then use actual_order_status otherwise always default to "order_status". Supported values for order_status: ["SUCCESS", "FAILURE", "PENDING"]
        - When asked about payments through UPI handle/VPA/UPI ID/UPI Address (eg. @icici, @okicici, @okhdfcbank, @ptyes), set payment_method_subtype filter on UPI_COLLECT. UPI handle is stored in "bank" field. (example - 'paytm handle' in the query refers to "Paytm" in the "bank" field and set payment_method_subtype filter on UPI_COLLECT)
        - When asked about orders processed through a specific wallet, set payment_method_type filter on WALLET and the wallet name is stored in "bank" field
        - If the query asks details about a specific merchant, add the filter for merchant_id. (Note: merchant_id should be lowercase and without spaces)
        - Consider Conversational Context: Carefully examine if the current user query is a continuation or refinement of a previous query within the ongoing conversation. If the current query lacks specific filter details but appears to build upon earlier messages, actively infer the necessary filters from the established conversational context. For example, if the user first asks "Give me the most recent orders" and then follows up with "Break it down by payment method type", the second query implicitly requires the payment_method dimension for the orders from the first query.
        - You are not allowed to use any field apart from the provided possible enum values in the JSON schema
        - After generating the filter, check each key and match it with the allowed JSON schema. Do not return filters outside of the JSON schema
        - Only use fields from the supported enum values above
        
        EXAMPLE - Latest SUCCESS orders with payment gateway filtering:
        {
            "clauses": [
                {"field": "order_status", "condition": "In", "val": ["SUCCESS"]},
                {"field": "payment_gateway", "condition": "NotIn", "val": [null]}
            ],
            "logic": "0 AND 1"
        }
        
        EXAMPLE - UPI Paytm handle orders:
        {
            "clauses": [
                {"field": "payment_method_subtype", "condition": "In", "val": ["UPI_COLLECT"]},
                {"field": "bank", "condition": "In", "val": ["Paytm"]}
            ],
            "logic": "0 AND 1"
        }
        
        EXAMPLE - Wallet orders:
        {
            "clauses": [
                {"field": "payment_method_type", "condition": "In", "val": ["WALLET"]},
                {"field": "bank", "condition": "In", "val": ["PayPal"]}
            ],
            "logic": "0 AND 1"
        }""",
    )
    domain: str = Field(
        ...,
        description="Domain for query, choose between 'ordersELS' or 'txnsELS' based on the filers passed in qfilters. If unsure, use 'txnsELS'. Choose 'ordersELS' only when ALL filters passed in qFilters are from the ordersELS domain. Even if any one filter is from the txnsELS domain, use 'txnsELS'."
    )


class JuspayGetOrderDetailsPayload(WithHeaders):
    order_id: str = Field(
        ..., description="Order ID for which details are to be fetched."
    )
