# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from pydantic import Field

from juspay_dashboard_mcp.api_schema.headers import WithHeaders


class GetMandateDetailsPayload(WithHeaders):
    mandate_id: str = Field(
        ...,
        description="The mandate ID to fetch details for (e.g., '9VTmNzY7SeT5TndRfXzEeg')."
    )
