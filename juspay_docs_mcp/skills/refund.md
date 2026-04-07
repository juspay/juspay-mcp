# Refund API

## Intent

Initiate a full or partial refund for a successfully charged order. Refunds can only be processed on orders with status `CHARGED`.

---

## API Endpoint

| Environment | Method | URL |
|---|---|---|
| Sandbox | POST | `https://sandbox.juspay.in/orders/{order_id}/refunds` |
| Production | POST | `https://api.juspay.in/orders/{order_id}/refunds` |

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
| `version` | `2023-06-30` | **Required** API version header |

---

## Request Body

| Parameter | Type | Max Length | Required | Description |
|---|---|---|---|---|
| `unique_request_id` | string | 255 | Yes | Unique alphanumeric identifier for this refund request (for idempotency) |
| `amount` | double | - | Yes | Refund amount in major units (minimum 1 INR) |

### Example Request Body

```json
{
  "unique_request_id": "refund_testing-order-one_001",
  "amount": 1.0
}
```

---

## Code Examples

### cURL

```bash
curl --location --request POST 'https://api.juspay.in/orders/testing-order-one/refunds' \
--header 'Authorization: Basic base_64_encoded_api_key==' \
--header 'x-merchantid: your_merchant_id' \
--header 'x-routing-id: customer_1122' \
--header 'Content-Type: application/json' \
--header 'version: 2023-06-30' \
--data-raw '{
    "unique_request_id": "refund_testing-order-one_001",
    "amount": 1.0
}'
```

### Node.js / JavaScript

```javascript
import fetch from 'node-fetch';

const apiKey = "<API_KEY>";
const merchantId = "<MERCHANT_ID>";
const orderId = "testing-order-one";
const xRoutingId = "<X_ROUTING_ID>";
const authorization = "Basic " + Buffer.from(apiKey + ":").toString("base64");

const requestPayload = JSON.stringify({
  "unique_request_id": "refund_testing-order-one_001",
  "amount": 1.0
});

const requestOptions = {
  method: 'POST',
  headers: {
    'Authorization': authorization,
    'x-merchantid': merchantId,
    'Content-Type': 'application/json',
    'x-routing-id': xRoutingId,
    'version': '2023-06-30'
  },
  body: requestPayload
};

fetch(`https://api.juspay.in/orders/${orderId}/refunds`, requestOptions)
  .then(response => response.json())
  .then(result => console.log(result))
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
    "x-routing-id": x_routing_id,
    "version": "2023-06-30"
}

payload = {
    "unique_request_id": "refund_testing-order-one_001",
    "amount": 1.0
}

response = requests.post(
    f"https://api.juspay.in/orders/{order_id}/refunds",
    headers=headers,
    json=payload
)
print(response.json())
```

### Java

```java
String apiKey = "<API_KEY>";
String merchantId = "<MERCHANT_ID>";
String orderId = "testing-order-one";
String xRoutingId = "<X_ROUTING_ID>";
String authorization = "Basic " + Base64.getEncoder().encodeToString((apiKey + ":").getBytes());

JSONObject payload = new JSONObject();
payload.put("unique_request_id", "refund_testing-order-one_001");
payload.put("amount", 1.0);

OkHttpClient client = new OkHttpClient();
MediaType mediaType = MediaType.parse("application/json");
RequestBody requestBody = RequestBody.create(mediaType, payload.toString());
Request request = new Request.Builder()
    .url("https://api.juspay.in/orders/" + orderId + "/refunds")
    .method("POST", requestBody)
    .addHeader("x-merchantid", merchantId)
    .addHeader("Authorization", authorization)
    .addHeader("Content-Type", "application/json")
    .addHeader("x-routing-id", xRoutingId)
    .addHeader("version", "2023-06-30")
    .build();

Response response = client.newCall(request).execute();
System.out.println(response.body().string());
```

---

## Response (200 OK)

```json
{
  "order_id": "testing-order-one",
  "status": "CHARGED",
  "refunds": [
    {
      "unique_request_id": "refund_testing-order-one_001",
      "amount": 1.0,
      "status": "PENDING",
      "created": "2024-01-15T10:30:00Z"
    }
  ],
  "refunded": true,
  "amount_refunded": 1.0
}
```

---

## Constraints

- **Only CHARGED orders can be refunded.** Orders in any other status will be rejected.
- **Maximum order age: 365 days.** Orders older than 365 days cannot be refunded.
- **Minimum refund amount: 1 INR** (or equivalent in the order currency).
- **Refund amount cannot exceed** the original order amount minus any previous refunds.
- **`unique_request_id` must be unique** per refund request. Reusing it will return the original refund response (idempotency).
- **`version` header is required.** Must be `2023-06-30`.

---

## Error Codes

| Error Code | Description |
|---|---|
| `REFUND_DUPLICATE_REQUEST` | A refund with this `unique_request_id` already exists |
| `INVALID_AMOUNT` | Amount is invalid (e.g., zero, negative, or non-numeric) |
| `INVALID_AMOUNT_REFUND` | Refund amount exceeds available refundable amount |
| `INVALID_ORDERID` | The specified `order_id` does not exist |
| `ORDER_TOO_OLD` | The order is older than 365 days |
| `CANNOT_PROCESS_AUTHORIZED_ORDER` | Order is in AUTHORIZED state, not CHARGED |

---

## Partial Refunds

You can issue multiple partial refunds on the same order, as long as the total refunded amount does not exceed the original order amount.

```javascript
// First partial refund
{ "unique_request_id": "refund_001", "amount": 50.0 }

// Second partial refund
{ "unique_request_id": "refund_002", "amount": 30.0 }

// Total refunded: 80.0 out of original amount
```

---

## Critical Notes

- **Always use a unique `unique_request_id`** per refund attempt to prevent duplicate refunds.
- **The `version` header (`2023-06-30`) is mandatory.** Without it, the API will reject the request.
- **Refund processing is asynchronous.** The initial response may show `status: "PENDING"`. Use the Order Status API to check if the refund has been completed.
- **Amount is in major units** (same as the order amount), not cents/paise.

---

## Documentation Links

- `https://juspay.io/in/docs/hyper-checkout/web/base-sdk-integration/refund.md`
- `https://juspay.io/in/docs/hyper-checkout/android/base-sdk-integration/refund.md`
- `https://juspay.io/in/docs/hyper-checkout/ios/base-sdk-integration/refund.md`
- `https://juspay.io/in/docs/hyper-checkout/react-native/base-sdk-integration/refund.md`
- `https://juspay.io/in/docs/hyper-checkout/flutter/base-sdk-integration/refund.md`
