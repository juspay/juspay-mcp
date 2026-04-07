# Juspay: HyperCheckout (Payment Page) — Complete Integration Flow

> This document describes the **end-to-end payment flow** for Juspay HyperCheckout across all platforms.
> Follow these steps IN ORDER. Do not skip steps.

## Prerequisites

Before starting integration, ensure you have:

1. **Juspay Account** — Get onboarded by the Juspay team
2. **Merchant ID** — From Juspay Dashboard > Settings > Profile
3. **Client ID** — From Juspay Dashboard > Settings > Profile (often same as Merchant ID)
4. **API Key** — Generate at Dashboard > Payments > Settings > Security > Create New API Key
5. **Webhook configured** — Dashboard > Payments > Settings > Webhook Tab
6. **Return URL** — Valid HTTPS endpoint for post-payment redirect (no query params, no IPs)

> **CRITICAL:** Merchant ID and Client ID are NEVER mockable. All other fields can use test data in sandbox.

**Documentation:**
- Web: {DOC_BASE}/web/overview/pre-requisites.md
- Android: {DOC_BASE}/android/overview/pre-requisites.md
- iOS: {DOC_BASE}/ios/overview/pre-requisites.md
- React Native: {DOC_BASE}/react-native/overview/pre-requisites.md
- Flutter: {DOC_BASE}/flutter/overview/pre-requisites.md

---

## Flow Overview

```
┌──────────┐     ┌──────────────┐     ┌────────────┐     ┌──────────┐
│  Client   │────▶│ Your Server  │────▶│   Juspay   │────▶│ Payment  │
│  (App/Web)│◀────│  (Backend)   │◀────│   Server   │◀────│ Gateway  │
└──────────┘     └──────────────┘     └────────────┘     └──────────┘
     │                  │                    │
     │ 1. SDK Init      │                    │
     │ (native only)    │                    │
     │                  │                    │
     │ 2. Request       │ 3. POST /session   │
     │    payment ─────▶│ ──────────────────▶│
     │                  │◀──────────────────│
     │                  │  sdk_payload /      │
     │ 4. Launch UI ◀───│  payment_links     │
     │                  │                    │
     │ 5. User pays ───────────────────────▶│──────────▶│
     │                  │                    │◀──────────│
     │ 6. Result ◀──────────────────────────│
     │ (callback/redirect)                   │
     │                  │                    │
     │ 7. Verify ──────▶│ GET /orders/{id}   │
     │    server-side   │ ──────────────────▶│
     │                  │◀──────────────────│
     │ 8. Show status ◀─│                    │
     │                  │                    │
     │                  │ 9. Webhook ◀───────│
     │                  │    (async)         │
```

---

## Step 1: Install SDK (Native Platforms Only)

**Web:** No SDK needed. Skip to Step 2.

**For Android, iOS, React Native, Flutter:** Install the Juspay HyperSDK.

→ Use intent: `get_juspay_code("sdk_setup", "<platform>")`

---

## Step 2: Initiate SDK (Native Platforms Only)

**Web:** Skip to Step 3.

**When:** On app launch or cart/home screen load — BEFORE the user clicks "Pay".

**Why:** SDK initialization is a fire-and-forget call that preloads assets. Calling it early reduces payment page load time.

**What happens:**
- SDK downloads required assets for your merchant configuration
- No UI is rendered
- A callback fires `initiate_result` when ready

**Rules:**
- Call `initiate()` only ONCE per SDK instance
- Must complete before `process()` is called
- Forward `onBackPressed()` and `onActivityResult()` to SDK (Android)

→ Use intent: `get_juspay_code("initiate_sdk", "<platform>")`

---

## Step 3: Create Order & Session (Server-Side)

**When:** User clicks "Pay" / "Checkout" — after the final payable amount is known.

**This is a server-to-server call.** Your client sends order details to YOUR backend, which calls Juspay.

### API: POST /session

| Environment | URL |
|---|---|
| Sandbox | `https://sandbox.juspay.in/session` |
| Production | `https://api.juspay.in/session` |

### What it does:
1. Creates an order in Juspay's system
2. Returns `payment_links` (URLs for web redirect/iframe)
3. Returns `sdk_payload` (payload for native SDK `process()` call)
4. Returns `clientAuthToken` (short-lived token for SDK auth)

