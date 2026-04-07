# Create Order & Payment Session

## Intent

Server-side API call to create a payment order and obtain a session token. This is always the first step in any Juspay integration. The response provides either a hosted payment page URL (web) or an `sdk_payload` (mobile SDKs) needed to launch the payment UI.

---

## API Endpoint

| Environment | Method | URL |
|---|---|---|
| Sandbox | POST | `https://sandbox.juspay.in/session` |
| Production | POST | `https://api.juspay.in/session` |

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
| `x-merchantid` | Your Merchant ID | Obtained from Juspay Dashboard > Profile |
| `Content-Type` | `application/json` | Must be JSON |
| `x-routing-id` | Customer ID | Must be consistent per customer across all API calls |

---

## Required Body Parameters

| Parameter | Type | Max Length | Description |
|---|---|---|---|
| `order_id` | string | 21 | Unique alphanumeric identifier for the order |
| `amount` | string | - | Amount in **major units** as a string, e.g. `"100.00"` (NOT cents/paise) |
| `customer_id` | string | 128 | Unique customer identifier |
| `customer_email` | string | 300 | Customer email address |
| `customer_phone` | string | 300 | 10-digit phone number, no country code |
| `payment_page_client_id` | string | - | Juspay Client ID from Dashboard |
| `action` | string | - | Must be `"paymentPage"` |
| `return_url` | string | 255 | HTTPS URL, no query parameters, no IP addresses |

## Optional Body Parameters

| Parameter | Type | Description |
|---|---|---|
| `currency` | string | ISO currency code (default: `"INR"`) |
| `description` | string | Order description |
| `first_name` | string | Customer first name |
| `last_name` | string | Customer last name |
| `udf1` through `udf10` | string | Custom user-defined fields |
| `language` | string | Language preference |
| `mobile_country_code` | string | Country code for phone number |

---

## Code Examples

### Node.js / JavaScript

```javascript
import fetch from 'node-fetch';
const apiKey = "<API_KEY>";
const merchantId = "<MERCHANT_ID>";
const clientId = "<CLIENT_ID>";
const xRoutingId = "<X_ROUTING_ID>";
const authorization = "Basic " + Buffer.from(apiKey + ":").toString("base64");

var requestPayload = JSON.stringify({
  "order_id": "testing-order-one",
  "amount": "1.0",
  "customer_id": "testing-customer-one",
  "customer_email": "test@mail.com",
  "customer_phone": "9876543210",
  "payment_page_client_id": clientId,
  "action": "paymentPage",
  "return_url": "https://shop.merchant.com",
  "description": "Complete your payment",
  "first_name": "John",
  "last_name": "wick"
});

var requestOptions = {
  method: 'POST',
  headers: {
    'Authorization': authorization,
    'x-merchantid': merchantId,
    'Content-Type': 'application/json',
    'x-routing-id': xRoutingId
  },
  body: requestPayload
};

fetch("https://api.juspay.in/session", requestOptions)
  .then(response => response.json())
  .then(result => console.log(result))
  .catch(error => console.log('error', error));
```

### Python

```python
import requests
import base64
import json

api_key = "your_api_key"
merchant_id = "your_merchant_id"
client_id = "your_client_id"
x_routing_id = "your_customer_id"

authorization = "Basic " + base64.b64encode(f"{api_key}:".encode("utf-8")).decode("utf-8")

headers = {
    "Authorization": authorization,
    "x-merchantid": merchant_id,
    "Content-Type": "application/json",
    "x-routing-id": x_routing_id
}

payload = {
    "order_id": "testing-order-one",
    "amount": "1.0",
    "customer_id": "testing-customer-one",
    "customer_email": "test@mail.com",
    "customer_phone": "9876543210",
    "payment_page_client_id": client_id,
    "action": "paymentPage",
    "return_url": "https://shop.merchant.com",
    "description": "Complete your payment",
    "first_name": "John",
    "last_name": "wick"
}

response = requests.post("https://api.juspay.in/session", headers=headers, json=payload)
print(response.json())
```

### Java

