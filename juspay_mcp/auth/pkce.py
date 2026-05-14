# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt
"""PKCE S256 helpers (RFC 7636).

We only support the S256 challenge method — the plain method is forbidden by
OAuth 2.1 and the MCP authorization profile requires S256 when technically
capable.
"""

from __future__ import annotations

import base64
import hashlib


def compute_s256_challenge(verifier: str) -> str:
    """Compute the base64url(no-padding) SHA-256 of `verifier`."""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def validate_s256(verifier: str, challenge: str) -> bool:
    return compute_s256_challenge(verifier) == challenge