### Required fields:
- `order_id` — unique, max 21 chars, alphanumeric
- `amount` — string in major units: `"100.00"` (NOT cents)
- `customer_id` — your customer identifier
- `customer_email`, `customer_phone` — customer contact
- `payment_page_client_id` — your Juspay Client ID
- `action` — `"paymentPage"`
- `return_url` — HTTPS URL for redirect after payment

### Customer handling:
- Juspay creates the customer automatically if it doesn't exist when you call `/session`
- The `customer_id` you pass is linked to saved cards, payment history, etc.
- For returning customers, passing the same `customer_id` enables saved payment methods

→ Use intent: `get_juspay_code("create_order_session", "<platform>")`

---

## Step 4: Open Payment Page (Client-Side)

**When:** Immediately after receiving the session response from your backend.

### Web — Redirect or iFrame
```javascript
// Option A: Redirect
window.location.replace(sessionData.payment_links.web);

// Option B: iFrame (must include allow="payment *;" for UPI)
<iframe src={sessionData.payment_links.web} allow="payment *;" />
```

### Native (Android / iOS / React Native / Flutter)
Pass the `sdk_payload` from the session response to the SDK's `process()` method:

```
// Pseudocode for all native platforms:
sdk.process(session_response.sdk_payload)
```

**Rules:**
- Call `process()` on the SAME SDK instance where `initiate()` was called
- Only call after the final payable amount is available
- On web, iframe width < 700px shows mobile UI; >= 700px shows desktop UI

→ Use intent: `get_juspay_code("open_payment_page", "<platform>")`

---

## Step 5: User Completes Payment

Juspay handles:
- Displaying available payment methods (cards, UPI, netbanking, wallets, etc.)
- Card input, validation, tokenization
- 3DS / OTP authentication
- Bank redirects
- UPI intent / collect flows

**No code needed from you for this step.** The SDK/payment page handles everything.

---

## Step 6: Handle Payment Response (Client-Side)

### Web
User is redirected to your `return_url` with query parameters:
```
https://your-site.com/result?status=CHARGED&order_id=xxx&signature=xxx&signature_algorithm=HMAC-SHA256
```

### Native Platforms
The SDK callback fires a `process_result` event with the payment outcome:
```json
{
  "event": "process_result",
  "error": false,
  "payload": {
    "status": "charged",
    "orderId": "your-order-id"
  }
}
```

### Status values in callback:
| Status | Error | Meaning |
|---|---|---|
| `charged` | false | Payment successful |
| `cod_initiated` | false | Cash on delivery placed |
| `backpressed` | true | User pressed back |
| `user_aborted` | true | User cancelled |
| `pending_vbv` | true | Awaiting authentication |
| `authorizing` | true | Authorization in progress |
| `authorization_failed` | true | Bank declined |
| `authentication_failed` | true | 3DS/OTP failed |
| `api_failure` | true | System error |

### Android lifecycle events to forward:
- `onBackPressed()` → `hyperServicesHolder.onBackPressed()` — returns true if SDK handled it
- `onActivityResult()` → forward to SDK for UPI intent app-switch returns
- `onRequestPermissionsResult()` → forward for OTP auto-read permission

→ Use intent: `get_juspay_code("handle_payment_response", "<platform>")`

---

## Step 7: Verify Payment Server-Side (MANDATORY)

> **CRITICAL SECURITY STEP — NEVER SKIP THIS**

After receiving the client-side result (URL params or SDK callback), your server MUST call the Order Status API to verify the payment.

### Why:
- Client-side status can be tampered with
- Network issues may cause incorrect client-side status
- The server-side Order Status API is the **single source of truth**

### API: GET /orders/{order_id}

| Environment | URL |
|---|---|
| Sandbox | `https://sandbox.juspay.in/orders/{order_id}` |
| Production | `https://api.juspay.in/orders/{order_id}` |

### What to verify:
1. `status` equals `CHARGED`
2. `amount` matches your expected order amount
3. `order_id` matches your order

### Decision logic:
```
if (response.status === "CHARGED" && response.amount === expectedAmount) {
    // Fulfill the order
} else if (response.status === "PENDING_VBV" || response.status === "AUTHORIZING") {
    // Payment still in progress — wait for webhook
} else {
    // Payment failed — show error to user
}
```

