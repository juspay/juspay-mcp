# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from pydantic import BaseModel, Field
from typing import Optional

class WithRoutingId(BaseModel):
    merchant_id_header: Optional[str] = Field(
        None,
        alias="x-merchantid",
        description=(
            "Merchant to execute this call as, sent upstream as the x-merchantid header. "
            "Overrides the JUSPAY_MERCHANT_ID header and the JUSPAY_MERCHANT_ID environment "
            "variable for this call only. Omit it to use the configured default merchant. "
            "This is transport credentials, not request data — it is stripped from the body "
            "before the call, and is unrelated to any `merchant_id` an endpoint takes in its "
            "own payload."
        )
    )
    routing_id: Optional[str] = Field(
        None,
        description=(
            "Optional custom routing ID for the API request. "
            "We recommend passing the customer_id as the x-routing-id. "
            "If the customer is checking out as a guest, you can pass an alternative ID "
            "that helps track the payment session lifecycle (e.g., Order ID or Cart ID)."
        )
    )
