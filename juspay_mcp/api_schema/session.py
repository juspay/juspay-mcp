from pydantic import Field
from typing import Optional, Literal
from juspay_mcp.api_schema.routing import WithRoutingId


class JuspaySessionPayload(WithRoutingId):
    order_id: str = Field(..., description="Unique Identifier for the order (Max 21 Alphanumeric).")
    amount: str = Field(..., description="Amount customer has to pay (e.g., '1.00').")
    customer_id: str = Field(..., description="Unique merchant identifier for the customer.")
    customer_email: str = Field(..., description="Customer's email address.")
    customer_phone: str = Field(..., description="Customer's mobile number.")
    payment_page_client_id: str = Field(..., description="Unique merchant identifier provided by Juspay.")
    action: Literal["paymentPage", "paymentManagement"] = Field(
        ...,
        description="Action to be performed, e.g., 'paymentPage'."
    )
    return_url: str = Field(..., description="URL for redirection post payment.")
    
    description: Optional[str] = Field(None, description="Order description for user.")
    first_name: Optional[str] = Field(None, description="Customer's first name.")
    last_name: Optional[str] = Field(None, description="Customer's last name.")
    mobile_country_code: Optional[str] = Field(None, description="Mobile country code without '+'")
    udf1: Optional[str] = Field(None, description="User defined field 1.")