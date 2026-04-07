# Juspay: Customer Management APIs

> Customer creation is a prerequisite for Express Checkout (Headless) flows.
> For HyperCheckout (Payment Page), the /session API creates the customer automatically — you can skip this.

## When Do You Need This?

| Integration Type | Customer API Required? |
|---|---|
| HyperCheckout (Payment Page) | **No** — `/session` creates customer automatically |
| Express Checkout (Headless SDK) | **Yes** — create customer before creating order |
| Express Checkout (API-only) | **Yes** — create customer before creating order |

---

## Flow: Customer → Order → Payment

```
1. GET /customers/{id}     →  Check if customer exists
   ↓ (404 = not found)
2. POST /customers          →  Create new customer (get client_auth_token)
   ↓
3. POST /orders             →  Create order with same customer_id (get client_auth_token)
   ↓
4. SDK process() or API     →  Make payment
```

**CRITICAL:** The `customer_id` MUST be consistent across:
- Customer creation
- SDK `initiate()` payload (`xRoutingId`)
- Order creation
- All API calls (`x-routing-id` header)

---

## API: Get Customer

| Field | Value |
|---|---|
| Sandbox | `GET https://sandbox.juspay.in/customers/{customer_id}` |
| Production | `GET https://api.juspay.in/customers/{customer_id}` |
| Auth | Basic Auth (`API_KEY:`) |

### Headers
| Header | Value |
|---|---|
| `Authorization` | `Basic base64(API_KEY:)` |
| `x-merchantid` | Your Merchant ID |
| `x-routing-id` | Customer ID |
| `Content-Type` | `application/x-www-form-urlencoded` |

### Path Parameters
| Parameter | Required | Description |
|---|---|---|
| `customer_id` | Yes | Customer ID (the `id` from create customer response) |

### Query Parameters
| Parameter | Description |
|---|---|
| `options.get_client_auth_token=true` | Returns a 15-min SDK auth token |

### cURL
```bash
curl -X GET \
  'https://sandbox.juspay.in/customers/cust_123?options.get_client_auth_token=true' \
  -H 'Authorization: Basic <base64(API_KEY:)>' \
  -H 'x-merchantid: <MERCHANT_ID>' \
  -H 'x-routing-id: cust_123' \
  -H 'Content-Type: application/x-www-form-urlencoded'
```

### Response (200)
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
  "last_updated": "2020-03-17T14:29:17Z",
  "juspay": {
    "client_auth_token": "tkn_8649cd66d30c47728b8dd2fb6279a4cc",
    "client_auth_token_expiry": "2020-03-17T14:45:26Z"
  }
}
```

### Error (404)
```json
{
  "status": "invalid_request_error",
  "error_code": "object_not_found",
  "error_message": "Cannot find what you are looking for"
}
```

---

## API: Create Customer

| Field | Value |
|---|---|
| Sandbox | `POST https://sandbox.juspay.in/customers` |
| Production | `POST https://api.juspay.in/customers` |
| Auth | Basic Auth (`API_KEY:`) |
| Content-Type | `application/x-www-form-urlencoded` |

### Headers
| Header | Value |
|---|---|
| `Authorization` | `Basic base64(API_KEY:)` |
| `x-merchantid` | Your Merchant ID |
| `x-routing-id` | Customer ID (must match object_reference_id) |
| `Content-Type` | `application/x-www-form-urlencoded` |

### Body Parameters
| Parameter | Required | Description |
|---|---|---|
| `object_reference_id` | Yes | Unique customer ID, min 8 chars |
| `mobile_number` | Yes | 10-digit phone, no country code prefix |
| `mobile_country_code` | No | Country code without `+` (e.g., `91`) |
| `email_address` | No | Customer email (required by many gateways) |
| `first_name` | No | Customer first name |
| `last_name` | No | Customer last name |
| `options.get_client_auth_token` | No | `true` for SDK integration |

### cURL
```bash
curl -X POST 'https://sandbox.juspay.in/customers' \
  -H 'Authorization: Basic <base64(API_KEY:)>' \
  -H 'x-merchantid: <MERCHANT_ID>' \
  -H 'x-routing-id: cust_email@example.com' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'object_reference_id=cust_email@example.com' \
  -d 'mobile_number=9876543210' \
  -d 'mobile_country_code=91' \
  -d 'email_address=cust@example.com' \
  -d 'first_name=John' \
  -d 'last_name=Doe' \
  -d 'options.get_client_auth_token=true'
```

### Node.js
```javascript
const response = await fetch(`${JUSPAY_BASE_URL}/customers`, {
  method: "POST",
  headers: {
    "Authorization": juspayAuth(),
    "x-merchantid": JUSPAY_MERCHANT_ID,
    "x-routing-id": customerId,
    "Content-Type": "application/x-www-form-urlencoded",
  },
  body: new URLSearchParams({
    object_reference_id: customerId,
    mobile_number: phone,
    email_address: email,
    first_name: firstName,
    last_name: lastName,
    "options.get_client_auth_token": "true",
  }),
});
```

### Python
```python
resp = requests.post(f"{JUSPAY_BASE_URL}/customers", headers={
    "Authorization": juspay_auth(),
    "x-merchantid": JUSPAY_MERCHANT_ID,
    "x-routing-id": customer_id,
    "Content-Type": "application/x-www-form-urlencoded",
}, data={
    "object_reference_id": customer_id,
    "mobile_number": phone,
    "email_address": email,
    "first_name": first_name,
    "last_name": last_name,
    "options.get_client_auth_token": "true",
})
```

### Response (200)
```json
{
  "id": "cst_tooedar2k7j1d60b",
  "object": "customer",
  "object_reference_id": "cust_email@example.com",
  "mobile_number": "9876543210",
  "mobile_country_code": "91",
  "email_address": "cust@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "date_created": "2020-03-17T14:29:17Z",
  "last_updated": "2020-03-17T14:29:17Z",
  "juspay": {
    "client_auth_token": "tkn_8649cd66d30c47728b8dd2fb6279a4cc",
    "client_auth_token_expiry": "2020-03-17T14:45:26Z"
  }
}
```

### Error (400)
```json
{
  "status": "Bad Request",
  "error_code": "Mandatory fields are missing",
  "error_message": "Details of missing keys"
}
```

---

## Response Fields Reference

| Field | Type | Description |
|---|---|---|
| `id` | string | Juspay's internal customer ID (e.g., `cst_...`) |
| `object` | string | Always `"customer"` |
| `object_reference_id` | string | Your customer ID (what you passed in) |
| `mobile_number` | string | Phone number |
| `mobile_country_code` | string | Country code |
| `email_address` | string | Email |
| `first_name` | string | First name |
| `last_name` | string | Last name |
| `date_created` | string | UTC timestamp |
| `last_updated` | string | UTC timestamp |
| `juspay.client_auth_token` | string | SDK auth token (15-min validity) |
| `juspay.client_auth_token_expiry` | string | Token expiry UTC timestamp |

---

## Juspay Documentation
- Get Customer: {EC_DOC_BASE}/{platform}/base-sdk-integration/getcustomer.md
- Create Customer: {EC_DOC_BASE}/{platform}/base-sdk-integration/createcustomer.md
- Creating a Customer (overview): {EC_DOC_BASE}/{platform}/base-sdk-integration/creating-a-customer.md
