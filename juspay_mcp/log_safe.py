# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

"""Helpers for writing log lines that never carry tokens, IDs or PII."""

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
