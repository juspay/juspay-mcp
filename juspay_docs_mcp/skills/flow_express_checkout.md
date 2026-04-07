# Juspay: Express Checkout (Headless) — Complete Integration Flow

> This document describes the **end-to-end payment flow** for Juspay Express Checkout (Headless SDK).
> Use this when the merchant wants to build their own payment UI but use Juspay's SDK for payment processing.
> For the hosted UI approach (Juspay builds the UI), see `flow_hypercheckout` instead.

## When to Use Express Checkout vs HyperCheckout

| Feature | HyperCheckout (Payment Page) | Express Checkout (Headless) |
|---|---|---|
| UI | Juspay-hosted payment page | Merchant builds their own UI |
| SDK service | `in.juspay.hyperpay` | `in.juspay.ec` |
| Complexity | Lower — single SDK call | Higher — merchant handles payment method selection, input |
| Customization | Theme/branding via Dashboard | Full control over UI/UX |
| Best for | Quick integration, migration | Custom checkout experiences |

---

## Prerequisites

Same as HyperCheckout:
1. **Juspay Account** — Onboarded by Juspay team
2. **Merchant ID** + **Client ID** — From Dashboard
3. **API Key** — From Dashboard > Security
4. **Webhook configured** — Dashboard > Webhook Tab

---

## Flow Overview

```
┌──────────┐     ┌──────────────┐     ┌────────────┐
│  Client   │────▶│ Your Server  │────▶│   Juspay   │
│  (App)    │◀────│  (Backend)   │◀────│   Server   │
└──────────┘     └──────────────┘     └────────────┘
     │                  │                    │
     │ 1. SDK Init      │                    │
     │ (in.juspay.ec)   │                    │
     │                  │                    │
     │                  │ 2. Create Customer │
     │                  │ ──────────────────▶│
     │                  │◀──────────────────│
     │                  │                    │
     │                  │ 3. Create Order    │
     │                  │ (with auth token)  │
     │                  │ ──────────────────▶│
     │                  │◀──────────────────│
     │                  │                    │
     │ 4. Get payment   │                    │
     │    methods ─────▶│                    │
     │◀────────────────│                    │
     │                  │                    │
     │ 5. User selects  │                    │
     │    payment method│                    │
     │                  │                    │
     │ 6. SDK process   │                    │
     │    (make payment)│                    │
     │                  │                    │
     │ 7. Result ◀──────│                    │
     │                  │                    │
     │ 8. Verify ──────▶│ GET /orders/{id}   │
     │                  │ ──────────────────▶│
     │ 9. Fulfill ◀────│◀──────────────────│
```

---

## Step 1: Install & Initiate SDK

Same SDK packages as HyperCheckout, but use service `in.juspay.ec` instead of `in.juspay.hyperpay`:

```json
{
  "requestId": "uuid",
  "service": "in.juspay.ec",
  "payload": {
    "action": "initiate",
    "merchantId": "<MERCHANT_ID>",
    "clientId": "<CLIENT_ID>",
    "environment": "sandbox"
  }
}
```

→ SDK setup is the same: `get_juspay_code("sdk_setup", "<platform>")`

---

## Step 2: Create Customer (Server-Side)

**For returning customers:** Check if customer exists first, then create if not.

### GET Customer
```
GET https://sandbox.juspay.in/customers/{customer_id}
```

**Response (200):**
```json
{
  "id": "cst_om2l6ctlptxwxuzj",
  "object": "customer",
  "object_reference_id": "customer@gmail.com",
  "mobile_number": "9988776655",
  "mobile_country_code": "91",
  "email_address": "customer@gmail.com",
  "first_name": "John",
  "last_name": "Smith",
  "date_created": "2020-03-17T14:29:17Z",
  "last_updated": "2020-03-17T14:29:17Z"
}
```

**404 = customer doesn't exist** → create one:

### POST Create Customer
```
POST https://sandbox.juspay.in/customers
Content-Type: application/x-www-form-urlencoded
```

**Parameters:**
| Parameter | Required | Description |
|---|---|---|
| `object_reference_id` | Yes | Unique customer ID (min 8 chars) |
| `mobile_number` | Yes | 10-digit phone (no country code prefix) |
| `mobile_country_code` | No | e.g., `91` (no `+`) |
| `email_address` | No | Customer email (required by many gateways) |
| `first_name` | No | Customer first name |
| `last_name` | No | Customer last name |
| `options.get_client_auth_token` | No | `true` for SDK integration (15-min token) |

**Response (200):**
```json
{
  "id": "cst_tooedar2k7j1d60b",
  "object": "customer",
  "object_reference_id": "customer_email",
  "mobile_number": "9999999999",
  "email_address": "test@juspay.in",
  "juspay": {
    "client_auth_token": "tkn_8649cd66d30c47728b8dd2fb6279a4cc",
    "client_auth_token_expiry": "2020-03-17T14:45:26Z"
  }
}
```

**Key rule:** The `customer_id` used in SDK `initiate` call and order creation MUST be the same to link saved payment methods correctly.

**Documentation:**
- Get Customer: {EC_DOC_BASE}/{platform}/base-sdk-integration/getcustomer.md
- Create Customer: {EC_DOC_BASE}/{platform}/base-sdk-integration/createcustomer.md

---

## Step 3: Create Order (Server-Side)

### POST Create Order
```
POST https://sandbox.juspay.in/orders
Content-Type: application/x-www-form-urlencoded
```

**Required Parameters:**
| Parameter | Type | Description |
|---|---|---|
| `order_id` | string (max 21) | Unique order identifier |
| `amount` | string | Amount in major units e.g., `"100.00"` |
| `customer_id` | string | Same customer_id from Step 2 |
| `options.get_client_auth_token` | boolean | Set `true` for SDK integration |

