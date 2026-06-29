# Juspay Dashboard MCP

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/) [![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A Model Context Protocol (MCP) server for Juspay's Merchant Dashboard APIs. This module enables AI agents and applications to access merchant dashboard features including gateway management, analytics, reporting, user management, settings, and payment link creation.

## Quick Start

> Connect to the Juspay-hosted remote MCP server — no local setup required.

**Remote MCP Server URL:**
```
https://mcp.juspay.in/dashboard/juspay-dashboard-stream
```

### Web & Desktop Apps (Claude, ChatGPT, Codex, Cursor)

1. Open **Settings → Connectors / MCP Servers / Tools & MCP**
2. Click **Create** / **Add** / **New MCP Server**
3. Paste the server URL: `https://mcp.juspay.in/dashboard/juspay-dashboard-stream`
4. Authenticate via OAuth when prompted

> ChatGPT requires Developer Mode enabled (Settings → Developer Mode) and a Plus/Pro/Team/Enterprise plan.

### CLI

#### Claude Code

```bash
# Step 1: Add the MCP server
claude mcp add --transport http juspay-dashboard https://mcp.juspay.in/dashboard/juspay-dashboard-stream

# Step 2: Start Claude Code
claude
```

Inside Claude Code:
1. Type `/mcp` to see MCP server status
2. Select `juspay-dashboard` from the list
3. Click to authenticate — your browser will open to Juspay Portal
4. Sign in with your Juspay credentials

#### Codex CLI

```bash
# Step 1: Add the MCP server
codex mcp add juspay-dashboard --url https://mcp.juspay.in/dashboard/juspay-dashboard-stream

# Step 2: Authenticate in browser when prompted

# Step 3: Start Codex
codex
```

#### Cursor

Step 1: Add to `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project):

```json
{
  "mcpServers": {
    "juspay-dashboard": {
      "url": "https://mcp.juspay.in/dashboard/juspay-dashboard-stream"
    }
  }
}
```

Step 2: Enable, authenticate, and start:

```bash
agent mcp enable juspay-dashboard
agent mcp login juspay-dashboard
agent
```

### IDEs (VS Code, Windsurf)

#### VS Code

Add to `.vscode/mcp.json` (project) or your user-level `mcp.json`, then open Agent mode in your AI extension and authenticate:

```json
{
  "servers": {
    "juspay-dashboard": {
      "type": "http",
      "url": "https://mcp.juspay.in/dashboard/juspay-dashboard-stream"
    }
  }
}
```

#### Windsurf

Open the MCP Marketplace in the Cascade panel and add the server URL, or add to `~/.codeium/windsurf/mcp_config.json` directly:

```json
{
  "mcpServers": {
    "juspay-dashboard": {
      "serverUrl": "https://mcp.juspay.in/dashboard/juspay-dashboard-stream"
    }
  }
}
```

### Other Clients

For clients that don't support remote HTTP transport, use the Docker image via STDIO. See [How to Generate OAuth Token](#how-to-generate-oauth-token) to get your token first.

```json
{
  "mcpServers": {
    "juspay-dashboard-mcp": {
      "command": "docker",
      "args": [
        "run",
        "--pull=always",
        "--rm",
        "-i",
        "-e",
        "JUSPAY_WEB_LOGIN_TOKEN",
        "-e",
        "JUSPAY_ENV",
        "juspaydotin/juspay-dashboard-mcp:latest"
      ],
      "env": {
        "JUSPAY_WEB_LOGIN_TOKEN": "your_juspay_oauth_token",
        "JUSPAY_ENV": "sandbox"
      }
    }
  }
}
```

---

## Table of Contents

- [Introduction](#introduction)
- [Key Features](#key-features)
- [Getting Started (Local Setup)](#getting-started-local-setup)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [How to Generate OAuth Token](#how-to-generate-oauth-token)
- [Available Tools](#available-tools)
  - [Account \& Session](#account--session)
  - [Gateway Management](#gateway-management)
  - [Order \& Transaction Lookup](#order--transaction-lookup)
  - [Payment Links](#payment-links)
  - [Analytics \& Querying (Q API)](#analytics--querying-q-api)
  - [Reporting](#reporting)
  - [Alerts \& Monitoring](#alerts--monitoring)
  - [Offer Management](#offer-management)
  - [User Management](#user-management)
  - [Settings Management](#settings-management)
  - [API Key Management](#api-key-management)
  - [Surcharge Rules](#surcharge-rules)
  - [Outages](#outages)
  - [Integration Checklist](#integration-checklist)
  - [Documentation (RAG)](#documentation-rag)
- [Troubleshooting](#troubleshooting)
  - [Common Issues](#common-issues)
  - [Debugging Tips](#debugging-tips)
- [License](#license)

## Introduction

The Juspay Dashboard MCP (Model Context Protocol) server provides a standardized interface for AI agents and applications to interact with Juspay's merchant dashboard. This enables AI assistants like Claude to perform complex dashboard operations, analytics queries, and administrative tasks through natural language commands.

## Key Features

- **Gateway Configuration**: View and manage payment gateway configurations
- **Advanced Analytics**: Query transaction data with flexible filters, dimensions, and metrics via the Q API
- **Payment Link Management**: Create and track payment links and autopay/mandate links
- **Reporting & Alerts**: Access configured reports and alert systems
- **User & Settings Management**: Manage dashboard users and merchant settings
- **Integration Monitoring**: Track integration progress and compliance
- **MCP Standard Compliance**: Seamless integration with LLMs and AI agents

## Getting Started (Local Setup)

> Only needed if you want to self-host the MCP server. For most users, the [Quick Start](#quick-start) above is all you need.

### Prerequisites

- Python 3.13+
- Juspay Dashboard Account with Web Login Token
- Nix (recommended) or pip for dependency management

### Installation

```bash
# Clone the repository
git clone https://github.com/juspay/juspay-mcp.git
cd juspay-mcp

# Using Nix (recommended)
nix develop

# Or using pip
pip install -e .
```

## Configuration

### Environment Variables

Create a `.env` file or set these environment variables:

```dotenv
# Required Credentials
JUSPAY_WEB_LOGIN_TOKEN="your_juspay_oauth_token"

# Server Mode (use "DASHBOARD" for dashboard APIs)
JUSPAY_MCP_TYPE="DASHBOARD"

# Environment: "sandbox" (default) or "production"
JUSPAY_ENV="sandbox"

# Optional: Include response schemas in tool descriptions
INCLUDE_RESPONSE_SCHEMA="false"
```

### How to Generate OAuth Token

Watch how to generate your Juspay Dashboard OAuth token:

https://github.com/user-attachments/assets/c8d38149-f3d1-46dc-984c-68f7b4d0ef88

## Available Tools

### Account & Session

| Tool Name | Description |
|-----------|-------------|
| `get_merchant_details` | Returns merchant and user session details for the authenticated caller. Includes merchantId, userId, email, username, tenantAccountId, and caller context. Takes no input - all info is derived from active session. |

### Gateway Management

| Tool Name | Description |
|-----------|-------------|
| `list_configured_gateway` | Lists all payment gateways configured for the merchant with gateway reference IDs, creation/modification dates, configured payment methods, and enabled payment flows. |
| `get_gateway_scheme` | Provides detailed configuration schema for a specific gateway including required/optional fields, supported payment methods, and features (3DS, AFT, etc.). |
| `get_gateway_details` | Returns complete details for a specific configured gateway by `mga_id`. Includes payment methods, EMI plans, mandate/subscription PMs, TPV PMs, and payment flows. |
| `list_gateway_scheme` | Lists all available payment gateways that can be configured on PGCC. Returns gateway names/identifiers without detailed configuration. |
| `get_merchant_gateways_pm_details` | Fetches all gateways with their supported payment methods including Payment Method Type (PMT) for each. This is the only tool that provides PMT information. |

### Order & Transaction Lookup

| Tool Name | Description |
|-----------|-------------|
| `list_orders_v4` | Retrieves orders within a time range with flexible filters. Supports filtering by payment status, order type, and various transaction fields. Requires 'domain' parameter (use 'txnsELS' as default). |
| `get_order_details` | Returns complete details for a specific order ID. Includes automatic retry logic to extract order_id from transaction_id if the order is not found directly. |

### Payment Links

| Tool Name | Description |
|-----------|-------------|
| `list_payment_links_v1` | Retrieves payment links created within a time range. Supports filtering by payment status and order type. |
| `create_payment_link` | Creates a new payment link with specified amount. Supports email/SMS/WhatsApp notifications, EMI options (Standard, Low Cost, No Cost), and various payment method filters. |
| `create_autopay_link` | Creates an autopay/recurring/mandate payment link. Requires amount, mandate_max_amount, mandate_start_date, mandate_end_date, and mandate_frequency. Supports all payment link features plus mandate configuration. |

### Analytics & Querying (Q API)

The Q API provides powerful analytics capabilities. Use these tools in sequence:

| Tool Name | Description |
|-----------|-------------|
| `qapi_info` | **Step 1 of 3**: Discovers valid dimensions and metrics for a domain. Must be called first to obtain field names. Supports domains: kvorders, kvtxns, kvrefundtxns, kvoffers, mandateexecutionkv, fulfillmentorders, sdklogs, kvcustomer, kvmandates, unauthtxns, apirequests. |
| `qapi_field_value_discovery` | **Step 2 of 3**: Looks up valid filter values for specific dimensions. Supports batch lookup with fuzzy matching. Use after qapi_info to discover valid values for filters. |
| `q_api` | **Step 3 of 3**: Executes analytics queries against the Q API. Supports metrics (total_amount, success_rate, success_volume, etc.), dimensions, filters, intervals, and sorting. Powerful for transaction analysis, success rate tracking, and business intelligence. |

**Supported Metrics:**
- `total_amount` / `order_with_transactions_gmv` - GMV/Processed amount
- `success_volume` / `success_rate` - Transaction success metrics
- `avg_ticket_size` - Average order value
- `average_latency` - Transaction latency
- `order_with_transactions` - Total transaction attempts
- And many more...

### Reporting

| Tool Name | Description |
|-----------|-------------|
| `list_report` | Lists all reports configured by the merchant with status, recipients, thresholds, and monitoring intervals. |
| `report_details` | Returns detailed information for a specific report ID including data sources, metrics, dimensions, and filters. |

### Alerts & Monitoring

| Tool Name | Description |
|-----------|-------------|
| `list_alerts` | Retrieves all alerts configured by the merchant with status, recipients, thresholds, and monitoring intervals. |
| `alert_details` | Provides detailed information for a specific alert ID including data source, monitored metrics, and trigger filters. |

### Offer Management

| Tool Name | Description |
|-----------|-------------|
| `list_offers` | Lists all offers configured by the merchant with status, applicable payment methods, offer codes, and validity periods. Supports sorting. |
| `get_offer_details` | Retrieves detailed information for specific offers including eligibility rules, benefit types, and configurations. |

### User Management

| Tool Name | Description |
|-----------|-------------|
| `list_users_v2` | Retrieves a paginated list of users associated with the merchant account. |
| `get_user` | Fetches details for a specific user by user ID including profile information and account details. |

### Settings Management

| Tool Name | Description |
|-----------|-------------|
| `get_general_settings` | Retrieves general configuration settings for the merchant including basic setup and feature enablement. |
| `get_conflict_settings` | Retrieves conflict settings configuration for payment processing. |
| `get_mandate_settings` | Retrieves mandate-related settings for recurring payments and subscriptions. |
| `get_priority_logic_settings` | Fetches all configured priority logic rules for gateway routing with status and complete logic definitions. |
| `get_routing_settings` | Provides success rate-based routing thresholds and downtime-based switching configurations. |
| `get_webhook_settings` | Retrieves webhook configuration settings for event notifications. |

### API Key Management

| Tool Name | Description |
|-----------|-------------|
| `create_api_key` | Generates a new API key for the merchant. Returns the plaintext key ONCE - it cannot be retrieved later. Requires immediate secure storage. |

### Surcharge Rules

| Tool Name | Description |
|-----------|-------------|
| `list_surcharge_rules` | Returns all configured surcharge rules with status and rule definitions. Use to audit when additional fees are applied to transactions. |

### Outages

| Tool Name | Description |
|-----------|-------------|
| `list_outages` | Returns outages within a specified time range with details including start/end times, status, and affected components. Essential for monitoring system health. |

### Integration Checklist

| Tool Name | Description |
|-----------|-------------|
| `integration_monitoring_status` | Tracks integration progress across platforms (Backend, Web, Android, iOS) and products. Shows passed/failed stages, critical vs non-critical items, and action items. Requires platform, product_integrated, merchant_id, and time range (last 45 days max). |
| `integration_platform_metrics` | Retrieves available platforms for a merchant (Android, iOS, Web). Use to determine platform defaults before calling other integration tools. |
| `integration_product_count_metrics` | Analyzes integration usage patterns by product type (Payment Page Signature, Payment Page Session, EC + SDK, EC Only). Requires platform filter. |
| `x_mid_monitoring` | Retrieves X-Mid header validation monitoring data for merchant transactions. Shows PASSED/FAILED validation status for each API endpoint. |

### Documentation (RAG)

| Tool Name | Description |
|-----------|-------------|
| `rag_tool` | Retrieves information from Juspay's product documentation (https://juspay.io/in/docs). Use for questions about Juspay's products, services, APIs, integration guides, or technical documentation. |

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Verify your `WEB_LOGIN_TOKEN` is valid and not expired
   - Ensure you're using the correct environment (sandbox vs production)

2. **Order Not Found in get_order_details**
   - The tool automatically attempts to extract order_id from transaction_id
   - If still failing, verify the order exists in your merchant account

3. **Q API Query Errors**
   - Always call `qapi_info` first to get valid field names
   - Use `qapi_field_value_discovery` to find valid filter values
   - Check that your time interval format is ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)

4. **Integration Checklist Data Not Found**
   - Only last 45 days of data is available
   - Ensure platform and product_integrated values are from the allowed set

### Debugging Tips

- Use `get_merchant_details` to verify your session context
- For Q API queries, start simple and add filters incrementally
- Check server logs for detailed error messages
- Use the RAG tool for documentation questions about Juspay features

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](../LICENSE) file for details.

Copyright 2025 Juspay Technologies Private Limited.
