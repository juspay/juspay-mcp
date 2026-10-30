# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class WithHeaders(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tenant_host: Optional[str] = Field(
        None,
        alias="x-tenant-host",
        description="Tenant host used by PP Studio AI auth when required.",
    )