```java
String apiKey = "<API_KEY>";
String merchantId = "<MERCHANT_ID>";
String clientId = "<CLIENT_ID>";
String xRoutingId = "<X_ROUTING_ID>";
String authorization = "Basic " + Base64.getEncoder().encodeToString((apiKey + ":").getBytes());

OkHttpClient client = new OkHttpClient();
MediaType mediaType = MediaType.parse("application/json");
RequestBody requestBody = RequestBody.create(mediaType, payload.toString());
Request request = new Request.Builder()
    .url("https://api.juspay.in/session")
    .method("POST", requestBody)
    .addHeader("x-merchantid", merchantId)
    .addHeader("Authorization", authorization)
    .addHeader("Content-Type", "application/json")
    .addHeader("x-routing-id", xRoutingId)
    .build();

Response response = client.newCall(request).execute();
System.out.println(response.body().string());
```

### cURL

```bash
curl --location --request POST 'https://api.juspay.in/session' \
--header 'Authorization: Basic base_64_encoded_api_key==' \
--header 'x-merchantid: your_merchant_id' \
--header 'x-routing-id: customer_1122' \
--header 'Content-Type: application/json' \
--data-raw '{
    "order_id": "testing-order-one",
    "amount": "1.0",
    "customer_id": "testing-customer-one",
    "customer_email": "test@mail.com",
    "customer_phone": "9876543210",
    "payment_page_client_id": "your_client_id",
    "action": "paymentPage",
    "return_url": "https://shop.merchant.com",
    "description": "Complete your payment",
    "first_name": "John",
    "last_name": "wick"
}'
```

---

## Response (200 OK)

```json
{
  "status": "NEW",
  "id": "ordeh_xxxxxxxxxxxxxxxxxxxx",
  "order_id": "testing-order-one",
  "payment_links": {
    "web": "https://api.juspay.io/orders/ordeh_xxxxxxxxxxxxxxxxxxxx/payment-page"
  },
  "sdk_payload": {
    "requestId": "12398b5571d74c3388a74004bc24370c",
    "service": "in.juspay.hyperpay",
    "payload": {
      "clientId": "yourClientId",
      "amount": "1.0",
      "merchantId": "yourMerchantId",
      "clientAuthToken": "tkn_xxxxxxxxxxxxxxxxxxxxx",
      "clientAuthTokenExpiry": "2022-03-12T20:29:23Z",
      "environment": "production",
      "action": "paymentPage",
      "customerId": "testing-customer-one",
      "returnUrl": "https://shop.merchant.com",
      "currency": "INR",
      "orderId": "testing-order-one"
    }
  }
}
```

### Key Response Fields

| Field | Usage |
|---|---|
| `payment_links.web` | URL for web redirect or iframe integration |
| `sdk_payload` | Pass directly to mobile SDK `process()` call |
| `sdk_payload.payload.clientAuthToken` | Session token, has expiry |
| `status` | Will be `"NEW"` for a freshly created order |

---

## Error Responses

| HTTP Code | Cause |
|---|---|
| 400 | Missing required fields or invalid values |
| 401 | Invalid API key or `access_denied` |
| 500 | Internal server error |

---

## Critical Notes

- **`amount` is a string in major units, NOT cents/paise.** `"100.00"` means 100 rupees, not 1 rupee.
- **`order_id` max length is 21 characters.** Alphanumeric only.
- **`x-routing-id` must be consistent per customer** across all API calls for that customer.
- **`return_url` must be HTTPS** with no query parameters and no IP addresses.
- **`payment_page_client_id` and `merchant_id` are NEVER mockable.** These must be real values from the Juspay Dashboard.
- The `sdk_payload` from the response is passed as-is to the mobile SDK `process()` method.

---

## Documentation Links

- Web: `https://juspay.io/in/docs/hyper-checkout/web/base-sdk-integration/session.md`
- Android: `https://juspay.io/in/docs/hyper-checkout/android/base-sdk-integration/session.md`
- iOS: `https://juspay.io/in/docs/hyper-checkout/ios/base-sdk-integration/session.md`
- React Native: `https://juspay.io/in/docs/hyper-checkout/react-native/base-sdk-integration/session.md`
- Flutter: `https://juspay.io/in/docs/hyper-checkout/flutter/base-sdk-integration/session.md`
