# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

"""Server instructions block shown to MCP clients on connect."""

INSTRUCTIONS = """\
Official Juspay Technologies MCP tools to help merchants integrate with
Juspay SDKs, APIs, and the broader payments stack.

Juspay is a Payment Aggregator. High-level integration shapes:
  1. Payment Page / Express Checkout - hosted UI loaded by Juspay SDK
  2. Headless Express Checkout       - SDK with merchant-built UI
  3. API Integration                 - direct S2S REST calls
Specialized SDKs: UPI TPAP, UPI Plugin, UPI Bank Integration, BNPL, etc.

Service identifiers:
  - in.juspay.hyperpay  -> Payment Page
  - in.juspay.ec        -> Headless Express Checkout
  - in.juspay.hyperapi  -> HyperUPI (TPAP, Plugin, Bank Integration)

Tools (call them in this order):
  - list_products(category?)  Browse the product catalog. Use this first
                              when you don't know which product is
                              relevant. Optional category filter (e.g.
                              CHECKOUT, BILLING, DASHBOARD, UPI SOLUTIONS).
  - explore_product(product)  Fetch the llms.txt index for one product by
                              slug (e.g. "hyper-checkout"). The index
                              contains .md page links.
  - doc_fetch_tool(url)       Fetch any allowed Juspay docs URL. Returns
                              markdown. Use this after explore_product to
                              read specific pages.

Credentials:
  - client_id / merchant_id come from the Juspay dashboard. They cannot
    be mocked.
  - For UPI integrations, issuing_psp (e.g. YBL, ICICI, AXIS) and
    auth_type (cat | rsa | direct-jws) determine which SDK variant to
    integrate against. Ask the merchant.
"""
