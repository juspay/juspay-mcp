# Environment Setup & Credentials

## Intent

Configure the required Juspay credentials and environment variables before starting any integration. This guide covers where to find each credential, how to store them, and how to construct the authentication header in every supported language.

---

## Required Credentials

| Variable | Source | Notes |
|---|---|---|
| `JUSPAY_API_KEY` | Dashboard > API Keys | Server-side only. Never expose in client code. |
| `JUSPAY_MERCHANT_ID` | Dashboard > Profile | Used in `x-merchantid` header and SDK init |
| `JUSPAY_CLIENT_ID` | Dashboard > Profile | Used in SDK init and `payment_page_client_id` |
| `JUSPAY_BASE_URL` | - | `sandbox.juspay.in` (testing) or `api.juspay.in` (production) |
| `JUSPAY_WEBHOOK_USERNAME` | Dashboard > Webhooks | For validating incoming webhook requests |
| `JUSPAY_WEBHOOK_PASSWORD` | Dashboard > Webhooks | For validating incoming webhook requests |

---

## Environment File

Create a `.env` file in your server project root:

```env
# Juspay API Credentials
JUSPAY_API_KEY=your_api_key_here
JUSPAY_MERCHANT_ID=your_merchant_id
JUSPAY_CLIENT_ID=your_client_id

# Environment: sandbox.juspay.in or api.juspay.in
JUSPAY_BASE_URL=sandbox.juspay.in

# Webhook credentials (configured in Juspay Dashboard)
JUSPAY_WEBHOOK_USERNAME=your_webhook_username
JUSPAY_WEBHOOK_PASSWORD=your_webhook_password
```

**IMPORTANT:** Add `.env` to your `.gitignore`. Never commit API keys to version control.

---

## Authentication Pattern

All Juspay server-side APIs use **Basic Auth** where:
- **Username** = your API key
- **Password** = empty string

The resulting header value is:

```
Authorization: Basic base64(API_KEY + ":")
```

Note the trailing colon after the API key (representing the empty password).

---

## Auth Construction by Language

### JavaScript / Node.js

```javascript
const apiKey = process.env.JUSPAY_API_KEY;
const merchantId = process.env.JUSPAY_MERCHANT_ID;
const clientId = process.env.JUSPAY_CLIENT_ID;
const baseUrl = process.env.JUSPAY_BASE_URL; // "sandbox.juspay.in" or "api.juspay.in"

const authorization = "Basic " + Buffer.from(apiKey + ":").toString("base64");

// Use in fetch/axios headers:
const headers = {
  'Authorization': authorization,
  'x-merchantid': merchantId,
  'Content-Type': 'application/json',
  'x-routing-id': customerId  // must be consistent per customer
};
```

### Python

```python
import base64
import os

api_key = os.environ["JUSPAY_API_KEY"]
merchant_id = os.environ["JUSPAY_MERCHANT_ID"]
client_id = os.environ["JUSPAY_CLIENT_ID"]
base_url = os.environ["JUSPAY_BASE_URL"]  # "sandbox.juspay.in" or "api.juspay.in"

authorization = "Basic " + base64.b64encode(f"{api_key}:".encode("utf-8")).decode("utf-8")

# Use in requests headers:
headers = {
    "Authorization": authorization,
    "x-merchantid": merchant_id,
    "Content-Type": "application/json",
    "x-routing-id": customer_id  # must be consistent per customer
}
```

### Java

```java
String apiKey = System.getenv("JUSPAY_API_KEY");
String merchantId = System.getenv("JUSPAY_MERCHANT_ID");
String clientId = System.getenv("JUSPAY_CLIENT_ID");
String baseUrl = System.getenv("JUSPAY_BASE_URL");

String authorization = "Basic " + Base64.getEncoder().encodeToString((apiKey + ":").getBytes());

// Use in OkHttp/HttpURLConnection headers:
// .addHeader("Authorization", authorization)
// .addHeader("x-merchantid", merchantId)
// .addHeader("Content-Type", "application/json")
// .addHeader("x-routing-id", customerId)
```

### PHP

