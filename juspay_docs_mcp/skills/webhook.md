# Webhook Integration

## Intent

Receive real-time payment status notifications from Juspay via server-to-server webhooks. Webhooks provide asynchronous updates for payment events, ensuring your system stays in sync even if the user closes their browser or the SDK callback is missed.

---

## Configuration

### Dashboard Setup

1. Navigate to **Dashboard > Payments > Settings > Webhook Tab**
2. Enter your webhook endpoint URL (must be HTTPS)
3. Set a **username** and **password** for Basic Auth
4. Save the configuration

Juspay will send POST requests to your endpoint with Basic Auth using the credentials you configured.

### Dynamic Webhooks (Per-Session)

You can override the dashboard webhook URL per session by including `metadata.webhook_url` in the Session API request body:

```json
{
  "order_id": "testing-order-one",
  "amount": "1.0",
  "customer_id": "testing-customer-one",
  "customer_email": "test@mail.com",
  "customer_phone": "9876543210",
  "payment_page_client_id": "your_client_id",
  "action": "paymentPage",
  "return_url": "https://shop.merchant.com",
  "metadata": {
    "webhook_url": "https://your-server.com/webhooks/juspay/order-123"
  }
}
```

---

## Webhook Request Format

Juspay sends a POST request with:
- **Basic Auth** header using the username and password configured in the dashboard
- **JSON body** containing the order/payment event data

---

## Handling Webhooks

### Requirements

1. **Return HTTP 200** on successful receipt. Any non-200 response causes Juspay to **retry** the webhook.
2. **Validate Basic Auth** credentials to ensure the request is from Juspay.
3. **Always verify with Order Status API** -- treat the webhook as a notification, not the source of truth.
4. **Process idempotently** -- you may receive the same webhook multiple times due to retries.

---

## Code Examples

### Node.js / Express

```javascript
const express = require('express');
const app = express();
app.use(express.json());

const WEBHOOK_USERNAME = process.env.JUSPAY_WEBHOOK_USERNAME;
const WEBHOOK_PASSWORD = process.env.JUSPAY_WEBHOOK_PASSWORD;

function validateBasicAuth(req) {
  const authHeader = req.headers['authorization'];
  if (!authHeader || !authHeader.startsWith('Basic ')) {
    return false;
  }
  const credentials = Buffer.from(authHeader.slice(6), 'base64').toString('utf-8');
  const [username, password] = credentials.split(':');
  return username === WEBHOOK_USERNAME && password === WEBHOOK_PASSWORD;
}

app.post('/webhooks/juspay', (req, res) => {
  // 1. Validate Basic Auth
  if (!validateBasicAuth(req)) {
    return res.status(401).send('Unauthorized');
  }

  // 2. Extract event data
  const eventData = req.body;
  const orderId = eventData.order_id || eventData.content?.order?.order_id;
  const status = eventData.status || eventData.content?.order?.status;

  console.log(`Webhook received: order=${orderId}, status=${status}`);

  // 3. ALWAYS verify with Order Status API
  // Do not trust webhook payload for fulfillment decisions
  verifyOrderStatus(orderId).then((verifiedStatus) => {
    // 4. Process the verified status
    processPaymentUpdate(orderId, verifiedStatus);
  });

  // 5. Return 200 immediately (non-200 triggers retry)
  res.status(200).send('OK');
});

app.listen(3000);
```

### Python / Flask

```python
from flask import Flask, request, jsonify
import base64
import os
import requests

app = Flask(__name__)

WEBHOOK_USERNAME = os.environ.get('JUSPAY_WEBHOOK_USERNAME')
WEBHOOK_PASSWORD = os.environ.get('JUSPAY_WEBHOOK_PASSWORD')

def validate_basic_auth():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Basic '):
        return False
    try:
        credentials = base64.b64decode(auth_header[6:]).decode('utf-8')
        username, password = credentials.split(':', 1)
        return username == WEBHOOK_USERNAME and password == WEBHOOK_PASSWORD
    except Exception:
        return False

@app.route('/webhooks/juspay', methods=['POST'])
def handle_webhook():
    # 1. Validate Basic Auth
    if not validate_basic_auth():
        return jsonify({"error": "Unauthorized"}), 401

    # 2. Extract event data
    event_data = request.get_json()
    order_id = event_data.get('order_id') or event_data.get('content', {}).get('order', {}).get('order_id')
    status = event_data.get('status') or event_data.get('content', {}).get('order', {}).get('status')

    print(f"Webhook received: order={order_id}, status={status}")

    # 3. ALWAYS verify with Order Status API
    # Do not trust webhook payload for fulfillment decisions
    verify_order_status(order_id)

    # 4. Return 200 immediately (non-200 triggers retry)
    return jsonify({"status": "received"}), 200

if __name__ == '__main__':
    app.run(port=3000)
```

---

## IP Whitelist

For additional security, you can whitelist Juspay's IP addresses at the network/firewall level.

### Production IPs

```
13.126.232.13
35.154.93.248
65.2.117.44
3.110.250.172
40.192.89.124
40.192.88.11
18.61.131.193
```

### Sandbox IPs

```
13.235.85.36
3.6.2.61
18.61.18.92
```

---

## JWT Encryption (Optional)

For enhanced security, you can enable JWT-encrypted webhook payloads in the Juspay Dashboard. When enabled:

1. Juspay signs the webhook payload as a JWT token
2. Your server decodes and verifies the JWT using the shared secret from the dashboard
3. This provides tamper-proof webhook delivery

Enable this in **Dashboard > Payments > Settings > Webhook Tab > JWT Settings**.

---

## Retry Behavior

- Juspay **retries** webhook delivery if your endpoint returns a non-200 HTTP status code.
- Retries follow an exponential backoff pattern.
- Your webhook handler must be **idempotent** to handle duplicate deliveries safely.

---

## Critical Notes

- **Always return HTTP 200** on successful receipt. Non-200 = Juspay retries.
- **Always verify with Order Status API.** Webhooks are notifications, not the source of truth. An attacker could forge webhook requests.
- **Validate Basic Auth** on every webhook request.
- **Process idempotently.** Use the `order_id` as a deduplication key.
- **IP whitelisting is recommended** for production deployments.
- **Do not perform long-running operations** in the webhook handler. Return 200 immediately and process asynchronously.

---

## Documentation Links

- `https://juspay.io/in/docs/hyper-checkout/web/base-sdk-integration/webhooks.md`
- `https://juspay.io/in/docs/hyper-checkout/android/base-sdk-integration/webhooks.md`
- `https://juspay.io/in/docs/hyper-checkout/ios/base-sdk-integration/webhooks.md`
- `https://juspay.io/in/docs/hyper-checkout/react-native/base-sdk-integration/webhooks.md`
- `https://juspay.io/in/docs/hyper-checkout/flutter/base-sdk-integration/webhooks.md`
