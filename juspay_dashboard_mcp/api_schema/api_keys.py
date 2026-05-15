# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from pydantic import Field
from juspay_dashboard_mcp.api_schema.headers import WithHeaders


class JuspayCreateApiKeyPayload(WithHeaders):
    """Generate a new API key for the merchant.

    The returned `apiKey` is shown only once at creation — the dashboard
    keeps only its masked form afterwards.
    """

    description: str = Field(
        ...,
        description=(
            "Human-readable label for the key (shown in the merchant's API "
            "Keys listing). Keep it short and identifiable, e.g. "
            "'mcp-cli-2026-05'."
        ),
    )
