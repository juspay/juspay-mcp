# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from pydantic import BaseModel, Field
from typing import Optional
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


class JuspayCreateOrValidateBeneficiaryPayload(WithHeaders):
    """Payload for creating or validating beneficiary bank account.
    
    Merchants can CREATE or VALIDATE beneficiary bank account using this API.
    - CREATE: Register a new beneficiary with bank account details
    - VALIDATE: Verify existing beneficiary details before initiating payouts
    
    Accepts simple flat values (name, ifsc, account) - nested payload is constructed automatically.
    """
    command: str = Field(
        ...,
        description="Command for the operation. Required. Supported values: 'CREATE', 'VALIDATE'."
    )
    name: str = Field(
        ...,
        description="Beneficiary's name as per bank account."
    )
    ifsc: str = Field(
        ...,
        description="IFSC code of the beneficiary's bank branch."
    )
    account: str = Field(
        ...,
        description="Bank account number of the beneficiary."
    )
    beneId: Optional[str] = Field(
        None,
        description="Unique reference ID for the beneficiary. Optional - auto-generated if not provided."
    )
    customerId: Optional[str] = Field(
        None,
        description="Merchant's unique customer identifier. Optional - taken from meta_info.customer_id if not provided."
    )
    email: Optional[str] = Field(
        None,
        description="Email address of the beneficiary. Optional - taken from meta_info.email if not provided."
    )
    phone: Optional[str] = Field(
        None,
        description="Phone number of the beneficiary. Optional - taken from meta_info.phone_no if not provided."
    )
