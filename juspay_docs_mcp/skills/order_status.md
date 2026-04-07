# Order Status API

## Intent

Server-side API call to check the current status of an order. This is the authoritative source of truth for payment status and **must** be called after every payment attempt to verify the outcome.

---

## API Endpoint

| Environment | Method | URL |
|---|---|---|
| Sandbox | GET | `https://sandbox.juspay.in/orders/{order_id}` |
| Production | GET | `https://api.juspay.in/orders/{order_id}` |

---

## Authentication

Basic Auth where the API key is the username and the password is empty.

```
Authorization: Basic base64(API_KEY + ":")
```

---

## Required Headers

| Header | Value | Notes |
|---|---|---|
| `Authorization` | `Basic <base64_encoded_key>` | API key as username, empty password |
| `x-merchantid` | Your Merchant ID | From Juspay Dashboard |
| `Content-Type` | `application/json` | |
| `x-routing-id` | Customer ID | Must match the value used when creating the order |

---

## Code Examples

### cURL

```bash
curl --location --request GET 'https://api.juspay.in/orders/testing-order-one' \
--header 'Authorization: Basic base_64_encoded_api_key==' \
--header 'x-merchantid: your_merchant_id' \
--header 'x-routing-id: customer_1122' \
--header 'Content-Type: application/json'
```

### Node.js / JavaScript

```javascript
import fetch from 'node-fetch';

const apiKey = "<API_KEY>";
const merchantId = "<MERCHANT_ID>";
const orderId = "testing-order-one";
const xRoutingId = "<X_ROUTING_ID>";
const authorization = "Basic " + Buffer.from(apiKey + ":").toString("base64");

const requestOptions = {
  method: 'GET',
  headers: {
    'Authorization': authorization,
    'x-merchantid': merchantId,
    'Content-Type': 'application/json',
    'x-routing-id': xRoutingId
  }
};

fetch(`https://api.juspay.in/orders/${orderId}`, requestOptions)
  .then(response => response.json())
  .then(result => {
    console.log("Status:", result.status);
    console.log("Amount:", result.amount);
    console.log("Order ID:", result.order_id);
  })
  .catch(error => console.log('error', error));
```

### Python

```python
import requests
import base64

api_key = "your_api_key"
merchant_id = "your_merchant_id"
order_id = "testing-order-one"
x_routing_id = "your_customer_id"

authorization = "Basic " + base64.b64encode(f"{api_key}:".encode("utf-8")).decode("utf-8")

headers = {
    "Authorization": authorization,
    "x-merchantid": merchant_id,
    "Content-Type": "application/json",
    "x-routing-id": x_routing_id
}

response = requests.get(f"https://api.juspay.in/orders/{order_id}", headers=headers)
data = response.json()

print("Status:", data["status"])
print("Amount:", data["amount"])
print("Order ID:", data["order_id"])
```

### Java

```java
String apiKey = "<API_KEY>";
String merchantId = "<MERCHANT_ID>";
String orderId = "testing-order-one";
String xRoutingId = "<X_ROUTING_ID>";
String authorization = "Basic " + Base64.getEncoder().encodeToString((apiKey + ":").getBytes());

OkHttpClient client = new OkHttpClient();
Request request = new Request.Builder()
    .url("https://api.juspay.in/orders/" + orderId)
    .method("GET", null)
    .addHeader("x-merchantid", merchantId)
    .addHeader("Authorization", authorization)
    .addHeader("Content-Type", "application/json")
    .addHeader("x-routing-id", xRoutingId)
    .build();

Response response = client.newCall(request).execute();
System.out.println(response.body().string());
```

---

## Response (200 OK)

```json
{
  "order_id": "testing-order-one",
  "txn_id": "txn_xxxxxxxxxxxxxxxx",
  "status": "CHARGED",
  "status_id": 21,
  "amount": 1.0,
  "currency": "INR",
  "refunded": false,
  "amount_refunded": 0.0,
  "payment_method_type": "UPI",
  "payment_method": "UPI",
  "card": {
    "last_four_digits": "1234",
    "card_brand": "VISA",
    "card_type": "CREDIT",
    "card_issuer": "HDFC"
  },
  "payment_gateway_response": {
    "resp_code": "SUCCESS",
    "resp_message": "Transaction successful",
    "txn_id": "gateway_txn_id"
  }
}
```

---

## Status Values

| Status | Status ID | Meaning |
|---|---|---|
| `NEW` | 10 | Order created, payment not attempted |
| `CHARGED` | 21 | Payment successful |
| `JUSPAY_DECLINED` | 22 | Declined by Juspay risk engine |
| `PENDING_VBV` | 23 | Awaiting 3DS / VBV authentication |
| `AUTHENTICATION_FAILED` | 26 | 3DS / OTP verification failed |
| `AUTHORIZATION_FAILED` | 27 | Bank declined the transaction |
| `AUTHORIZING` | 28 | Payment is being processed |
| `COD_INITIATED` | 29 | Cash on delivery order placed |
| `AUTO_REFUNDED` | 105 | Automatically refunded |

### Status Decision Logic

```
if status == "CHARGED":
    # Payment successful - fulfill the order
elif status in ["PENDING_VBV", "AUTHORIZING"]:
    # Payment in progress - poll again after a delay
elif status in ["AUTHENTICATION_FAILED", "AUTHORIZATION_FAILED", "JUSPAY_DECLINED"]:
    # Payment failed - prompt user to retry
elif status == "NEW":
    # Payment not yet attempted
elif status == "AUTO_REFUNDED":
    # Payment was charged but automatically refunded
```

---

## Key Response Fields

| Field | Type | Description |
|---|---|---|
| `order_id` | string | The order identifier |
| `txn_id` | string | Juspay transaction ID |
| `status` | string | Current order status (see table above) |
| `status_id` | integer | Numeric status code |
| `amount` | number | Order amount in major units |
| `currency` | string | Currency code |
| `refunded` | boolean | Whether any refund has been processed |
| `amount_refunded` | number | Total amount refunded |
| `payment_method_type` | string | e.g., `"UPI"`, `"CARD"`, `"NB"`, `"WALLET"` |
| `payment_method` | string | Specific method (e.g., `"UPI"`, `"VISA"`) |
| `card` | object | Card details (if card payment) |
| `payment_gateway_response` | object | Raw gateway response |

---

## Critical Notes

- **Always verify BOTH `order_id` AND `amount`** in the response to prevent order tampering.
- **This API is the single source of truth** for payment status. Never rely solely on client-side SDK callbacks or return URL query parameters.
- **`x-routing-id` must match** the value used when creating the order via the Session API.
- **Poll for pending statuses:** If status is `PENDING_VBV` or `AUTHORIZING`, poll this endpoint every few seconds until a final status is reached.
- **Idempotent:** This is a GET request and can be called any number of times safely.

---

## Documentation Links

- Web: `https://juspay.io/in/docs/hyper-checkout/web/base-sdk-integration/order-status-api.md`
- Android: `https://juspay.io/in/docs/hyper-checkout/android/base-sdk-integration/order-status-api.md`
- iOS: `https://juspay.io/in/docs/hyper-checkout/ios/base-sdk-integration/order-status-api.md`
- React Native: `https://juspay.io/in/docs/hyper-checkout/react-native/base-sdk-integration/order-status-api.md`
- Flutter: `https://juspay.io/in/docs/hyper-checkout/flutter/base-sdk-integration/order-status-api.md`
