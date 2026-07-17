from __future__ import annotations

import base64
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return int(raw)


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def is_local_development() -> bool:
    raw = os.getenv("DEPLOYMENT_ENV") or ""
    return raw.strip().lower() == "local"


# --- ingest token resolution (plaintext, or KMS-decrypted once at startup) -----------

_resolved_token: str | None = None
_token_resolved = False


def _kms_decrypt(ciphertext_b64: str) -> str | None:
    """Decrypt a base64-encoded AWS KMS ciphertext to plaintext.

    boto3 is imported lazily so the public package works without it whenever KMS is not
    used (self-hosters, local dev). Returns None on any failure — a bad token just
    disables analytics, it never crashes the server.
    """
    try:
        import boto3  # optional dependency: install `juspay-mcp[kms]`

        region = os.getenv("CLI_ANALYTICS_KMS_REGION") or os.getenv("AWS_REGION")
        client = boto3.client("kms", region_name=region)
        resp = client.decrypt(CiphertextBlob=base64.b64decode(ciphertext_b64))
        return resp["Plaintext"].decode("utf-8")
    except Exception:
        logger.error(
            "CLI analytics: KMS decrypt of CLI_ANALYTICS_INGEST_TOKEN failed — analytics disabled",
            exc_info=True,
        )
        return None


def _resolve_ingest_token() -> str | None:
    """The ingest bearer token, resolved once and cached.

    Plaintext by default. When `CLI_ANALYTICS_INGEST_TOKEN_KMS` is truthy (and not local
    dev), the env value is treated as a base64 KMS ciphertext and decrypted a single time;
    the decrypted plaintext is what gets sent as the bearer over TLS.
    """
    global _resolved_token, _token_resolved
    if _token_resolved:
        return _resolved_token
    raw = os.getenv("CLI_ANALYTICS_INGEST_TOKEN") or None
    if raw and _env_bool("CLI_ANALYTICS_INGEST_TOKEN_KMS", False) and not is_local_development():
        raw = _kms_decrypt(raw)
    _resolved_token = raw
    _token_resolved = True
    return _resolved_token


@dataclass(frozen=True)
class AnalyticsConfig:
    enabled: bool
    ingest_url: str | None
    ingest_token: str | None
    event_max_bytes: int
    http_timeout_seconds: float


def load() -> AnalyticsConfig:
    ingest_url = os.getenv("CLI_ANALYTICS_INGEST_URL") or None
    ingest_token = _resolve_ingest_token()
    # Default on only when we have somewhere to send + a token to send with.
    enabled = _env_bool("CLI_ANALYTICS_ENABLED", bool(ingest_url and ingest_token))
    return AnalyticsConfig(
        enabled=enabled,
        ingest_url=ingest_url,
        ingest_token=ingest_token,
        event_max_bytes=_env_int("CLI_ANALYTICS_EVENT_MAX_BYTES", 32 * 1024),
        http_timeout_seconds=_env_float("CLI_ANALYTICS_HTTP_TIMEOUT_SECONDS", 2.0),
    )


def warm() -> None:
    """Resolve config once at startup so the (possibly KMS-decrypting) token lookup happens
    synchronously at boot — off the request/event-loop path — and any decrypt error shows up
    in the startup logs. Logs the enabled state only; never the token value."""
    cfg = load()
    logger.info(
        "CLI analytics: %s (ingest_url=%s, token=%s)",
        "enabled" if cfg.enabled else "disabled",
        "set" if cfg.ingest_url else "unset",
        "resolved" if cfg.ingest_token else "unset",
    )
