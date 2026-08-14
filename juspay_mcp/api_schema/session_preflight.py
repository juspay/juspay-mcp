# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from pydantic import BaseModel, Field
from typing import Optional, Literal


class JuspaySessionPreflightPayload(BaseModel):
    """Payload for the session preflight check.

    Every field is deliberately Optional. This tool exists to report which
    mandatory fields are *absent*, so it must be callable with a partial (even
    empty) payload — the generic required-field guard in `tools.py` would
    otherwise reject the call before the check could run.
    """

    gateway: Optional[str] = Field(
        None,
        description=(
            "Name of the configured payment gateway whose extra mandatory "
            "requirements should be checked (e.g., 'RAZORPAY'). "
            "Defaults to 'DEFAULT' when omitted or unrecognised."
        ),
    )

    # --- Fields mirrored from JuspaySessionPayload ---
    order_id: Optional[str] = Field(None, description="Unique Identifier for the order (Max 21 Alphanumeric).")
    amount: Optional[str] = Field(None, description="Amount customer has to pay (e.g., '1.00').")
    customer_id: Optional[str] = Field(None, description="Unique merchant identifier for the customer.")
    customer_email: Optional[str] = Field(None, description="Customer's email address.")
    customer_phone: Optional[str] = Field(None, description="Customer's mobile number.")
    payment_page_client_id: Optional[str] = Field(None, description="Unique merchant identifier provided by Juspay.")
    action: Optional[Literal["paymentPage", "paymentManagement"]] = Field(
        None,
        description="Action to be performed, e.g., 'paymentPage'."
    )
    return_url: Optional[str] = Field(None, description="URL for redirection post payment.")

    # --- Extra fields required to carry the payment through to completion ---
    currency: Optional[str] = Field(None, description="Currency code (e.g., 'INR').")

    class Config:
        extra = "allow"
