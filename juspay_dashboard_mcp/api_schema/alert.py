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
    merchantId: str = Field(
        ...,
        description="Merchant ID for which alerts are to be listed."
    )
    task_type: Literal["alert"] = Field(
        "alert", 
        description="Type of monitoring task. Should be 'alert'."
    )