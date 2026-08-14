# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from juspay_mcp.api_schema.session import JuspaySessionPayload
from juspay_mcp.api_schema.session_preflight import JuspaySessionPreflightPayload

DEFAULT_GATEWAY = "DEFAULT"

# Extra mandatory params a configured gateway needs on top of whatever the
# session create API itself requires. Keyed by gateway name (upper-cased).
# `amount` and `return_url` are intentionally absent here — they are already
# required by JuspaySessionPayload and are picked up from the session schema.
GATEWAY_REQUIREMENTS = {
    DEFAULT_GATEWAY: [
        "currency",
    ],
}

# Field descriptions, so the caller is told what to go collect.
_FIELD_DESCRIPTIONS = {
    name: prop.get("description", "")
    for name, prop in JuspaySessionPreflightPayload.model_json_schema()
    .get("properties", {})
    .items()
}


def _session_required_fields() -> list[str]:
    """Required fields of the session create API, read off its live schema so
    this check never drifts from JuspaySessionPayload."""
    return list(JuspaySessionPayload.model_json_schema().get("required", []))


def _is_absent(value) -> bool:
    """A present-but-blank value is as useless to the gateway as an absent one."""
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _requirements(gateway: str) -> list[tuple[str, str]]:
    """Merged (field, source) requirements, session fields first, deduped."""
    merged: list[tuple[str, str]] = []
    seen = set()
    for field in _session_required_fields():
        if field not in seen:
            seen.add(field)
            merged.append((field, "session_schema"))
    for field in GATEWAY_REQUIREMENTS[gateway]:
        if field not in seen:
            seen.add(field)
            merged.append((field, "gateway"))
    return merged


def _next_action(missing: list[dict]) -> str:
    """The instruction handed back to the calling agent. Missing params must be
    collected from the user — never guessed, defaulted or invented — so this
    spells that out rather than relying on the tool description alone."""
    if not missing:
        return (
            "All mandatory params are present. You may now call session_api_juspay "
            "with this payload."
        )

    fields = ", ".join(entry["field"] for entry in missing)
    return (
        "Do NOT call session_api_juspay yet, and do NOT guess, invent, default or "
        "use placeholder values for the missing params. Ask the user to supply "
        f"these {len(missing)} param(s) directly: {fields}. Use each param's "
        "`description` to phrase the request. Once the user has provided them, "
        "call session_preflight_check_juspay again to confirm nothing is "
        "outstanding before creating the session."
    )


async def session_preflight_check_juspay(payload: dict) -> dict:
    """
    Reports which mandatory params are still missing before a Juspay session
    can be created and carried through to a completed payment.

    Purely local — makes no network call. Combines the required fields of the
    session create API with the extra params the configured gateway demands,
    then reports which of them the given payload is missing.

    Args:
        payload (dict): A partial (or empty) session payload, optionally with a
                        `gateway` key naming the configured gateway.

    When anything is missing, the returned `next_action` instructs the calling
    agent to collect those params from the user rather than proceeding.

    Returns:
        dict: {ready, gateway, gateway_recognised, next_action, missing, satisfied}
    """
    payload = payload or {}

    requested_gateway = payload.get("gateway") or DEFAULT_GATEWAY
    gateway = str(requested_gateway).upper()
    gateway_recognised = gateway in GATEWAY_REQUIREMENTS
    if not gateway_recognised:
        gateway = DEFAULT_GATEWAY

    missing = []
    satisfied = []

    for field, source in _requirements(gateway):
        if _is_absent(payload.get(field)):
            missing.append(
                {
                    "field": field,
                    "description": _FIELD_DESCRIPTIONS.get(field, ""),
                    "source": source,
                }
            )
        else:
            satisfied.append(field)

    return {
        "ready": not missing,
        "gateway": gateway,
        "gateway_recognised": gateway_recognised,
        "next_action": _next_action(missing),
        "missing": missing,
        "satisfied": satisfied,
    }
