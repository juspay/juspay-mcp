# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

"""Helpers for writing log lines that never carry tokens, IDs or PII."""

import json
import re
from urllib.parse import urlparse

import httpx

_HAS_DIGIT = re.compile(r"\d")
_VERSION = re.compile(r"v\d+")


def safe_url(url) -> str:
    """Return ``host/path`` for logging.

    The query string, fragment and credentials are dropped, and any path
    segment containing a digit (order ids, customer ids, mga ids...) is
    replaced with ``{id}``.
    """
    try:
        parsed = urlparse(str(url))
        segments = [
            "{id}" if _HAS_DIGIT.search(seg) and not _VERSION.fullmatch(seg) else seg
            for seg in parsed.path.split("/")
        ]
        return f"{parsed.hostname or ''}{'/'.join(segments)}"
    except Exception:
        return "[unparseable-url]"


def safe_exc(exc: BaseException) -> str:
    """Describe an exception without its message.

    Exception messages can embed URLs, response bodies or request data, so
    only the class name (and the HTTP status for httpx errors) is returned.
    """
    if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
        return f"{type(exc).__name__}(status={exc.response.status_code})"
    return type(exc).__name__


# Upstream error bodies are shown to the model (and stored in analytics), and
# they often echo the request. Keep them useful for self-correction, but strip
# secrets and cap the size.
_SECRET_KEY_PARTS = (
    "password",
    "secret",
    "token",
    "apikey",
    "api_key",
    "authorization",
    "cookie",
    "cvv",
    "cardnumber",
    "card_number",
    "email",
    "phone",
    "mobile",
    "vpa",
)
_SECRET_HEADERS = ("authorization", "x-web-logintoken", "cookie", "x-api-key", "juspay_token")
_MAX_ERROR_CHARS = 500
_REDACTED = "[REDACTED]"


def _redact_error_body(value):
    if isinstance(value, dict):
        return {
            k: (
                _REDACTED
                if any(p in str(k).lower() for p in _SECRET_KEY_PARTS)
                and v is not None
                and not isinstance(v, (dict, list))
                else _redact_error_body(v)
            )
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_redact_error_body(v) for v in value]
    return value


def safe_upstream_error(response) -> str:
    """Upstream error body that is safe to put in an exception message.

    Secret-looking JSON fields and any credential the request carried are
    replaced with ``[REDACTED]``, and the result is truncated.
    """
    if response is None:
        return "Unknown error"
    try:
        text = response.text
    except Exception:
        return "Unknown error"

    try:
        parsed = json.loads(text)
    except ValueError:
        parsed = None
    if isinstance(parsed, (dict, list)):
        redacted = _redact_error_body(parsed)
        if redacted != parsed:
            text = json.dumps(redacted, ensure_ascii=False)

    try:
        for name, value in response.request.headers.items():
            if name.lower() not in _SECRET_HEADERS:
                continue
            for candidate in {value, value.rsplit(" ", 1)[-1]}:
                if len(candidate) >= 8:
                    text = text.replace(candidate, _REDACTED)
    except Exception:
        pass

    if len(text) > _MAX_ERROR_CHARS:
        text = text[:_MAX_ERROR_CHARS] + "...[truncated]"
    return text