**Optional but recommended:**
| Parameter | Description |
|---|---|
| `customer_email` | Required by some gateways |
| `customer_phone` | Required by some gateways |
| `currency` | Default `INR` |
| `return_url` | Post-payment redirect URL |

**cURL:**
```bash
curl -X POST 'https://sandbox.juspay.in/orders' \
  -H 'Authorization: Basic <base64(API_KEY:)>' \
  -H 'x-merchantid: <MERCHANT_ID>' \
  -H 'x-routing-id: <customer_id>' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'order_id=order_123' \
  -d 'amount=100.00' \
  -d 'customer_id=cust_123' \
  -d 'customer_email=test@example.com' \
  -d 'options.get_client_auth_token=true'
```

**Response (200):**
```json
{
  "status": "NEW",
  "status_id": 10,
  "id": "ordeu_8bddad1e3b9c85eab3db4528575c01b",
  "order_id": "order_123",
  "payment_links": {
    "web": "https://api.juspay.in/merchant/pay/ordeu_...",
    "mobile": "https://api.juspay.in/merchant/pay/ordeu_...?mobile=true"
  },
  "juspay": {
    "client_auth_token": "tkn_753275c49a44a1a313eb2567f2fd6b",
    "client_auth_token_expiry": "2020-06-16T10:43:35Z"
  },
  "amount": 100.00,
  "currency": "INR"
}
```

**Important:** Save the `client_auth_token` — you need it for SDK `process()` calls.

**Documentation:** {EC_DOC_BASE}/{platform}/base-sdk-integration/create-order-api.md

---

## Step 4: Get Payment Methods (Client-Side via SDK)

After order creation, use the SDK to fetch available payment methods:

```json
{
  "requestId": "uuid",
  "service": "in.juspay.ec",
  "payload": {
    "action": "paymentPage",
    "merchantId": "<MERCHANT_ID>",
    "clientId": "<CLIENT_ID>",
    "orderId": "order_123",
    "clientAuthToken": "tkn_...",
    "environment": "sandbox"
  }
}
```

The callback returns available payment options (cards, UPI, wallets, netbanking, etc.) that you display in your custom UI.

**Documentation:** {EC_DOC_BASE}/{platform}/payloads/display-payment-options.md

---

## Step 5: User Selects Payment Method

Your custom UI presents the payment methods. User selects one and provides required input (card details, UPI VPA, etc.).

---

## Step 6: Process Payment (Client-Side via SDK)

Based on the payment method selected, call the SDK with the appropriate payload:

### Cards
```json
{
  "requestId": "uuid",
  "service": "in.juspay.ec",
  "payload": {
    "action": "paymentPage",
    "orderId": "order_123",
    "clientAuthToken": "tkn_...",
    "paymentMethod": "CARD",
    "cardNumber": "4111111111111111",
    "cardExpMonth": "12",
    "cardExpYear": "2025",
    "cardSecurityCode": "123",
    "nameOnCard": "John Doe",
    "saveToLocker": true
  }
}
```

### UPI Collect
```json
{
  "payload": {
    "action": "upiTxn",
    "orderId": "order_123",
    "clientAuthToken": "tkn_...",
    "paymentMethod": "UPI",
    "custVpa": "user@upi"
  }
}
```

### Wallets, Netbanking, etc.
Each has its own payload structure. See docs:
- Cards: {EC_DOC_BASE}/{platform}/payloads/cards--new-cards.md
- UPI Collect: {EC_DOC_BASE}/{platform}/payloads/upi-collect-payments.md
- UPI Intent: {EC_DOC_BASE}/{platform}/payloads/upi-intent-payments.md
- Wallets: {EC_DOC_BASE}/{platform}/payloads/wallets--redirection.md
- Netbanking: {EC_DOC_BASE}/{platform}/payloads/nb-payments.md

---

## Steps 7-9: Same as HyperCheckout

The response handling, server-side verification, and webhook flow are identical:

- **Step 7:** Handle `process_result` callback → `get_juspay_code("handle_payment_response", "<platform>")`
- **Step 8:** Verify via Order Status API → `get_juspay_code("order_status", "<platform>")`
- **Step 9:** Handle webhooks → `get_juspay_code("webhook", "<platform>")`

---

## HyperCheckout vs Express Checkout — When to Choose What

| If migrating from... | Recommended Juspay integration |
|---|---|
| Adyen Drop-in | **HyperCheckout** (Payment Page) — same concept: hosted UI |
| Adyen Components | **Express Checkout** (Headless) — same concept: custom UI with SDK |
| Stripe Checkout (hosted) | **HyperCheckout** |
| Stripe Elements (embedded) | **Express Checkout** |
| Razorpay Standard Checkout | **HyperCheckout** |
| Razorpay Custom UI | **Express Checkout** |
| Any PSP with API-only | **Express Checkout** or direct API |

---

## Juspay Documentation
- EC Overview: {EC_DOC_BASE}/{platform}/overview/integration-architecture.md
- EC Pre-requisites: {EC_DOC_BASE}/{platform}/overview/pre-requisites.md
- Payment Options: {EC_DOC_BASE}/{platform}/payloads/display-payment-options.md
- Cards: {EC_DOC_BASE}/{platform}/payloads/cards-integration-workflow.md
- UPI: {EC_DOC_BASE}/{platform}/payloads/upi-integration-workflow.md
- Wallets: {EC_DOC_BASE}/{platform}/payloads/wallets-integration-workflow.md
- Netbanking: {EC_DOC_BASE}/{platform}/payloads/nb-workflow.md
