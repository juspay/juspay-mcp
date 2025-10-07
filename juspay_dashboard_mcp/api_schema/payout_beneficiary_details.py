# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from pydantic import BaseModel, Field
from juspay_dashboard_mcp.api_schema.headers import WithHeaders


class JuspayListBeneficiariesPerCustomerIdPayload(WithHeaders):
    customerId: str = Field(
        ...,
        description="Unique identifier for the customer whose beneficiaries are to be retrieved. Used to fetch all beneficiaries associated with this specific customer for payout operations.",
    )


class JuspayGetBeneficiaryDetailsPayload(WithHeaders):
    customerId: str = Field(
        ...,
        description="Unique identifier for the customer who owns the beneficiary account.",
    )
    beneId: str = Field(
        ...,
        description="Unique identifier for the specific beneficiary whose detailed information is to be retrieved.",
    )