```php
<?php
$apiKey = getenv('JUSPAY_API_KEY');
$merchantId = getenv('JUSPAY_MERCHANT_ID');
$clientId = getenv('JUSPAY_CLIENT_ID');
$baseUrl = getenv('JUSPAY_BASE_URL');

$authorization = "Basic " . base64_encode($apiKey . ":");

// Use with cURL:
$headers = [
    "Authorization: " . $authorization,
    "x-merchantid: " . $merchantId,
    "Content-Type: application/json",
    "x-routing-id: " . $customerId
];

$ch = curl_init();
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
// ... rest of cURL setup
```

### Ruby

```ruby
require 'base64'
require 'net/http'
require 'json'

api_key = ENV['JUSPAY_API_KEY']
merchant_id = ENV['JUSPAY_MERCHANT_ID']
client_id = ENV['JUSPAY_CLIENT_ID']
base_url = ENV['JUSPAY_BASE_URL']

authorization = "Basic " + Base64.strict_encode64("#{api_key}:")

# Use with Net::HTTP:
uri = URI("https://#{base_url}/session")
http = Net::HTTP.new(uri.host, uri.port)
http.use_ssl = true

request = Net::HTTP::Post.new(uri)
request['Authorization'] = authorization
request['x-merchantid'] = merchant_id
request['Content-Type'] = 'application/json'
request['x-routing-id'] = customer_id
```

### C# / .NET

```csharp
using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;

string apiKey = Environment.GetEnvironmentVariable("JUSPAY_API_KEY");
string merchantId = Environment.GetEnvironmentVariable("JUSPAY_MERCHANT_ID");
string clientId = Environment.GetEnvironmentVariable("JUSPAY_CLIENT_ID");
string baseUrl = Environment.GetEnvironmentVariable("JUSPAY_BASE_URL");

string authorization = "Basic " + Convert.ToBase64String(Encoding.UTF8.GetBytes(apiKey + ":"));

// Use with HttpClient:
var client = new HttpClient();
client.DefaultRequestHeaders.Add("Authorization", authorization);
client.DefaultRequestHeaders.Add("x-merchantid", merchantId);
client.DefaultRequestHeaders.Add("x-routing-id", customerId);
// Content-Type is set on the content object, not headers
```

---

## Sandbox vs Production

| | Sandbox | Production |
|---|---|---|
| Base URL | `https://sandbox.juspay.in` | `https://api.juspay.in` |
| API Key | Sandbox key from Dashboard | Production key from Dashboard |
| SDK Environment | `"sandbox"` | `"production"` |
| Real Payments | No | Yes |
| Test Cards | Use Juspay test cards | Real cards only |

Use sandbox for development and testing. Switch to production only after thorough testing.

---

## Credential Rules

- **`JUSPAY_API_KEY`** is server-side only. Never include it in client-side code, mobile apps, or frontend bundles.
- **`JUSPAY_CLIENT_ID`** and **`JUSPAY_MERCHANT_ID`** are used in both server-side API calls and client-side SDK initialization. These are **NOT secrets** but are **NOT mockable** -- you must use real values from the Juspay Dashboard.
- **`x-routing-id`** must be consistent per customer. Always use the same `customer_id` value for a given customer across all API calls.
- **Webhook credentials** are set by you in the Dashboard and must match what your server validates.

---

## Quick Validation

After setting up credentials, verify your configuration with a simple Order Status call:

```bash
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Basic $(echo -n 'YOUR_API_KEY:' | base64)" \
  -H "x-merchantid: YOUR_MERCHANT_ID" \
  -H "Content-Type: application/json" \
  "https://sandbox.juspay.in/orders/nonexistent-order-id"
```

- **200** or **404** = credentials are valid (404 means order not found, but auth succeeded)
- **401** = invalid API key or merchant ID
- **Connection error** = wrong base URL

---

## Documentation Links

- Dashboard guide: `https://juspay.io/in/docs/hyper-checkout/web/base-sdk-integration/getting-started.md`
- API authentication: `https://juspay.io/in/docs/hyper-checkout/web/base-sdk-integration/authentication.md`
