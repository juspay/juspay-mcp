# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from typing import Optional
from pydantic import BaseModel, Field
from juspay_dashboard_mcp.api_schema.headers import WithHeaders


class JuspayListSurchargeRulesPayload(WithHeaders):
    """Returns a list of all configured surcharge rules, including their current status and rule definitions."""
    merchantId: Optional[str] = Field(
        None,
        description="Merchant identifier (admin only, optional)."
    )
