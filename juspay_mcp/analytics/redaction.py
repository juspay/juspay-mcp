from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any


SENSITIVE_KEY_PARTS = (
    "api_key",
    "apikey",
    "authorization",
    "card",
    "cookie",
    "cvv",
    "pan",
    "password",
    "secret",
    "token",
)

REDACTED = "[REDACTED]"
TRUNCATED = "[TRUNCATED]"


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in SENSITIVE_KEY_PARTS)


def redact(value: Any) -> Any:
    if isinstance(value, Mapping):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            str_key = str(key)
            redacted[str_key] = REDACTED if _is_sensitive_key(str_key) else redact(item)
        return redacted

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [redact(item) for item in value]

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    return value


def fit_jsonb_payload(value: dict[str, Any], max_bytes: int) -> dict[str, Any]:
    """Return a JSON-serializable payload no larger than max_bytes if possible."""
    payload = redact(value)
    encoded = json.dumps(payload, default=str, separators=(",", ":")).encode("utf-8")
    if len(encoded) <= max_bytes:
        return payload

    compact = dict(payload)
    if "arguments" in compact:
        compact["arguments"] = TRUNCATED
    if "metadata" in compact:
        compact["metadata"] = TRUNCATED

    encoded = json.dumps(compact, default=str, separators=(",", ":")).encode("utf-8")
    if len(encoded) <= max_bytes:
        return compact

    return {
        "type": compact.get("type", "unknown"),
        "mcp": compact.get("mcp"),
        "tool": compact.get("tool"),
        "status": compact.get("status"),
        "payload_truncated": True,
    }
