# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from typing import Literal, Optional

from pydantic import Field

from juspay_ai_studio_mcp.api_schema.headers import WithHeaders


SessionStatus = Literal[
    "CREATED",
    "RUNNING",
    "IO_WAITING",
    "IO_COMPLETED",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
]


class CreateSessionPayload(WithHeaders):
    client_id: Optional[str] = Field(
        None,
        description="Merchant client ID whose payment page should be edited or inspected.",
    )
    requirement: str = Field(
        ...,
        min_length=1,
        description="Natural-language Studio AI request, for example 'disable wallet payments'.",
    )
    platforms: Optional[Literal["desktop", "mobile", "both"]] = Field(
        None,
        description="Viewport scope for validation. Defaults to the PP Studio AI service default.",
    )
    model: Optional[str] = Field(
        None,
        description="Optional model override for the PP Studio AI worker.",
    )
    approved_version: Optional[str] = Field(
        None,
        description="Optional approved Studio config version to use as the starting point.",
    )


class ResumeSessionPayload(WithHeaders):
    session_id: str = Field(
        ...,
        min_length=1,
        description="PP Studio AI session ID to resume.",
    )
    input: str = Field(
        ...,
        min_length=1,
        description="User reply or follow-up instruction for the session.",
    )


class ListSessionPayload(WithHeaders):
    status: Optional[SessionStatus] = Field(
        None,
        description="Optional session status filter.",
    )
    client_id: Optional[str] = Field(
        None,
        description="Optional merchant client ID filter.",
    )


class GetSessionPayload(WithHeaders):
    session_id: str = Field(
        ...,
        min_length=1,
        description="PP Studio AI session ID to inspect.",
    )


class StopSessionPayload(WithHeaders):
    session_id: str = Field(
        ...,
        min_length=1,
        description="PP Studio AI session ID to stop/interrupt.",
    )


class PaymentPageLinkPayload(WithHeaders):
    session_id: str = Field(
        ...,
        min_length=1,
        description="PP Studio AI session ID whose review URL should be returned.",
    )
    viewport: Optional[Literal["desktop", "mobile"]] = Field(
        None,
        description="Optional viewport hint appended to the review URL.",
    )


class DownloadConfigsPayload(WithHeaders):
    session_id: str = Field(
        ...,
        min_length=1,
        description="PP Studio AI session ID whose generated config zip URL should be returned.",
    )
