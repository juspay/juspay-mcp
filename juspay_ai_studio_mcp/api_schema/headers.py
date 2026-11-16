# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from pydantic import BaseModel, ConfigDict


class WithHeaders(BaseModel):
    """Tool payload with no arguments of its own."""

    model_config = ConfigDict(populate_by_name=True)
