# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from typing import Optional
from pydantic import BaseModel, Field
from juspay_dashboard_mcp.api_schema.headers import WithHeaders


class JuspayGetPayoutGatewayDetailsPayload(WithHeaders):
    gateway: str = Field(
        ...,
        description="Gateway identifier/type for the payout gateway (e.g., 'RAZORPAY', 'PAYU'). Specifies which gateway's credential details are to be retrieved.",
    )
    rail: str = Field(
        ...,
        description="Rail identifier for the gateway configuration. Used in conjunction with gateway to identify the specific gateway credential setup.",
    )


class JuspayGetPayoutBalancePayload(WithHeaders):
    isForce: Optional[str] = Field(
        "false",
        description="Force refresh balance from gateways. Set to 'true' to fetch real-time balance data directly from gateway providers, 'false' to use cached data. Defaults to 'false'.",
        pattern="^(true|false)$"
    )
