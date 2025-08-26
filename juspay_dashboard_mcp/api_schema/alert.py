# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from pydantic import BaseModel, Field
from typing import Optional, Literal
from juspay_dashboard_mcp.api_schema.headers import WithHeaders

class JuspayAlertDetailsPayload(WithHeaders):
    task_uid: str = Field(
        ...,
        description="Unique alert ID for which details are to be fetched."
    )
    user_name: str = Field(
        ...,
        description="User name associated with the alert."
    )

class JuspayListAlertsPayload(WithHeaders):
    merchant_id: str = Field(
        ...,
        description="Merchant ID for which alerts are to be listed."
    )
    task_type: Literal["alert"] = Field(
        ...,
        description="Type of monitoring task. Should be 'alert'."
    )