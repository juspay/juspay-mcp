# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from pydantic import Field
from juspay_dashboard_mcp.api_schema.headers import WithHeaders


class JuspayCreateApiKeyPayload(WithHeaders):
    """Generate a new API key for the merchant and store it in an env file.

    The freshly-generated key is written directly into the caller-supplied
    env file and is NEVER returned to the agent — the tool returns only the
    env var name + a masked form. This keeps the plaintext secret out of the
    agent's context and the chat transcript.
    """

    description: str = Field(
        ...,
        description=(
            "Human-readable label for the key (shown in the merchant's API "
            "Keys listing). Keep it short and identifiable, e.g. "
            "'mcp-cli-2026-05'."
        ),
    )
    env_file_path: str = Field(
        ...,
        description=(
            "ABSOLUTE path to the .env file of the project the user is "
            "working in. The generated API key is written here and is NOT "
            "returned to you — reference it afterwards via the environment "
            "variable name this tool returns. The file is created if it does "
            "not exist. If you don't know the path, ask the user or use the "
            "project root's .env (must be an absolute path)."
        ),
    )
    env_var_name: str = Field(
        "JUSPAY_API_KEY",
        description=(
            "Environment variable name to store the key under. Defaults to "
            "JUSPAY_API_KEY. Use a distinct name (e.g. JUSPAY_API_KEY_SANDBOX) "
            "if the project needs more than one."
        ),
    )
