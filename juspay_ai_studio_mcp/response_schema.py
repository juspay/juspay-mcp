# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

session_summary_response_schema = {
    "type": "object",
    "properties": {
        "session_id": {"type": "string"},
        "status": {"type": "string"},
        "client_id": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "created_by": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "platforms": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "model": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "requirement": {"type": "string"},
        "current_question": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "final_output": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "last_error": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "run_count": {"type": "integer"},
        "created_at": {"type": "string"},
        "updated_at": {"type": "string"},
        "completed_at": {"anyOf": [{"type": "string"}, {"type": "null"}]},
    },
}

session_list_response_schema = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": session_summary_response_schema,
        },
        "total": {"type": "integer"},
    },
}

session_detail_response_schema = {
    "type": "object",
    "properties": {
        **session_summary_response_schema["properties"],
        "agent_session_id": {"type": "string"},
        "state": {},
        "messages": {"type": "array"},
        "runs": {"type": "array"},
        "events": {"type": "array"},
    },
}

worker_health_response_schema = {
    "type": "object",
    "properties": {
        "enabled": {"type": "boolean"},
        "started": {"type": "boolean"},
        "stopped": {"type": "boolean"},
        "worker_id": {"type": "string"},
        "max_concurrent": {"type": "integer"},
        "wake_pending": {"type": "boolean"},
        "in_flight_session_ids": {"type": "array", "items": {"type": "string"}},
        "queue": {"type": "object"},
    },
}

payment_page_link_response_schema = {
    "type": "object",
    "properties": {
        "session_id": {"type": "string"},
        "review_url": {"type": "string"},
        "payment_page_url": {"type": "string"},
        "preview_bootstrap_url": {"type": "string"},
        "config_version_url": {"type": "string"},
    },
}

download_configs_response_schema = {
    "type": "object",
    "properties": {
        "session_id": {"type": "string"},
        "config_zip_url": {"type": "string"},
        "download_url": {"type": "string"},
        "config_version": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "warning": {"type": "string"},
    },
}