→ Use intent: `get_juspay_code("order_status", "<platform>")`

---

## Step 8: Show Result to User

Based on the **server-verified** status (NOT the client-side status), show the user:
- Success page (for `CHARGED`)
- Failure page with retry option (for failed statuses)
- Pending page (for `PENDING_VBV` / `AUTHORIZING`)

This UI is YOUR responsibility — neither the Juspay SDK nor the payment page provides it.

---

## Step 9: Handle Webhooks (Async)

Juspay sends server-to-server webhook notifications for payment events asynchronously.

**When:** After payment completion (success or failure), refund processing, etc.

**Why use webhooks even if you already verify via Order Status API:**
- Handles cases where user closes the browser before redirect
- Handles delayed payment methods (bank transfers, UPI collect)
- Required for refund notifications
- Provides a reliable backup for payment confirmation

### Webhook rules:
- Return HTTP 200 — Juspay retries on non-200
- Validate Basic Auth credentials (configured in Dashboard)
- ALWAYS verify with Order Status API — don't trust webhook payload alone
- Can override webhook URL per transaction via `metadata.webhook_url` in session API

→ Use intent: `get_juspay_code("webhook", "<platform>")`

---

## Optional: Refunds

After a payment is `CHARGED`, you can process full or partial refunds.

### API: POST /orders/{order_id}/refunds

**Constraints:**
- Only works on `CHARGED` orders
- Min refund: 1 INR
- Max refund: `effective_amount - amount_refunded`
- Orders older than 365 days cannot be refunded
- Use `unique_request_id` for idempotency

→ Use intent: `get_juspay_code("refund", "<platform>")`

---

## Optional: Cancel Order

Cancel an order before payment is attempted.

### API: POST /merchants/{merchant_id}/order/{order_id}/cancel

```bash
curl -X POST 'https://api.juspay.in/merchants/{merchant_id}/order/{order_id}/cancel' \
  -H 'Authorization: Basic <encoded>' \
  -H 'x-merchantid: <merchant_id>' \
  -H 'Content-Type: application/json' \
  -d '{"cancel_reason": "Customer requested cancellation"}'
```

**Response:**
```json
{
  "status": "Success",
  "message": "Order cancelled successfully",
  "order_id": "your-order-id"
}
```

**Note:** A cancelled order cannot be reactivated. Generate a new session if needed.

---

## Quick Reference: API Endpoints

| API | Method | Sandbox URL | Production URL |
|---|---|---|---|
| Create Session | POST | `https://sandbox.juspay.in/session` | `https://api.juspay.in/session` |
| Order Status | GET | `https://sandbox.juspay.in/orders/{order_id}` | `https://api.juspay.in/orders/{order_id}` |
| Refund | POST | `https://sandbox.juspay.in/orders/{order_id}/refunds` | `https://api.juspay.in/orders/{order_id}/refunds` |
| Cancel | POST | `https://sandbox.juspay.in/merchants/{mid}/order/{oid}/cancel` | `https://api.juspay.in/merchants/{mid}/order/{oid}/cancel` |
| Get Customer | GET | `https://sandbox.juspay.in/customers/{customer_id}` | `https://api.juspay.in/customers/{customer_id}` |
| Create Customer | POST | `https://sandbox.juspay.in/customers` | `https://api.juspay.in/customers` |

All APIs use **Basic Auth**: `Authorization: Basic base64(API_KEY + ":")`

---

## Juspay Documentation
- Architecture: {DOC_BASE}/{platform}/overview/integration-architecture.md
- Pre-requisites: {DOC_BASE}/{platform}/overview/pre-requisites.md
- Session API: {DOC_BASE}/{platform}/base-sdk-integration/session.md
- Order Status: {DOC_BASE}/{platform}/base-sdk-integration/order-status-api.md
- Webhooks: {DOC_BASE}/{platform}/base-sdk-integration/webhooks.md
- Refunds: {DOC_BASE}/{platform}/base-sdk-integration/refund-order-api.md
- Error Codes: {DOC_BASE}/{platform}/resources/error-codes.md
- Transaction Status: {DOC_BASE}/{platform}/resources/transaction-status.md
- Test Resources: {DOC_BASE}/{platform}/resources/test-resources.md
