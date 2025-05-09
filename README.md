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

| Tool Name            | Description                                     |
| -------------------- | ----------------------------------------------- |
| `session_api_juspay` | Creates a new Juspay session for a given order. |
| `create_txn_juspay`  | Creates an order and processes payment          |
