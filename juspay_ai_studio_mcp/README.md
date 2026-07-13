# Juspay PP Studio AI MCP

MCP package for controlling the PP Studio AI session service.

## Tools

| Tool Name | Description |
|-----------|-------------|
| `create_session` | Create a new PP Studio AI session for a merchant payment-page request. |
| `resume_session` | Resume a waiting/completed/failed/stopped session with a user reply or follow-up. |
| `list_session` | List PP Studio AI sessions, optionally filtered by status or client ID. |
| `get_session` | Fetch full session details, transcript, runs, events, state, and result. |
| `stop_session` | Interrupt a running or queued session and move it into a follow-up state. |
| `payment_page_link` | Return the review URL for the generated live payment-page preview. |
| `download_configs` | Return the config zip download URL for a session. |

## Environment

```dotenv
JUSPAY_MCP_TYPE="PP_AI_STUDIO"
PP_AI_STUDIO_BASE_URL="http://localhost:8001"
PP_AI_STUDIO_API_KEY="your_api_key_or_dashboard_token"
```

Fallback token variables are also accepted:

```dotenv
PP_AI_STUDIO_TOKEN="your_token"
JUSPAY_AI_STUDIO_TOKEN="your_token"
JUSPAY_WEB_LOGIN_TOKEN="your_token"
```
