# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import json
import os


def make_api_config(name, description, model, handler, response_schema=None):
    desc = description.strip()
    include_response_schema = os.getenv("INCLUDE_RESPONSE_SCHEMA")
    if include_response_schema == "true" and response_schema:
        desc += f"\nReturns response following this schema:\n{json.dumps(response_schema, indent=2)}"
    return {
        "name": name,
        "description": desc,
        "model": model,
        "schema": model.model_json_schema(),
        "handler": handler,
    }

