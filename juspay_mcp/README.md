# Juspay Payments MCP

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/) [![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A Model Context Protocol (MCP) server for Juspay's Core Payment APIs. This module enables AI agents and applications to perform payment processing operations including order management, transactions, refunds, customer management, card operations, and UPI payments.

## Table of Contents

- [Introduction](#introduction)
- [Key Features](#key-features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Quick Start](#quick-start)
- [Usage with Claude and AI Assistants](#usage-with-claude-and-ai-assistants)
- [Configuration](#configuration)
- [Available Tools](#available-tools)
  - [Order Management](#order-management)
  - [Payment Sessions](#payment-sessions)
  - [Transaction Processing](#transaction-processing)
  - [Refund Operations](#refund-operations)
  - [Customer Management](#customer-management)
  - [Card Management](#card-management)
  - [UPI Payments](#upi-payments)
  - [Offers](#offers)
  - [Wallets](#wallets)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Introduction

The Juspay Payments MCP (Model Context Protocol) server provides a standardized interface for AI agents and applications to interact with Juspay's core payment processing infrastructure. This enables AI assistants like Claude to perform complex payment operations through natural language commands.

## Key Features

- **Complete Payment Lifecycle**: Create orders, process payments, handle refunds, and track order status
- **Multi-Payment Method Support**: Cards, UPI (Collect & Intent), Wallets, and more
- **Customer & Card Management**: Create customers, store cards securely, manage payment methods
- **Offer Integration**: List and apply promotional offers during checkout
- **MCP Standard Compliance**: Seamless integration with LLMs and AI agents via Model Context Protocol

## Getting Started

### Prerequisites

- Python 3.13+
- Juspay Merchant Account with API credentials
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
# Using Nix
nix run

# Standard Python
python ./juspay_mcp/main.py

# STDIO mode
python ./juspay_mcp/stdio.py
```

## Usage with Claude and AI Assistants

Add the following to your `claude_desktop_config.json`:

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
        "JUSPAY_ENV": "sandbox"
      }
    }
  }
}
```

Replace `your_juspay_api_key` and `your_juspay_merchant_id` with your actual credentials.

## Configuration

Create a `.env` file or set these environment variables:

```dotenv
# Required Credentials
JUSPAY_API_KEY="your_juspay_api_key"
JUSPAY_MERCHANT_ID="your_juspay_merchant_id"

# Server Mode (use "CORE" for payments)
JUSPAY_MCP_TYPE="CORE"

# Environment: "sandbox" (default) or "production"
JUSPAY_ENV="sandbox"

# Optional: Include response schemas in tool descriptions
INCLUDE_RESPONSE_SCHEMA="false"
```

## Available Tools

### Order Management

| Tool Name | Description |
|-----------|-------------|
| `create_order_juspay` | Creates a new order in the Juspay payment system. Required before initiating any payment. |
| `update_order_juspay` | Updates an existing order with new details (amount, metadata, etc.). |
| `order_status_api_juspay` | Retrieves comprehensive order status including payment details, transaction info, refund status, and gateway responses. Essential for verifying payment completion. |
| `order_fulfillment_sync_juspay` | Updates the fulfillment status of an order after successful payment (e.g., shipped, delivered). |

### Payment Sessions

| Tool Name | Description |
|-----------|-------------|
| `session_api_juspay` | Creates a new Juspay session for a given order. Used to initialize the payment flow and obtain a session token for client-side SDK integration. |

### Transaction Processing

| Tool Name | Description |
|-----------|-------------|
| `create_txn_juspay` | Creates an order and processes payment in a single API call. Combines order creation and payment initiation for streamlined checkout. |
| `create_moto_txn_juspay` | Creates an order with MOTO (Mail Order/Telephone Order) authentication. Used for card-not-present transactions where the customer provides card details over phone or email. |

### Refund Operations

| Tool Name | Description |
|-----------|-------------|
| `create_refund_juspay` | Initiates a refund for a specific order using the `order_id`. Supports full and partial refunds. |
| `create_txn_refund_juspay` | Initiates a refund based on transaction ID instead of order ID. Useful when multiple transactions exist for an order. |

### Customer Management

| Tool Name | Description |
|-----------|-------------|
| `create_customer_juspay` | Creates a new customer profile in Juspay with contact details and metadata. |
| `get_customer_juspay` | Retrieves customer details including email, mobile number, name, and creation dates. Supports fetching client auth token for SDK integration. |
| `update_customer_juspay` | Updates an existing customer's information (email, phone, name, etc.). |

### Card Management

| Tool Name | Description |
|-----------|-------------|
| `add_card_juspay` | Adds a new card to Juspay's secure locker for a customer. Enables saved card payments. |
| `list_cards_juspay` | Lists all cards stored for a customer. Returns tokens and metadata including brand, issuer, expiry, last four digits, and tokenization status. |
| `delete_card_juspay` | Deletes a saved card from the Juspay system. |
| `update_card_juspay` | Updates details for a saved card (e.g., expiry date, nickname). |
| `get_card_info_juspay` | Retrieves card information using BIN (Bank Identification Number). Returns card type, brand, bank, country, and eligibility for features like ATM PIN, Mandate, and tokenization. Accepts 6-9 digit BINs. |
| `get_bin_list_juspay` | Retrieves list of eligible BINs for a specific authentication type ("OTP" or "VIES"). Useful for filtering cards based on authentication support. |
| `get_saved_payment_methods` | Fetches a customer's saved payment methods including VPAs, Cards, and Wallets. Enables faster checkout with one-click payments. |

### UPI Payments

| Tool Name | Description |
|-----------|-------------|
| `upi_collect` | Creates a UPI Collect transaction. Sends a payment request to the customer's UPI ID/VPA which they approve in their UPI app. |
| `verify_vpa` | Verifies if a UPI Virtual Payment Address (VPA) is valid before initiating a transaction. Returns VPA holder name if valid. |
| `upi_intent` | Creates a UPI Intent transaction for payment using UPI apps. Generates a UPI intent link that opens the customer's preferred UPI app directly. |

### Offers

| Tool Name | Description |
|-----------|-------------|
| `list_offers_juspay` | Lists all active offers based on merchant configuration. Returns offer descriptions, eligibility rules, discount/cashback calculations, applicable payment methods, and eligible products. Supports optional coupon code validation. |

### Wallets

| Tool Name | Description |
|-----------|-------------|
| `list_wallets` | Lists all wallets for a customer (linked and unlinked). Returns wallet names, tokens, balance information, and payment method breakdown. Supports direct debit for linked wallets. |

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Verify your `JUSPAY_API_KEY` is correct and has appropriate permissions
   - Ensure you're using the right environment (sandbox vs production)

2. **Order Not Found**
   - Confirm the `order_id` exists in your Juspay account
   - Check if you're querying the correct environment

3. **Invalid Card BIN**
   - Card BIN must be 6-9 digits
   - Ensure the BIN belongs to a supported card network

4. **UPI VPA Verification Failed**
   - VPA format should be `username@handle` (e.g., `user@upi`)
   - Some VPAs may be temporarily unavailable for verification

### Debugging Tips

- Check server logs for detailed error messages
- Use `order_status_api_juspay` to verify order state before operations
- In sandbox mode, use test credentials and test card numbers

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](../LICENSE) file for details.

Copyright 2025 Juspay Technologies Private Limited.
