# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from pydantic import BaseModel


class WithHeaders(BaseModel):
    """Tool payload with no arguments of its own.

    tenant_id / cookie / x-source-id are set from the request context, never by
    the tool call (see get_common_headers).
    """
