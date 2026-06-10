# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from typing import Optional
from pydantic import Field

from juspay_dashboard_mcp.api_schema.headers import WithHeaders


class JuspayGetClientConfigPayload(WithHeaders):
    merchantId: Optional[str] = Field(
        default=None,
        description="Merchant ID to fetch client configuration for. Auto-detected from session if not provided."
    )
