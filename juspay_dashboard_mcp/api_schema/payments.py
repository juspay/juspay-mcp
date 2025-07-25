# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from typing import Optional, Dict, Any
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
