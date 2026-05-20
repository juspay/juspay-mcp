# Juspay Dashboard MCP

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/) [![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A Model Context Protocol (MCP) server for Juspay's Merchant Dashboard APIs. This module enables AI agents and applications to access merchant dashboard features including gateway management, analytics, reporting, user management, settings, and payment link creation.

## Table of Contents

- [Juspay Dashboard MCP](#juspay-dashboard-mcp)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Key Features](#key-features)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Quick Start](#quick-start)
  - [Usage with Claude and AI Assistants](#usage-with-claude-and-ai-assistants)
  - [Configuration](#configuration)
    - [How to Generate OAuth Token](#how-to-generate-oauth-token)
    - [Environment Variables](#environment-variables)
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

## Getting Started

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

### Quick Start

1. Set up your environment variables (see [Configuration](#configuration))
2. Start the server:

```bash
# Set to Dashboard mode
export JUSPAY_MCP_TYPE=DASHBOARD

# Using Nix
nix run

# Standard Python
python ./juspay_mcp/main.py

# Or run Docker
docker run -it juspay-dashboard-mcp:latest
```

## Usage with Claude and AI Assistants

Add the following to your `claude_desktop_config.json`:

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
        "JUSPAY_WEB_LOGIN_TOKEN": "your_juspay_web_login_token",
        "JUSPAY_ENV": "sandbox"
      }
    }
  }
}
```

Replace `your_juspay_web_login_token` with your actual dashboard login token.

## Configuration

### How to Generate OAuth Token

Watch how to generate your Juspay Dashboard OAuth token:

https://github.com/user-attachments/assets/c8d38149-f3d1-46dc-984c-68f7b4d0ef88
### Environment Variables

Create a `.env` file or set these environment variables:

```dotenv
# Required Credentials
JUSPAY_WEB_LOGIN_TOKEN="your_juspay_web_login_token"

# Server Mode (use "DASHBOARD" for dashboard APIs)
JUSPAY_MCP_TYPE="DASHBOARD"

# Environment: "sandbox" (default) or "production"
JUSPAY_ENV="sandbox"

# Optional: Include response schemas in tool descriptions
INCLUDE_RESPONSE_SCHEMA="false"
```

## Available Tools

### Account & Session

| Tool Name | Description |
|-----------|-------------|
| `juspay_get_merchant_details` | Returns merchant and user session details for the authenticated caller. Includes merchantId, userId, email, username, tenantAccountId, and caller context. Takes no input - all info is derived from active session. |

### Gateway Management

| Tool Name | Description |
|-----------|-------------|
| `juspay_list_configured_gateway` | Lists all payment gateways configured for the merchant with gateway reference IDs, creation/modification dates, configured payment methods, and enabled payment flows. |
| `juspay_get_gateway_scheme` | Provides detailed configuration schema for a specific gateway including required/optional fields, supported payment methods, and features (3DS, AFT, etc.). |
| `juspay_get_gateway_details` | Returns complete details for a specific configured gateway by `mga_id`. Includes payment methods, EMI plans, mandate/subscription PMs, TPV PMs, and payment flows. |
| `juspay_list_gateway_scheme` | Lists all available payment gateways that can be configured on PGCC. Returns gateway names/identifiers without detailed configuration. |
| `juspay_get_merchant_gateways_pm_details` | Fetches all gateways with their supported payment methods including Payment Method Type (PMT) for each. This is the only tool that provides PMT information. |

### Order & Transaction Lookup

| Tool Name | Description |
|-----------|-------------|
| `juspay_list_orders_v4` | Retrieves orders within a time range with flexible filters. Supports filtering by payment status, order type, and various transaction fields. Requires 'domain' parameter (use 'txnsELS' as default). |
| `juspay_get_order_details` | Returns complete details for a specific order ID. Includes automatic retry logic to extract order_id from transaction_id if the order is not found directly. |

### Payment Links

| Tool Name | Description |
|-----------|-------------|
| `juspay_list_payment_links_v1` | Retrieves payment links created within a time range. Supports filtering by payment status and order type. |
| `create_payment_link_juspay` | Creates a new payment link with specified amount. Supports email/SMS/WhatsApp notifications, EMI options (Standard, Low Cost, No Cost), and various payment method filters. |
| `create_autopay_link_juspay` | Creates an autopay/recurring/mandate payment link. Requires amount, mandate_max_amount, mandate_start_date, mandate_end_date, and mandate_frequency. Supports all payment link features plus mandate configuration. |

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
| `juspay_list_report` | Lists all reports configured by the merchant with status, recipients, thresholds, and monitoring intervals. |
| `juspay_report_details` | Returns detailed information for a specific report ID including data sources, metrics, dimensions, and filters. |

### Alerts & Monitoring

| Tool Name | Description |
|-----------|-------------|
| `juspay_list_alerts` | Retrieves all alerts configured by the merchant with status, recipients, thresholds, and monitoring intervals. |
| `juspay_alert_details` | Provides detailed information for a specific alert ID including data source, monitored metrics, and trigger filters. |

### Offer Management

| Tool Name | Description |
|-----------|-------------|
| `juspay_list_offers` | Lists all offers configured by the merchant with status, applicable payment methods, offer codes, and validity periods. Supports sorting. |
| `juspay_get_offer_details` | Retrieves detailed information for specific offers including eligibility rules, benefit types, and configurations. |

### User Management

| Tool Name | Description |
|-----------|-------------|
| `juspay_list_users_v2` | Retrieves a paginated list of users associated with the merchant account. |
| `juspay_get_user` | Fetches details for a specific user by user ID including profile information and account details. |

### Settings Management

| Tool Name | Description |
|-----------|-------------|
| `juspay_get_general_settings` | Retrieves general configuration settings for the merchant including basic setup and feature enablement. |
| `juspay_get_conflict_settings` | Retrieves conflict settings configuration for payment processing. |
| `juspay_get_mandate_settings` | Retrieves mandate-related settings for recurring payments and subscriptions. |
| `juspay_get_priority_logic_settings` | Fetches all configured priority logic rules for gateway routing with status and complete logic definitions. |
| `juspay_get_routing_settings` | Provides success rate-based routing thresholds and downtime-based switching configurations. |
| `juspay_get_webhook_settings` | Retrieves webhook configuration settings for event notifications. |

### API Key Management

| Tool Name | Description |
|-----------|-------------|
| `juspay_create_api_key` | Generates a new API key for the merchant. Returns the plaintext key ONCE - it cannot be retrieved later. Requires immediate secure storage. |

### Surcharge Rules

| Tool Name | Description |
|-----------|-------------|
| `juspay_list_surcharge_rules` | Returns all configured surcharge rules with status and rule definitions. Use to audit when additional fees are applied to transactions. |

### Outages

| Tool Name | Description |
|-----------|-------------|
| `list_outages_juspay` | Returns outages within a specified time range with details including start/end times, status, and affected components. Essential for monitoring system health. |

### Integration Checklist

| Tool Name | Description |
|-----------|-------------|
| `juspay_integration_monitoring_status` | Tracks integration progress across platforms (Backend, Web, Android, iOS) and products. Shows passed/failed stages, critical vs non-critical items, and action items. Requires platform, product_integrated, merchant_id, and time range (last 45 days max). |
| `juspay_integration_platform_metrics` | Retrieves available platforms for a merchant (Android, iOS, Web). Use to determine platform defaults before calling other integration tools. |
| `juspay_integration_product_count_metrics` | Analyzes integration usage patterns by product type (Payment Page Signature, Payment Page Session, EC + SDK, EC Only). Requires platform filter. |
| `juspay_x_mid_monitoring` | Retrieves X-Mid header validation monitoring data for merchant transactions. Shows PASSED/FAILED validation status for each API endpoint. |

### Documentation (RAG)

| Tool Name | Description |
|-----------|-------------|
| `rag_tool_juspay` | Retrieves information from Juspay's product documentation (https://juspay.io/in/docs). Use for questions about Juspay's products, services, APIs, integration guides, or technical documentation. |

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Verify your `JUSPAY_WEB_LOGIN_TOKEN` is valid and not expired
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

- Use `juspay_get_merchant_details` to verify your session context
- For Q API queries, start simple and add filters incrementally
- Check server logs for detailed error messages
- Use the RAG tool for documentation questions about Juspay features

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](../LICENSE) file for details.

Copyright 2025 Juspay Technologies Private Limited.
