# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from typing import Optional, List
from pydantic import BaseModel, Field

class ListEmiPlansPayload(BaseModel):
    """
    Payload for listing EMI plans. All filters are optional.
    """
    emiType: Optional[str] = None
    gateway: Optional[str] = None
    bankCode: Optional[str] = None
    tenure: Optional[int] = None
    cardType: Optional[str] = None
    offset: Optional[int] = None
    limit: Optional[int] = None
    disabled: Optional[bool] = None

class EmiPlanItem(BaseModel):
    """
    Represents a single EMI plan item in the response.
    """
    tenure: int
    paymentMethodType: str
    gateway: str
    gatewayPlanId: Optional[str] = None
    minAmount: float
    emiType: str
    cardType: str
    interestRate: float
    juspayBankCodeId: int
    id: int
    paymentMethod: str
    bankCode: str
    merchantAccountId: int

class EmiPlanSummary(BaseModel):
    """
    Represents the summary object in the EMI plans response.
    """
    count: int
    totalCount: int

class EmiPlansResponse(BaseModel):
    """
    Represents the overall response structure for listing EMI plans.
    """
    summary: EmiPlanSummary
    rows: List[EmiPlanItem]
