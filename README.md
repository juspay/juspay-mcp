# Juspay MCP Tools

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/) [![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A Model Context Protocol (MCP) server to interact with Juspay APIs. This package enables AI agents and other tools to leverage Juspay's capabilities for core payment processing and merchant dashboard interactions.

## Table of Contents

- [Juspay MCP Tools](#juspay-mcp-tools)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Key Features](#key-features)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Quick Start](#quick-start)
  - [Usage with Claude and Other AI Assistants](#usage-with-claude-and-other-ai-assistants)
    - [Juspay Payments MCP](#juspay-payments-mcp)
    - [Juspay Dashboard MCP](#juspay-dashboard-mcp)
  - [Configuration](#configuration)
    - [Environment Variables](#environment-variables)
    - [Running Both Core and Dashboard APIs](#running-both-core-and-dashboard-apis)
  - [Architecture](#architecture)
  - [Available Tools](#available-tools)
    - [Juspay Payments Tools](#juspay-payments-tools)
      - [Order Management](#order-management)
      - [Payment Processing](#payment-processing)
      - [Customer Management](#customer-management)
      - [Card Management](#card-management)
      - [UPI Payments](#upi-payments)
      - [Offers and Wallets](#offers-and-wallets)
    - [Juspay Dashboard Tools](#juspay-dashboard-tools)
      - [Gateway Management](#gateway-management)
      - [Reporting](#reporting)
      - [User Management](#user-management)
      - [Settings Management](#settings-management)
      - [Advanced Querying](#advanced-querying)
  - [Troubleshooting](#troubleshooting)
    - [Common Issues](#common-issues)
    - [Debugging Tips](#debugging-tips)
  - [Contributing](#contributing)
    - [Development Environment](#development-environment)
  - [License](#license)

## Introduction

The Juspay MCP (Model Context Protocol) server provides a standardized interface for AI agents and applications to interact with Juspay's payment processing infrastructure and merchant dashboard.

Model Context Protocol is an emerging standard for enabling AI models and agents to interact with external tools and APIs in a structured, discoverable way. This allows AI assistants like Claude to perform complex payment operations and dashboard management tasks through natural language.

## Key Features

- **Dual API Coverage:** Provides tools for both Juspay's Core Payment APIs and Dashboard APIs.

- **MCP Integration:** Enables seamless integration with LLMs and AI agents via the Model Context Protocol.

- **Configurable Modes:** Run the server specifically for Core APIs or Dashboard APIs using an environment variable.

## Getting Started

### Prerequisites

- Python 3.13+
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/juspay/juspay-mcp.git
cd juspay-mcp

# 2. Install dependencies
pip install -e .  # For development (editable install)
# or
pip install .     # For standard installation
```

### Quick Start

1. Set up your environment variables (see Configuration section)
2. Start the server:

```bash
# For standard HTTP server
python main.py

# For STDIO mode (used with direct integrations)
python stdio.py
```

## Usage with Claude and Other AI Assistants

### Juspay Payments MCP

Add the following to your `claude_desktop_config.json` or equivalent configuration:

```json
{
  "mcpServers": {
    "juspay-mcp": {
      "command": "docker",
      "args": [
        "run",
        "--pull=always",
        "--rm",
        "-i",
        "-e",
        "JUSPAY_API_KEY",
        "-e",
        "JUSPAY_MERCHANT_ID",
        "-e",
        "JUSPAY_ENV",
        "juspaydotin/juspay-mcp:latest"
      ],
      "env": {
        "JUSPAY_API_KEY": "your_juspay_api_key",
        "JUSPAY_MERCHANT_ID": "your_juspay_merchant_id",
        "JUSPAY_ENV": "sandbox | production"
      }
    }
  }
}
```

Please replace the `your_juspay_api_key` and `your_juspay_merchant_id` with your api key and merchant id.
Default values for `JUSPAY_ENV` is `sandbox`.

### Juspay Dashboard MCP

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
        "JUSPAY_ENV": "sandbox | production"
      }
    }
  }
}
```

Please replace the `your_juspay_web_login_token` with your dashboard login token.

## Configuration

### Environment Variables

Create a `.env` file in the project root or set these variables in your environment:

```dotenv
# --- Required Juspay Credentials for Payments ---
JUSPAY_API_KEY="your_juspay_api_key"
JUSPAY_MERCHANT_ID="your_juspay_merchant_id"

# --- Required Juspay Credentials for Dashboard ---
JUSPAY_WEB_LOGIN_TOKEN="your_juspay_web_login_token"

# --- Required Server Mode ---
# Determines which set of tools the server will expose.
# Options: "CORE" (default), "DASHBOARD"
JUSPAY_MCP_TYPE="CORE"

# --- Optional: Juspay Environment ---
# Set to "production" to use live API endpoints.
# Options: "sandbox" (default), "production"
JUSPAY_ENV="sandbox"

# --- Optional: Include Response Schemas ---
# When set to "true", tool descriptions will include JSON schemas for responses
# Options: "false" (default), "true"
INCLUDE_RESPONSE_SCHEMA="false"

# --- Optional: Ignoring the tools in list ---
# When set with list of tools those will be ignored in dashboard list_tools.
DASHBOARD_TOOL_IGNORE_LIST='["q_api"]'
```

### Running Both Core and Dashboard APIs

The server runs _either_ Core _or_ Dashboard tools per instance, controlled by `JUSPAY_MCP_TYPE`. To access both sets simultaneously, run two separate server instances with different `JUSPAY_MCP_TYPE` values and ports:

```bash
# Terminal 1: Run Core API server
JUSPAY_MCP_TYPE=CORE python main.py --port 8000

# Terminal 2: Run Dashboard API server
JUSPAY_MCP_TYPE=DASHBOARD python main.py --port 8001
```

## Architecture

The Juspay MCP server consists of two primary modules:

1. **juspay_mcp**: Handles core payment processing functionality including orders, transactions, refunds, customers, cards, UPI, and more.

2. **juspay_dashboard_mcp**: Provides access to merchant dashboard features like gateway management, reporting, user management, and settings.

Each module:

- Defines API schemas in `api_schema/` directory
- Implements API handlers in `api/` directory
- Exposes tools via the tools.py file
- Manages configuration in config.py

The MCP server translates AI assistant requests into properly formatted API calls to Juspay's backend services, handling authentication, request formatting, and response parsing automatically.

## Available Tools

### Juspay Payments Tools

#### Order Management

| Tool Name                       | Description                                                           |
| ------------------------------- | --------------------------------------------------------------------- |
| `create_order_juspay`           | Creates a new order in Juspay payment system.                         |
| `update_order_juspay`           | Updates an existing order in Juspay.                                  |
| `order_status_api_juspay`       | Retrieves the status of a specific Juspay order using its `order_id`. |
| `order_fulfillment_sync_juspay` | Updates the fulfillment status of a Juspay order.                     |

#### Payment Processing

| Tool Name                  | Description                                                             |
| -------------------------- | ----------------------------------------------------------------------- |
| `session_api_juspay`       | Creates a new Juspay session for a given order.                         |
| `create_txn_juspay`        | Creates an order and processes payment in a single API call.            |
| `create_moto_txn_juspay`   | Creates an order with MOTO (Mail Order/Telephone Order) authentication. |
| `create_refund_juspay`     | Initiates a refund for a specific Juspay order using its `order_id`.    |
| `create_txn_refund_juspay` | Initiates a refund based on transaction ID (instead of order ID).       |

#### Customer Management

| Tool Name                | Description                                                       |
| ------------------------ | ----------------------------------------------------------------- |
| `create_customer_juspay` | Creates a new customer in Juspay with the provided details.       |
| `get_customer_juspay`    | Retrieves customer details using the Juspay customer ID.          |
| `update_customer_juspay` | Updates an existing customer in Juspay with the provided details. |

#### Card Management

| Tool Name                   | Description                                                                   |
| --------------------------- | ----------------------------------------------------------------------------- |
| `add_card_juspay`           | Adds a new card to the Juspay system for a customer.                          |
| `list_cards_juspay`         | Retrieves all stored cards for a specific customer.                           |
| `delete_card_juspay`        | Deletes a saved card from the Juspay system.                                  |
| `update_card_juspay`        | Updates details for a saved card.                                             |
| `get_card_info_juspay`      | Retrieves information about a specific card BIN (Bank Identification Number). |
| `get_bin_list_juspay`       | Retrieves a list of eligible BINs for a specific authentication type.         |
| `get_saved_payment_methods` | Retrieves a customer's saved payment methods.                                 |

#### UPI Payments

| Tool Name     | Description                                                             |
| ------------- | ----------------------------------------------------------------------- |
| `upi_collect` | Creates a UPI Collect transaction for requesting payment from a UPI ID. |
| `verify_vpa`  | Verifies if a UPI Virtual Payment Address (VPA) is valid.               |
| `upi_intent`  | Creates a UPI Intent transaction for payment using UPI apps.            |

#### Offers and Wallets

| Tool Name                       | Description                                                         |
| ------------------------------- | ------------------------------------------------------------------- |
| `list_offers_juspay`            | Lists available offers for a given order with optional coupon code. |
| `get_offer_order_status_juspay` | Retrieves the status of an order along with offer details.          |
| `list_wallets`                  | Fetches all wallets linked to the given customer.                   |

### Juspay Dashboard Tools

#### Gateway Management

| Tool Name                                 | Description                                                                           |
| ----------------------------------------- | ------------------------------------------------------------------------------------- |
| `juspay_list_configured_gateway`          | Gets all configured gateways for the merchant.                                        |
| `juspay_get_gateway_scheme`               | Provides detailed configuration info for a gateway (fields, payment methods).         |
| `juspay_get_gateway_details`              | Returns detailed information about a specific configured gateway (`mga_id` required). |
| `juspay_list_gateway_scheme`              | Returns a list of all available payment gateways that can be configured.              |
| `juspay_gateway_downtime`                 | Retrieves downtime information for a gateway (`order_id` required).                   |
| `juspay_get_merchant_gateways_pm_details` | Fetches all gateways and their supported payment methods for the merchant.            |

#### Reporting

| Tool Name                      | Description                                                            |
| ------------------------------ | ---------------------------------------------------------------------- |
| `juspay_report_details`        | Returns detailed information for a specific report ID.                 |
| `juspay_list_report`           | Lists all reports configured by the merchant.                          |
| `juspay_list_orders_v4`        | Retrieves orders within a time range (dashboard perspective).          |
| `juspay_get_order_details`     | Returns complete details for a given order ID (dashboard perspective). |
| `juspay_list_payment_links_v1` | Retrieves payment links created within a time range.                   |

#### User Management

| Tool Name                 | Description                                                                     |
| ------------------------- | ------------------------------------------------------------------------------- |
| `juspay_get_user`         | Fetches details for a specific user by user ID.                                 |
| `juspay_list_users_v2`    | Retrieves a list of users associated with a merchant, with optional pagination. |

#### Settings Management

| Tool Name                            | Description                                                       |
| ------------------------------------ | ----------------------------------------------------------------- |
| `juspay_get_conflict_settings`       | Retrieves conflict settings configuration for payment processing. |
| `juspay_get_general_settings`        | Retrieves general configuration settings for the merchant.        |
| `juspay_get_mandate_settings`        | Retrieves mandate-related settings for recurring payments.        |
| `juspay_get_priority_logic_settings` | Fetches all configured priority logic rules.                      |
| `juspay_get_routing_settings`        | Provides details of success rate-based routing thresholds.        |
| `juspay_get_webhook_settings`        | Retrieves webhook configuration settings for the merchant.        |
| `juspay_list_surcharge_rules`        | Returns a list of all configured surcharge rules.                 |

#### Advanced Querying

| Tool Name | Description                                                                           |
| --------- | ------------------------------------------------------------------------------------- |
| `q_api`   | Generic Query API for various dashboard data domains (refer to q_api.py for details). |

## Troubleshooting

### Common Issues

1. **Authentication Failures**

   - Ensure your API keys are correct and have appropriate permissions
   - Verify you're using the right environment (sandbox/production)

2. **Request Validation Errors**

   - Check that all required fields are present in your request
   - Validate format of values (e.g., proper phone number format, valid email)

3. **Connection Issues**
   - Check network connectivity
   - Verify firewall settings allow outbound connections to Juspay endpoints

### Debugging Tips

1. Inspect the server logs for error messages and request/response details.

2. For MCP communication issues, verify that your AI assistant platform is correctly configured to send and receive MCP-formatted messages.

## Contributing

We welcome contributions to the Juspay MCP server! Here's how you can contribute:

1. **Fork the repository** and create your feature branch

   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make your changes** and ensure they follow our coding standards

   - Use type annotations where appropriate
   - Add docstrings to new functions and classes
   - Follow PEP 8 style guidelines

3. **Add tests** for any new functionality

4. **Submit a pull request** with a clear description of the changes and their benefits

### Development Environment

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](./LICENSE) file for the full license text.

Copyright 2025 Juspay Technologies Private Limited.

