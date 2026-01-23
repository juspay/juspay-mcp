# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from typing import Optional
from pydantic import BaseModel, Field

from juspay_dashboard_mcp.api_schema.headers import WithHeaders

class JuspayGetUserPayload(WithHeaders):
    userId: str = Field(
        ..., 
        description="Unique identifier for the user to retrieve."
    )
    merchantId: Optional[str] = Field(
        None, 
        description="Merchant identifier (admin only, optional)."
    )

class JuspayGetUserDetailsPayload(WithHeaders):
    userId: str = Field(
        ..., 
        description="Unique identifier for the user to retrieve detailed information for."
    )

class JuspayListUsersV2Payload(WithHeaders):
    offset: Optional[int] = Field(
        0, 
        description="Pagination offset for the user list (default: 0)."
    )
    merchantId: Optional[str] = Field(
        None, 
        description="Merchant identifier (admin only, optional)."
    )
