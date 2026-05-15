# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import logging
import os
import subprocess
import tempfile

import httpx

from juspay_dashboard_mcp.api.utils import get_juspay_host_from_api, get_juspay_credentials
from juspay_dashboard_mcp.config import get_common_headers

logger = logging.getLogger(__name__)


def _write_env_var(env_file_path: str, var_name: str, value: str) -> dict:
    """Write `var_name=value` into `env_file_path`, atomically and at mode 0600.

    - Creates the file (and parent dirs) if missing.
    - If a non-comment line for `var_name` already exists, it is replaced in
      place — no duplicate line. Otherwise the line is appended.
    - Every other line in the file is preserved untouched.

    Returns {"created": bool, "updated_in_place": bool}.
    """
    parent = os.path.dirname(env_file_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    created = not os.path.exists(env_file_path)
    existing_lines: list[str] = []
    if not created:
        with open(env_file_path, "r") as f:
            existing_lines = f.read().splitlines()

    new_line = f"{var_name}={value}"
    updated = False
    out_lines: list[str] = []
    for line in existing_lines:
        stripped = line.lstrip()
        if stripped.startswith(f"{var_name}=") and not stripped.startswith("#"):
            out_lines.append(new_line)
            updated = True
        else:
            out_lines.append(line)
    if not updated:
        out_lines.append(new_line)

    content = "\n".join(out_lines) + "\n"

    # Atomic write: temp file in the same dir, then os.replace().
    fd, tmp_path = tempfile.mkstemp(dir=parent or ".", prefix=".env-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        os.chmod(tmp_path, 0o600)
        os.replace(tmp_path, env_file_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
    os.chmod(env_file_path, 0o600)

    return {"created": created, "updated_in_place": updated}


def _gitignore_warning(env_file_path: str) -> str | None:
    """If the env file is inside a git repo but NOT gitignored, return a warning.

    Best-effort: any failure (git missing, not a repo) returns None silently.
    """
    parent = os.path.dirname(env_file_path) or "."
    try:
        inside = subprocess.run(
            ["git", "-C", parent, "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            timeout=5,
        )
        if inside.returncode != 0 or inside.stdout.strip() != b"true":
            return None  # not a git repo — nothing to warn about
        check = subprocess.run(
            ["git", "-C", parent, "check-ignore", env_file_path],
            capture_output=True,
            timeout=5,
        )
        # check-ignore: rc 0 = path IS ignored, rc 1 = NOT ignored.
        if check.returncode == 1:
            return (
                f"{env_file_path} is inside a git repository and is NOT "
                f"gitignored. Add it to .gitignore so the API key is not "
                f"committed."
            )
    except Exception:
        pass
    return None


async def create_api_key_juspay(payload: dict, meta_info: dict = None) -> dict:
    """Generate a new merchant API key and store it in the caller's env file.

    The plaintext key is written to `env_file_path` and is deliberately NOT
    included in the return value — callers reference it via the environment
    variable name instead. The key is also kept out of server logs (this
    handler issues the Portal request directly rather than via `post()`,
    which logs full response bodies).
    """
    env_file_path = payload["env_file_path"]
    env_var_name = (payload.get("env_var_name") or "JUSPAY_API_KEY").strip()

    # Validate the destination BEFORE creating the key — a key is shown only
    # once by Juspay, so we must not mint one we can't store.
    if not os.path.isabs(env_file_path):
        raise ValueError(
            f"env_file_path must be an absolute path; got {env_file_path!r}. "
            "Pass the absolute path to the project's .env file."
        )
    if os.path.isdir(env_file_path):
        raise ValueError(
            f"env_file_path points to a directory, not a file: {env_file_path!r}"
        )
    if not env_var_name or any(c in env_var_name for c in "= \t\n"):
        raise ValueError(
            f"env_var_name must be a valid env variable name; got {env_var_name!r}"
        )

    host = await get_juspay_host_from_api(meta_info=meta_info)
    api_url = f"{host}/api/ec/v1/apiKeys"
    request_payload = {"description": payload["description"]}

    # Issue the request inline (NOT via utils.post) — post() logs the full
    # response body at INFO, which would write the plaintext key into the
    # server log. Headers are built the same way post() builds them.
    juspay_creds = get_juspay_credentials()
    if not juspay_creds and meta_info:
        juspay_creds = meta_info.get("juspay_credentials")
    headers = get_common_headers(request_payload, meta_info, juspay_creds)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(api_url, headers=headers, json=request_payload)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response else "unknown"
            raise Exception(f"Juspay API key creation failed (HTTP {status})") from e
        except Exception as e:
            raise Exception(f"Juspay API key creation failed: {e}") from e

    api_key = data.get("apiKey")
    if not api_key:
        raise Exception("API key creation response did not contain a key.")

    write_info = _write_env_var(env_file_path, env_var_name, api_key)
    warning = _gitignore_warning(env_file_path)

    # Log only non-secret identifiers — never the plaintext key.
    logger.info(
        "API key created (masked=%s, id=%s) and written to %s as %s",
        data.get("maskedApiKey"),
        data.get("id"),
        env_file_path,
        env_var_name,
    )

    result = {
        "status": "written_to_env",
        "env_file": env_file_path,
        "env_var": env_var_name,
        "env_file_created": write_info["created"],
        "updated_in_place": write_info["updated_in_place"],
        "maskedApiKey": data.get("maskedApiKey"),
        "id": data.get("id"),
        "key_status": data.get("status"),
        "scope": data.get("scope"),
        "merchantAccountId": data.get("merchantAccountId"),
        "dateCreated": data.get("dateCreated"),
        "message": (
            f"API key generated and saved to {env_file_path} as "
            f"{env_var_name}. The plaintext key was deliberately NOT returned "
            f"— reference it through the {env_var_name} environment variable. "
            f"Juspay shows the key only once, so it cannot be retrieved again "
            f"via this tool."
        ),
    }
    if warning:
        result["warning"] = warning
    return result
