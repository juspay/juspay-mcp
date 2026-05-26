# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from typing import Optional

from pydantic import Field

from juspay_dashboard_mcp.api_schema.headers import WithHeaders


class JuspayListZohoBooksInvoicesPayload(WithHeaders):
    customer_name: Optional[str] = Field(
        None,
        description=(
            "Zoho Books customer name. Omit this on the first call; if multiple "
            "customer names are configured, the tool returns customer_selection_required."
        ),
    )
    merchantId: Optional[str] = Field(
        None,
        description="Merchant ID. Leave empty; inferred from context automatically.",
    )
    tenantAccountId: Optional[str] = Field(
        None,
        description="Tenant account ID. Leave empty; inferred from context automatically.",
    )
    status: Optional[str] = Field(
        None,
        description="Invoice status filter: sent, draft, overdue, paid, void, unpaid, partially_paid, viewed.",
    )
    created_date: Optional[str] = Field(None, description="Filter by exact invoice creation date, YYYY-MM-DD.")
    created_date_start: Optional[str] = Field(None, description="Creation date range start (inclusive), YYYY-MM-DD. Must be used together with created_date_end.")
    created_date_end: Optional[str] = Field(None, description="Creation date range end (inclusive), YYYY-MM-DD. Must be used together with created_date_start.")
    created_date_before: Optional[str] = Field(None, description="Creation date range end (exclusive), YYYY-MM-DD. Must be used together with created_date_after.")
    created_date_after: Optional[str] = Field(None, description="Creation date range start (exclusive), YYYY-MM-DD. Must be used together with created_date_before.")
    due_date: Optional[str] = Field(None, description="Filter by exact due date, YYYY-MM-DD.")
    due_date_start: Optional[str] = Field(None, description="Due date range start (inclusive), YYYY-MM-DD. Must be used together with due_date_end.")
    due_date_end: Optional[str] = Field(None, description="Due date range end (inclusive), YYYY-MM-DD. Must be used together with due_date_start.")
    due_date_before: Optional[str] = Field(None, description="Due date range end (exclusive), YYYY-MM-DD. Must be used together with due_date_after.")
    due_date_after: Optional[str] = Field(None, description="Due date range start (exclusive), YYYY-MM-DD. Must be used together with due_date_before.")
