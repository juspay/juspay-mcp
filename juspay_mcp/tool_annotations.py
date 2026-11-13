# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from __future__ import annotations

from collections.abc import Iterable

import mcp.types as types

READ_ONLY = types.ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
)

WRITE = types.ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=True,
    idempotentHint=False,
    openWorldHint=True,
)


def apply_annotations(tools: list[dict], read_only_tools: Iterable[str]) -> None:
    """Mark listed tools READ_ONLY and every other tool WRITE."""
    read_only = set(read_only_tools)
    unknown = read_only - {tool["name"] for tool in tools}
    if unknown:
        raise ValueError(f"READ_ONLY_TOOLS lists unregistered tools: {sorted(unknown)}")
    for tool in tools:
        if tool.get("annotations") is None:
            tool["annotations"] = READ_ONLY if tool["name"] in read_only else WRITE
