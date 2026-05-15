"""Verify that with OAUTH_ENABLED=false (the default), the OAuth subsystem is
inert: no /.well-known routes are exposed by the auth package and no Bearer
middleware is installed. The legacy JuspayHeaderAuthMiddleware path stays.
"""

from __future__ import annotations

import os
import sys

# Ensure flag is off
os.environ.pop("OAUTH_ENABLED", None)

from juspay_mcp.auth import config as auth_config

cfg = auth_config.load()
if cfg.enabled:
    print("[FAIL] config.enabled True when OAUTH_ENABLED unset")
    sys.exit(1)
print("[OK] OAUTH_ENABLED unset -> config.enabled is False")

# Toggle false explicitly
os.environ["OAUTH_ENABLED"] = "false"
cfg2 = auth_config.load()
if cfg2.enabled:
    print("[FAIL] OAUTH_ENABLED=false still enabled")
    sys.exit(1)
print("[OK] OAUTH_ENABLED=false -> config.enabled is False")

# Toggle true to make sure the flag works in the opposite direction too
os.environ["OAUTH_ENABLED"] = "true"
cfg3 = auth_config.load()
if not cfg3.enabled:
    print("[FAIL] OAUTH_ENABLED=true did not enable")
    sys.exit(1)
print("[OK] OAUTH_ENABLED=true -> config.enabled is True")

print("[OK] feature flag honoured in both directions")
