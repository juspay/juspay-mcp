# Juspay MCP

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

MCP (Model Context Protocol) servers that let AI assistants interact with Juspay's payment APIs and merchant dashboard through natural language.

## Which MCP do you need?

| | [Payments MCP](./juspay_mcp/README.md) | [Dashboard MCP](./juspay_dashboard_mcp/README.md) |
|---|---|---|
| **Use when you want to…** | Process payments, manage orders, handle refunds, work with customers and cards | Configure gateways, query analytics, manage users, view reports, create payment links |
| **Credential required** | API Key + Merchant ID | Dashboard login (OAuth) |
| **Docker image** | `juspaydotin/juspay-mcp:latest` | `juspaydotin/juspay-dashboard-mcp:latest` |
| **Tools include** | `create_order`, `create_txn`, `create_refund`, `upi_collect`, `list_wallets`, … | `q_api`, `juspay_list_configured_gateway`, `create_payment_link`, `juspay_list_orders_v4`, … |
| **Full docs** | [juspay_mcp/README.md](./juspay_mcp/README.md) | [juspay_dashboard_mcp/README.md](./juspay_dashboard_mcp/README.md) |

> You can run both servers simultaneously — see the individual READMEs for setup instructions.

## Prerequisites

- A Juspay merchant account ([sign up](https://sandbox.portal.juspay.in/selfSignUp))
- Docker (recommended for quickest setup)

## Contributing

1. Fork the repository and create a feature branch
2. Make your changes following PEP 8 and adding type annotations where appropriate
3. Add tests for any new functionality
4. Open a pull request with a clear description of the change

```bash
# Set up the development environment (requires Nix)
git clone https://github.com/juspay/juspay-mcp.git
cd juspay-mcp
nix develop

# Run tests
nix run .#test
```

## License

Apache License 2.0. See the [LICENSE](./LICENSE) file for details.

Copyright 2025 Juspay Technologies Private Limited.
