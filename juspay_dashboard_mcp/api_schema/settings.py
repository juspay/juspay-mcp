# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from typing import List, Optional
from pydantic import BaseModel, Field

from juspay_dashboard_mcp.api_schema.headers import WithHeaders

class JuspayConflictSettingsPayload(WithHeaders):
    """Schema for conflict settings API."""
    pass  # No specific fields required beyond the common headers

class JuspayGeneralSettingsPayload(WithHeaders):
    """Schema for general settings API."""
    pass  # No specific fields required beyond the common headers

class JuspayMandateSettingsPayload(WithHeaders):
    merchantId: Optional[str] = Field(
        None, 
        description="Optional merchant ID to retrieve mandate settings for."
    )

class JuspayPriorityLogicSettingsPayload(WithHeaders):
    """Schema for priority logic settings API."""
    pass  # No specific fields required beyond the common headers

class JuspayRoutingSettingsPayload(WithHeaders):
    """Schema for routing settings API."""
    pass  # No specific fields required beyond the common headers

class JuspayWebhookSettingsPayload(WithHeaders):
    """Schema for webhook settings API."""
    pass  # No specific fields required beyond the common headers


class JuspayUpdateGeneralSettingsPayload(WithHeaders):
    """Update payload for the merchant's general settings.

    Currently exposes only `returnUrl` (the payment redirect URL). Pass an
    empty string to clear it.
    """

    returnUrl: str = Field(
        ...,
        description=(
            "Payment redirect URL the merchant's customer is sent back to "
            "after the Juspay-hosted payment flow completes. Pass an empty "
            "string to clear/unset."
        ),
    )


class JuspayUpdateWebhookSettingsPayload(WithHeaders):
    """Update the webhook URL and event subscriptions for the merchant.

    `webhookEvents` REPLACES the merchant's full event subscription map —
    events not listed will be unsubscribed. The handler internally rebuilds
    the `webhookConfigs` JSON with defaults for the boilerplate flags
    (addFullGatewayResponse, trimWebhookResponse, etc.) so the caller only
    needs to think about URL + events + optional basic-auth credentials.
    """

    webHookurl: str = Field(
        ...,
        description=(
            "URL Juspay will POST event notifications to. Must be a fully "
            "qualified HTTPS URL reachable from Juspay's infrastructure."
        ),
    )
    webhookEvents: List[str] = Field(
        ...,
        description=(
            "List of Juspay event names to subscribe to. Example: "
            "[\"ORDER_SUCCEEDED\", \"ORDER_FAILED\", \"TXN_CHARGED\"]. "
            "Common event names include ORDER_SUCCEEDED, ORDER_FAILED, "
            "ORDER_CREATED, ORDER_AUTHORIZED, TXN_CREATED, TXN_CHARGED, "
            "MANDATE_CREATED, MANDATE_ACTIVATED, MANDATE_REVOKED, "
            "MANDATE_FAILED, NOTIFICATION_SUCCEEDED, TOKEN_STATUS_CREATED, "
            "TOKEN_STATUS_UPDATED, CHARGEBACK_ALREADY_REFUNDED. Pass an "
            "empty list to unsubscribe from all events."
        ),
    )
    webHookUsername: Optional[str] = Field(
        None,
        description=(
            "Optional HTTP basic-auth username Juspay will use when calling "
            "the webhook URL."
        ),
    )
    webHookPassword: Optional[str] = Field(
        None,
        description=(
            "Optional HTTP basic-auth password Juspay will use when calling "
            "the webhook URL."
        ),
    )