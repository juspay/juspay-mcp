# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from juspay_dashboard_mcp.api_schema.headers import WithHeaders
from juspay_dashboard_mcp.api_schema.qapi import Filter

class JuspayListOrdersV4Payload(WithHeaders):
    dateFrom: str = Field(
        ...,
        description="Start date/time in ISO 8601 format (e.g., 'YYYY-MM-DDTHH:MM:SSZ')."
    )
    dateTo: str = Field(
        ...,
        description="End date/time in ISO 8601 format (e.g., 'YYYY-MM-DDTHH:MM:SSZ')."
    )
    offset: Optional[int] = Field(
        0,
        description="Offset for pagination (optional, default is 0)."
    )
    limit: Optional[int] = Field(
        None, # Default to None if not provided
        description="Limit for the number of orders to fetch (optional)."
    )
    paymentStatus: Optional[str] = Field(
        None,
        description="Optional filter for payment status (e.g., 'CHARGED', 'PENDING')."
    )
    orderType: Optional[str] = Field(
        None,
        description="Optional filter for order type."
    )
    domain: Optional[str] = Field(
        "ordersELS",
        description="Domain for query (optional, default is 'ordersELS')."
    ),
    qFilters: Optional[Dict[str, Any]] = Field(
         None,
        description="""A dict representing the 'filters' section with valid field values from the schema.
                IMPORTANT NOTES:
                  - DO NOT pass limit in qFilters. It is already handled in the payload.
                  - Only pass the supported filters in the qFilters. DO NOT pass anyother filters in qFilter. The supported filters are:
                        "customer_id", // unique identifier for the customer
                        "business_region", 
                        "actual_order_status", // actual order status gives granular information about the order status. Possible values are: 'COD_INITIATED', 'AUTHORIZED', 'AUTO_REFUNDED', 'AUTHENTICATION_FAILED', 'CAPTURE_INITIATED', 'CAPTURE_FAILED', 'AUTHORIZING', 'VOIDED', 'NEW', 'SUCCESS', 'PENDING_AUTHENTICATION', 'AUTHORIZATION_FAILED', 'PARTIAL_CHARGED', 'JUSPAY_DECLINED', 'TO_BE_CHARGED'
                        "ord_currency", // Order currency
                        "order_refunded_entirely", // boolean, true if order is refunded entirely
                        "order_source_object", 
                        "order_source_object_id",
                        "order_status", // order status gives high level information about the order status. Possible values are: 'SUCCESS', 'FAILURE', 'PENDING'
                        "order_type", // order type gives information about the type of order. Possible values are: 'MANDATE_PAYMENT', 'ORDER_PAYMENT', 'TPV_MANDATE_REGISTER', 'TPV_PAYMENT', 'MOTO_PAYMENT', 'VAN_PAYMENT', 'MANDATE_REGISTER', 'TPV_MANDATE_PAYMENT'
                        "is_retargeted_order", // boolean, true if order is retargeted
                        "is_retried_order", // boolean, true if order is retried
                        "industry", // industry of the merchant
                        "prev_order_status", // previous order status gives information about the previous status of the order. Possible values are: 'SUCCESS', 'FAILURE', 'PENDING'
                        "order_created_at", // order created at timestamp
                        "merchant_id", // unique identifier for the merchant
                        "full_udf1", // UDFs are user-defined fields that can be used to store additional information about the order. The UDFs are stored as key-value pairs. The keys are "full_udf1", "full_udf2", "full_udf3", "full_udf4", "full_udf5", "full_udf6", "full_udf7", "full_udf8", "full_udf9", and "full_udf10". The values can be any string.
                        "full_udf2", 
                        "full_udf3",
                        "full_udf4", 
                        "full_udf5",
                        "full_udf6",
                        "full_udf7",
                        "full_udf8",
                        "full_udf9",
                        "full_udf10"
                 
                     # Example filter for latest orders with actual_order_status as SUCCESS 
                        {
    "and": {
        "right": {
            "field": "order_created_at",
            "condition": "LessThanEqual",
            "val": "1741328100"
        },
        "left": {
            "and": {
                "right": {
                    "field": "order_created_at",
                    "condition": "GreaterThanEqual",
                    "val": "1741285800"
                },
                "left": {
                    "field": "actual_order_status",
                    "condition": "In",
                    "val": "SUCCESS"
                }
            }
        }
    }
}                   
                  ```
                 - ALWAYS add a filter to exclude null values when querying for top values of any dimension/field. This ensures that null values don't appear in the top results. For example, when asked for "top payment gateways", always include a filter like `"condition": "NotIn", "field": "payment_gateway", "val": [null]`. _MAKE SURE TO ALWAYS FILTER OUT NULL VALUES NOT EMPTY STRING ""_
                 - Consider Conversational Context: Carefully examine if the current user query is a continuation or refinement of a previous query within the ongoing conversation. If the current query lacks specific filter details but appears to build upon earlier messages, actively infer the necessary filters from the established conversational context. For example, if the user first asks "Give me the most recent orders" and then follows up with "Break it down by payment method type", the second query implicitly requires the `payment_method` dimension for the orders from the first query.
                 - You are not allowed to use any field apart from the provided possible enum values in the JSON schema.
                 - Do not return an empty filter object.
                 - After generating the filter, check each key and match it with the allowed JSON schema. Do not return filters outside of the JSON schema.
                 - Return only the JSON filter in the output; do not return any other text apart from the generated filter.
                 - If the query asks details about a specific merchant, add the filter for merchant_id. (Note: merchant_id should be lowercase and without spaces)
                 - NOTE: When asked to filter on order success/failure, always use "order_status" in dimensions or filter fields. If the user wants more fine grained filtering then use actual_order_status otherwise always default to "order_status". Supported values for order_status: ["SUCCESS", "FAILURE", "PENDING"]"""
    )

class JuspayGetOrderDetailsPayload(WithHeaders):
    order_id: str = Field(
        ...,
        description="Order ID for which details are to be fetched."
    )