# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from typing import List, Literal, Optional
from pydantic import BaseModel, Field

DomainEnum = Literal[
    "kvorders",
    "kvtxns",
    "kvrefundtxns",
    "kvoffers",
    "mandateexecutionkv",
    "fulfillmentorders",
    "sdklogs",
    "kvcustomer",
    "kvmandates",
    "unauthtxns",
    "apirequests",
]


class QApiInfoPayload(BaseModel):
    domain: DomainEnum = Field(
        ...,
        description="Analytics domain to retrieve schema for (dimensions, filters, metrics).",
    )


class QApiDimensionLookupRequest(BaseModel):
    dimension: str = Field(
        ...,
        description="Dimension name to look up values for.",
    )
    queries: List[str] = Field(
        default_factory=list,
        description="Fuzzy search queries. If empty, returns the first N values for the dimension.",
    )
    max_results: Optional[int] = Field(
        None,
        description="Maximum results per query. Overrides default_limit when set.",
    )


class QApiFieldValueDiscoveryPayload(BaseModel):
    domain: DomainEnum = Field(
        ...,
        description="Analytics domain to query field values for.",
    )
    requests: List[QApiDimensionLookupRequest] = Field(
        ...,
        description="List of dimension lookup requests.",
    )
    default_limit: int = Field(
        10,
        description="Default maximum results per query (1–50). Can be overridden per request via max_results.",
        ge=1,
        le=50,
    )
