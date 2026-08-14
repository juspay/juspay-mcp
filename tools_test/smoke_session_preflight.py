"""Verify the session preflight check reports missing mandatory params correctly:
an empty payload flags everything, a complete payload is ready, blank values count
as missing, and an unknown gateway falls back to DEFAULT. Also asserts the tool is
registered and callable with a partial payload.
"""

from __future__ import annotations

import asyncio
import sys

from juspay_mcp.api.session_preflight import (
    GATEWAY_REQUIREMENTS,
    session_preflight_check_juspay,
)
from juspay_mcp.api_schema.session import JuspaySessionPayload
from juspay_mcp.api_schema.session_preflight import JuspaySessionPreflightPayload
from juspay_mcp.tools import AVAILABLE_TOOLS

failures = []


def check(condition, message):
    if condition:
        print(f"[OK] {message}")
    else:
        print(f"[FAIL] {message}")
        failures.append(message)


def run(payload):
    return asyncio.run(session_preflight_check_juspay(payload))


SESSION_REQUIRED = list(JuspaySessionPayload.model_json_schema()["required"])
GATEWAY_EXTRAS = GATEWAY_REQUIREMENTS["DEFAULT"]

COMPLETE = {
    "order_id": "ord_1",
    "amount": "1.00",
    "customer_id": "cust_1",
    "customer_email": "a@b.com",
    "customer_phone": "9999999999",
    "payment_page_client_id": "client_1",
    "action": "paymentPage",
    "return_url": "https://example.com/return",
    "currency": "INR",
}

# --- The tool must be registered, and its schema must require nothing ---
entry = next((t for t in AVAILABLE_TOOLS if t["name"] == "session_preflight_check_juspay"), None)
check(entry is not None, "session_preflight_check_juspay is registered in AVAILABLE_TOOLS")
if entry is not None:
    check(
        not entry["schema"].get("required"),
        "preflight schema declares no required fields (so partial payloads reach the handler)",
    )

# --- Empty payload: everything is missing ---
result = run({})
check(result["ready"] is False, "empty payload -> ready is False")
missing_fields = {m["field"] for m in result["missing"]}
check(
    missing_fields == set(SESSION_REQUIRED) | set(GATEWAY_EXTRAS),
    "empty payload -> every session-required and gateway-extra field is missing",
)
check(result["satisfied"] == [], "empty payload -> nothing satisfied")
check(
    {m["field"] for m in result["missing"] if m["source"] == "gateway"} == set(GATEWAY_EXTRAS),
    "empty payload -> gateway extras are tagged source 'gateway'",
)
check(
    all(m["description"] for m in result["missing"]),
    "every missing entry carries a description",
)

# --- next_action must direct the agent to collect missing params from the user ---
action = result["next_action"]
check("ask the user" in action.lower(), "missing params -> next_action tells the agent to ask the user")
check(
    all(field in action for field in missing_fields),
    "missing params -> next_action names every missing field",
)
check(
    "do not guess" in action.lower() and "placeholder" in action.lower(),
    "missing params -> next_action forbids guessing or placeholder values",
)
check(
    "session_api_juspay" in action,
    "missing params -> next_action names the tool that must not be called yet",
)

# --- Complete payload: ready ---
result = run(dict(COMPLETE))
check(result["ready"] is True, "complete payload -> ready is True")
check(result["missing"] == [], "complete payload -> nothing missing")
check(
    set(result["satisfied"]) == set(SESSION_REQUIRED) | set(GATEWAY_EXTRAS),
    "complete payload -> all mandatory params satisfied",
)
check(
    "ask the user" not in result["next_action"].lower()
    and "session_api_juspay" in result["next_action"],
    "complete payload -> next_action clears the agent to call session_api_juspay",
)

# --- A single missing param still yields a directive naming just that param ---
result = run({k: v for k, v in COMPLETE.items() if k != "currency"})
action = result["next_action"]
check("currency" in action, "one missing param -> next_action names it")
check(
    "order_id" not in action and "customer_email" not in action,
    "one missing param -> next_action does not name satisfied params",
)

# --- Dropped params must stay dropped ---
DROPPED = ["confirm", "card_number", "card_exp_month", "card_exp_year"]
empty_missing = {m["field"] for m in run({})["missing"]}
schema_props = JuspaySessionPreflightPayload.model_json_schema()["properties"]
for field in DROPPED:
    check(field not in GATEWAY_EXTRAS, f"{field} is not in the gateway requirements")
    check(field not in empty_missing, f"empty payload -> {field} is not reported as missing")
    check(field not in schema_props, f"{field} is not in the preflight input schema")

# --- Blank string counts as missing ---
result = run(dict(COMPLETE, currency="   "))
check(
    "currency" in {m["field"] for m in result["missing"]},
    "blank currency -> treated as missing",
)

# --- Unknown gateway falls back to DEFAULT ---
result = run(dict(COMPLETE, gateway="NOT_A_REAL_GATEWAY"))
check(result["gateway"] == "DEFAULT", "unknown gateway -> falls back to DEFAULT")
check(result["gateway_recognised"] is False, "unknown gateway -> gateway_recognised is False")
check(result["ready"] is True, "unknown gateway -> still evaluates against DEFAULT requirements")

# --- Known gateway is recognised, case-insensitively ---
result = run(dict(COMPLETE, gateway="default"))
check(result["gateway_recognised"] is True, "lowercase known gateway -> recognised")

# --- The pydantic model tolerates a partial payload ---
try:
    JuspaySessionPreflightPayload(**{"order_id": "ord_1"})
    check(True, "JuspaySessionPreflightPayload accepts a partial payload")
except Exception as exc:  # noqa: BLE001
    check(False, f"JuspaySessionPreflightPayload rejected a partial payload: {exc}")

if failures:
    print(f"\n[FAIL] {len(failures)} check(s) failed")
    sys.exit(1)
print("\n[OK] session preflight check behaves as specified")
