# Adyen to Juspay Migration Skill

> **For AI Agents**: This is a structured migration skill document. Follow each section in order.
> Do NOT skip steps. Ask the merchant for required information before proceeding.
> After completing migration, run the validation checklist at the end.

---

## PHASE 0: GATHER INFORMATION FROM MERCHANT

**STOP. Before writing any code, you MUST collect the following from the merchant:**

### Required Information
1. **Juspay Merchant ID** - Get from Juspay Dashboard (Settings > Profile)
2. **Juspay Client ID** - Get from Juspay Dashboard (Settings > Profile)
3. **Juspay API Key** - Get from Juspay Dashboard (Settings > API Keys)
4. **Platform(s)** - Which platforms to migrate: Web, Android, iOS, React Native, Flutter
5. **Current Adyen integration type** - Sessions flow, Advanced flow, or Drop-in vs Components
6. **Target Juspay integration type** - Payment Page (recommended for Drop-in migrants) or Express Checkout Headless
7. **Return URL** - HTTPS URL for post-payment redirect (no query params, no IP addresses, must be reachable from Juspay servers)
8. **Webhook URL** - HTTPS endpoint for server notifications

### Important Notes
- **Client ID and Merchant ID are NEVER mockable** - they must be real values from the Juspay Dashboard
- Other fields (amount, order_id, customer details) can use test data during development
- Juspay Sandbox base URL: `https://sandbox.juspay.in`
- Juspay Production base URL: `https://api.juspay.in`

---

## PHASE 1: CONCEPT MAPPING

### 1.1 Credentials Mapping

| Adyen Credential | Juspay Equivalent | Where to Get |
|---|---|---|
| `ADYEN_API_KEY` | `JUSPAY_API_KEY` | Juspay Dashboard > Settings > API Keys |
| `ADYEN_MERCHANT_ACCOUNT` | `JUSPAY_MERCHANT_ID` | Juspay Dashboard > Settings > Profile |
| `ADYEN_CLIENT_KEY` (frontend) | `JUSPAY_CLIENT_ID` (aka `payment_page_client_id`) | Juspay Dashboard > Settings > Profile |
| `ADYEN_HMAC_KEY` (webhooks) | Username/Password (webhooks) | Juspay Dashboard > Settings > Webhooks |

### 1.2 Environment Mapping

| Adyen | Juspay |
|---|---|
| `TEST` environment | `sandbox` environment |
| `LIVE` environment | `production` environment |
| `https://checkout-test.adyen.com` | `https://sandbox.juspay.in` |
| `https://checkout-live.adyen.com` | `https://api.juspay.in` |

### 1.3 Integration Type Mapping

| Adyen Integration | Juspay Equivalent | Recommendation |
|---|---|---|
| Drop-in (Sessions flow) | HyperCheckout (Payment Page) | **Recommended** - closest 1:1 match |
| Drop-in (Advanced flow) | HyperCheckout (Payment Page) | Same UI, different backend |
| Components | Express Checkout (Headless) | Custom UI, headless SDK |
| API-only | Express Checkout API (S2S) | Direct REST API calls |

### 1.4 API Endpoint Mapping

| Adyen API | Juspay API | Notes |
|---|---|---|
| `POST /sessions` | `POST /session` | Creates order + returns SDK payload |
| `POST /payments` | `POST /order/create` + `POST /session` | Juspay separates order creation from session |
| `POST /payments/details` | `GET /orders/{order_id}` | Order Status API |
| `POST /payments/{id}/refunds` | `POST /orders/{order_id}/refunds` | Refund API |
| `POST /payments/{id}/cancels` | `POST /orders/{order_id}/refunds` | Use refund for cancellation |
| Webhook notifications | Webhook notifications | Different payload format |

### 1.5 Payment Status Mapping

| Adyen `resultCode` | Juspay `status` | `status_id` | Meaning |
|---|---|---|---|
| `Authorised` | `CHARGED` | 21 | Payment successful |
| `Refused` | `AUTHENTICATION_FAILED` or `AUTHORIZATION_FAILED` | 26 / 27 | Payment declined |
| `Error` | `JUSPAY_DECLINED` | 22 | System error |
| `Cancelled` | `BACKPRESSED` or `USER_ABORTED` | 35 / 38 | User cancelled |
| `Pending` | `PENDING_VBV` | 23 | Awaiting authentication |
| `Received` | `NEW` | 10 | Order created, payment not attempted |
| `RedirectShopper` | `PENDING_VBV` | 23 | Redirect to bank |
| `PresentToShopper` | `PENDING_VBV` | 23 | Show voucher/QR to shopper |
| `IdentifyShopper` / `ChallengeShopper` | `PENDING_VBV` | 23 | 3DS challenge |
| N/A | `AUTHORIZING` | 28 | Authorization in progress |
| N/A | `COD_INITIATED` | 29 | Cash on delivery |
| N/A | `AUTO_REFUNDED` | 105 | Auto refund initiated |

### 1.6 Payment Method Mapping

| Adyen `paymentMethod.type` | Juspay `payment_method_type` | Juspay `payment_method` |
|---|---|---|
| `scheme` (cards) | `CARD` | `VISA`, `MASTERCARD`, `RUPAY`, `AMEX` |
| `ideal`, `eps`, etc. (bank) | `NB` | Bank-specific codes (e.g., `NB_HDFC`) |
| `paytm`, `amazonpay` (wallet) | `WALLET` | Wallet-specific codes |
| `upi` | `UPI` | `UPI` |
| `klarna`, `afterpay` (BNPL) | `CONSUMER_FINANCE` | Provider-specific codes |

### 1.7 SDK Package Mapping

| Platform | Adyen Package | Juspay Package |
|---|---|---|
| Web | `@adyen/adyen-web` (npm) | HyperCheckout JS (CDN/script tag) |
| Android | `com.adyen.checkout:drop-in` (Gradle) | `in.juspay:hypersdk` (Gradle) |
| iOS | `Adyen` (CocoaPods/SPM) | `HyperSDK` (CocoaPods) |
| React Native | `@adyen/react-native` (npm) | `hyper-sdk-react` (npm) |
| Flutter | `adyen_checkout_flutter` (pub.dev) | `hypersdkflutter` (pub.dev) |

---

## PHASE 2: BACKEND MIGRATION

The backend migration is **platform-agnostic** — the same server-side changes apply regardless of which frontend platform you use.

### 2.1 Environment Variables

**REMOVE these Adyen env vars:**
```
ADYEN_API_KEY=...
ADYEN_MERCHANT_ACCOUNT=...
ADYEN_CLIENT_KEY=...
ADYEN_HMAC_KEY=...
```

**ADD these Juspay env vars:**
```
JUSPAY_API_KEY=your_juspay_api_key
JUSPAY_MERCHANT_ID=your_juspay_merchant_id
JUSPAY_CLIENT_ID=your_juspay_client_id
JUSPAY_BASE_URL=https://sandbox.juspay.in
```

### 2.2 Session/Order Creation Endpoint

This is the core backend change. Adyen's `/sessions` becomes Juspay's `/session`.

**ADYEN (before):**
```javascript
// Node.js with @adyen/api-library
const { Client, Config, CheckoutAPI } = require("@adyen/api-library");

const config = new Config();
config.apiKey = process.env.ADYEN_API_KEY;
const client = new Client({ config });
client.setEnvironment("TEST");
const checkout = new CheckoutAPI(client);

app.post("/api/sessions", async (req, res) => {
  const { amount, countryCode = "US" } = req.body;
  const response = await checkout.PaymentsApi.sessions({
    amount: {
      currency: amount?.currency || "USD",
      value: amount?.value || 1000, // minor units (cents)
    },
    countryCode,
    merchantAccount: process.env.ADYEN_MERCHANT_ACCOUNT,
    reference: uuidv4(),
    returnUrl: "https://your-site.com/checkout/result",
    channel: "Web",
  });
  res.json(response);
});
```

**JUSPAY (after):**
```javascript
// Node.js with fetch/axios (no SDK needed — direct REST API)
const JUSPAY_BASE_URL = process.env.JUSPAY_BASE_URL || "https://sandbox.juspay.in";
const JUSPAY_API_KEY = process.env.JUSPAY_API_KEY;
const JUSPAY_MERCHANT_ID = process.env.JUSPAY_MERCHANT_ID;
const JUSPAY_CLIENT_ID = process.env.JUSPAY_CLIENT_ID;

// Helper: Juspay uses Basic Auth with API key as username, empty password
function getJuspayAuthHeader() {
  return "Basic " + Buffer.from(JUSPAY_API_KEY + ":").toString("base64");
}

app.post("/api/session", async (req, res) => {
  try {
    const { amount, currency = "INR", customer_id, customer_email, customer_phone } = req.body;
    const order_id = "order_" + uuidv4().replace(/-/g, "").substring(0, 16);

    const response = await fetch(`${JUSPAY_BASE_URL}/session`, {
      method: "POST",
      headers: {
        "Authorization": getJuspayAuthHeader(),
        "x-merchantid": JUSPAY_MERCHANT_ID,
        "Content-Type": "application/json",
        "x-routing-id": customer_id,
      },
      body: JSON.stringify({
        order_id: order_id,
        amount: String(amount), // Juspay uses string amount in major units (e.g., "100.00")
        customer_id: customer_id,
        customer_email: customer_email,
        customer_phone: customer_phone,
        payment_page_client_id: JUSPAY_CLIENT_ID,
        action: "paymentPage",
        return_url: "https://your-site.com/checkout/result",
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      return res.status(response.status).json(data);
    }
    res.json(data);
  } catch (err) {
    console.error("Session creation error:", err.message);
    res.status(500).json({ error: err.message });
  }
});
```

**KEY DIFFERENCES:**
- Adyen amount is in **minor units** (cents): `1000` = $10.00. Juspay amount is in **major units** (string): `"10.00"` = $10.00
- Adyen uses a dedicated SDK library. Juspay uses direct REST API calls (no server SDK needed)
- Adyen uses `reference` for order ID. Juspay uses `order_id` (max 21 chars, alphanumeric)
- Juspay requires `customer_id`, `customer_email`, `customer_phone` as mandatory fields
- Juspay requires `payment_page_client_id` and `action: "paymentPage"` for HyperCheckout
- Juspay requires `x-merchantid` and `x-routing-id` headers

**PYTHON (after):**
```python
import base64
import requests
import uuid

JUSPAY_BASE_URL = os.environ.get("JUSPAY_BASE_URL", "https://sandbox.juspay.in")
JUSPAY_API_KEY = os.environ["JUSPAY_API_KEY"]
JUSPAY_MERCHANT_ID = os.environ["JUSPAY_MERCHANT_ID"]
JUSPAY_CLIENT_ID = os.environ["JUSPAY_CLIENT_ID"]

def get_juspay_auth_header():
    encoded = base64.b64encode(f"{JUSPAY_API_KEY}:".encode("utf-8")).decode("utf-8")
    return f"Basic {encoded}"

@app.route("/api/session", methods=["POST"])
def create_session():
    data = request.json
    order_id = f"order_{uuid.uuid4().hex[:16]}"
    
    response = requests.post(
        f"{JUSPAY_BASE_URL}/session",
        headers={
            "Authorization": get_juspay_auth_header(),
            "x-merchantid": JUSPAY_MERCHANT_ID,
            "Content-Type": "application/json",
            "x-routing-id": data["customer_id"],
        },
        json={
            "order_id": order_id,
            "amount": str(data["amount"]),
            "customer_id": data["customer_id"],
            "customer_email": data["customer_email"],
            "customer_phone": data["customer_phone"],
            "payment_page_client_id": JUSPAY_CLIENT_ID,
            "action": "paymentPage",
            "return_url": "https://your-site.com/checkout/result",
        },
    )
    return jsonify(response.json()), response.status_code
```

**JAVA (after):**
```java
import java.net.http.*;
import java.util.Base64;

String juspayBaseUrl = System.getenv("JUSPAY_BASE_URL");
String apiKey = System.getenv("JUSPAY_API_KEY");
String merchantId = System.getenv("JUSPAY_MERCHANT_ID");
String clientId = System.getenv("JUSPAY_CLIENT_ID");

String authHeader = "Basic " + Base64.getEncoder().encodeToString((apiKey + ":").getBytes());

// POST /session
HttpRequest request = HttpRequest.newBuilder()
    .uri(URI.create(juspayBaseUrl + "/session"))
    .header("Authorization", authHeader)
    .header("x-merchantid", merchantId)
    .header("Content-Type", "application/json")
    .header("x-routing-id", customerId)
    .POST(HttpRequest.BodyPublishers.ofString("""
        {
            "order_id": "%s",
            "amount": "%s",
            "customer_id": "%s",
            "customer_email": "%s",
            "customer_phone": "%s",
            "payment_page_client_id": "%s",
            "action": "paymentPage",
            "return_url": "https://your-site.com/checkout/result"
        }
        """.formatted(orderId, amount, customerId, email, phone, clientId)))
    .build();

HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
```

### 2.3 Order Status Endpoint

**ADYEN (before):** Handled automatically by Sessions flow, or via `/payments/details`

**JUSPAY (after):**
```javascript
app.get("/api/order-status/:orderId", async (req, res) => {
  try {
    const response = await fetch(
      `${JUSPAY_BASE_URL}/orders/${req.params.orderId}`,
      {
        method: "GET",
        headers: {
          "Authorization": getJuspayAuthHeader(),
          "x-merchantid": JUSPAY_MERCHANT_ID,
          "Content-Type": "application/json",
          "x-routing-id": req.query.customer_id || req.params.orderId,
        },
      }
    );
    const data = await response.json();
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});
```

**CRITICAL:** Always verify both `order_id` AND `amount` from the Order Status API response before fulfilling the order. Never trust client-side status alone.

### 2.4 Refund Endpoint

**ADYEN (before):**
```javascript
// Uses Adyen Modifications API
const refund = await checkout.ModificationsApi.refundCapturedPayment(pspReference, {
  amount: { currency: "USD", value: 1000 },
  merchantAccount: process.env.ADYEN_MERCHANT_ACCOUNT,
  reference: uuidv4(),
});
```

**JUSPAY (after):**
```javascript
app.post("/api/refund/:orderId", async (req, res) => {
  try {
    const { amount, reason } = req.body;
    const unique_request_id = "refund_" + uuidv4().replace(/-/g, "").substring(0, 16);

    const response = await fetch(
      `${JUSPAY_BASE_URL}/orders/${req.params.orderId}/refunds`,
      {
        method: "POST",
        headers: {
          "Authorization": getJuspayAuthHeader(),
          "x-merchantid": JUSPAY_MERCHANT_ID,
          "Content-Type": "application/json",
          "version": "2023-06-30",
          "x-routing-id": req.query.customer_id || req.params.orderId,
        },
        body: JSON.stringify({
          unique_request_id: unique_request_id,
          amount: amount, // in major units (e.g., 10.00)
        }),
      }
    );
    const data = await response.json();
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});
```

**KEY DIFFERENCES:**
- Adyen refunds by `pspReference` (payment ID). Juspay refunds by `order_id`
- Juspay requires a `unique_request_id` for idempotency
- Juspay requires `version` header
- Minimum refund amount in Juspay is 1 INR
- Refunds only possible on `CHARGED` orders
- Cannot refund orders older than 365 days

### 2.5 Webhook Handler

**ADYEN (before):**
```javascript
app.post("/api/webhooks", async (req, res) => {
  const notificationItems = req.body?.notificationItems;
  for (const { NotificationRequestItem } of notificationItems) {
    // HMAC validation
    if (process.env.ADYEN_HMAC_KEY) {
      const validator = new hmacValidator();
      if (!validator.validateHMAC(NotificationRequestItem, process.env.ADYEN_HMAC_KEY)) {
        continue;
      }
    }
    const { eventCode, success, merchantReference, pspReference } = NotificationRequestItem;
    // Process notification...
  }
  res.json({ notificationResponse: "[accepted]" });
});
```

**JUSPAY (after):**
```javascript
app.post("/api/webhooks", async (req, res) => {
  try {
    // Juspay sends Basic Auth credentials configured in Dashboard
    const authHeader = req.headers.authorization;
    if (authHeader) {
      const credentials = Buffer.from(authHeader.split(" ")[1], "base64").toString();
      const [username, password] = credentials.split(":");
      // Validate against your configured webhook credentials
      if (username !== process.env.JUSPAY_WEBHOOK_USERNAME ||
          password !== process.env.JUSPAY_WEBHOOK_PASSWORD) {
        return res.status(401).json({ error: "Unauthorized" });
      }
    }

    const webhookData = req.body;
    const { order_id, status, txn_id, txn_uuid } = webhookData.content || webhookData;

    console.log(`Webhook: order_id=${order_id} status=${status} txn_id=${txn_id}`);

    // IMPORTANT: Always verify with Order Status API
    const orderStatus = await fetch(
      `${JUSPAY_BASE_URL}/orders/${order_id}`,
      {
        headers: {
          "Authorization": getJuspayAuthHeader(),
          "x-merchantid": JUSPAY_MERCHANT_ID,
          "Content-Type": "application/json",
        },
      }
    );
    const orderData = await orderStatus.json();

    // Process based on verified status
    switch (orderData.status) {
      case "CHARGED":
        // Payment successful - fulfill order
        break;
      case "AUTHENTICATION_FAILED":
      case "AUTHORIZATION_FAILED":
      case "JUSPAY_DECLINED":
        // Payment failed
        break;
      case "AUTO_REFUNDED":
        // Refund processed
        break;
    }

    // CRITICAL: Return 200 OK, otherwise Juspay will retry
    res.status(200).json({ status: "ok" });
  } catch (err) {
    console.error("Webhook error:", err);
    res.status(200).json({ status: "ok" }); // Still return 200 to prevent retries
  }
});
```

**KEY DIFFERENCES:**
- Adyen uses HMAC signature validation. Juspay uses Basic Auth (username/password configured in Dashboard)
- Adyen wraps notifications in `notificationItems[].NotificationRequestItem`. Juspay sends flat JSON with `content` object
- Adyen responds with `{ notificationResponse: "[accepted]" }`. Juspay expects HTTP 200 status
- Adyen sends `eventCode` + `success`. Juspay sends `status` directly
- **Always verify webhook data with Order Status API** — this is mandatory in Juspay

### 2.6 Webhook Configuration

**Adyen:** Configure in Adyen Customer Area > Developers > Webhooks
**Juspay:** Configure in Juspay Dashboard > Payments > Settings > Webhook Tab

In Juspay Dashboard:
1. Set webhook URL (HTTPS endpoint)
2. Set username and password for Basic Auth
3. Optionally add custom headers
4. Select webhook events to receive
5. Optionally enable JWT encryption for payloads

**Juspay Webhook IP Whitelist:**
- Production: `13.126.232.13`, `35.154.93.248`, `65.2.117.44`, `3.110.250.172`, `40.192.89.124`, `40.192.88.11`, `18.61.131.193`
- Sandbox: `13.235.85.36`, `3.6.2.61`, `18.61.18.92`

---

## PHASE 3: FRONTEND MIGRATION — WEB

### 3.1 Remove Adyen Dependencies

```bash
npm uninstall @adyen/adyen-web
```

Remove CSS import: `import "@adyen/adyen-web/styles/adyen.css";`

### 3.2 Juspay Web Integration

Juspay HyperCheckout on web uses **URL redirect** or **iframe** — there is no npm package to install. The payment UI is hosted by Juspay.

**ADYEN (before) — React example:**
```jsx
import { AdyenCheckout, Dropin } from "@adyen/adyen-web";
import "@adyen/adyen-web/styles/adyen.css";

const CLIENT_KEY = import.meta.env.VITE_ADYEN_CLIENT_KEY;

function Checkout() {
  const dropinRef = useRef(null);

  useEffect(() => {
    async function initCheckout() {
      const res = await fetch("/api/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount: { currency: "USD", value: 1000 } }),
      });
      const session = await res.json();

      const checkout = await AdyenCheckout({
        environment: "test",
        clientKey: CLIENT_KEY,
        session: { id: session.id, sessionData: session.sessionData },
        onPaymentCompleted: (result) => {
          navigate(`/result?resultCode=${result.resultCode}`);
        },
        onPaymentFailed: (result) => {
          navigate(`/result?resultCode=${result?.resultCode || "Error"}`);
        },
        onError: (err) => console.error(err),
      });

      new Dropin(checkout).mount(dropinRef.current);
    }
    initCheckout();
  }, []);

  return <div ref={dropinRef} />;
}
```

**JUSPAY (after) — React example (redirect approach):**
```jsx
function Checkout() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function initCheckout() {
      try {
        const res = await fetch("/api/session", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            amount: "10.00",
            customer_id: "cust_123",
            customer_email: "user@example.com",
            customer_phone: "9876543210",
          }),
        });

        if (!res.ok) throw new Error("Failed to create session");
        const data = await res.json();

        // Redirect to Juspay hosted payment page
        if (data.payment_links?.web) {
          window.location.replace(data.payment_links.web);
        } else {
          throw new Error("No payment link received");
        }
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    }
    initCheckout();
  }, []);

  if (error) return <div>Error: {error}</div>;
  return <div>Redirecting to payment page...</div>;
}
```

**JUSPAY (after) — React example (iframe approach):**
```jsx
function Checkout() {
  const [paymentUrl, setPaymentUrl] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function initCheckout() {
      try {
        const res = await fetch("/api/session", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            amount: "10.00",
            customer_id: "cust_123",
            customer_email: "user@example.com",
            customer_phone: "9876543210",
          }),
        });

        if (!res.ok) throw new Error("Failed to create session");
        const data = await res.json();
        setPaymentUrl(data.payment_links?.web);
      } catch (err) {
        setError(err.message);
      }
    }
    initCheckout();
  }, []);

  if (error) return <div>Error: {error}</div>;
  if (!paymentUrl) return <div>Loading payment...</div>;

  return (
    <iframe
      src={paymentUrl}
      allow="payment *;"
      style={{ width: "100%", height: "920px", border: "none" }}
      title="Juspay Payment"
    />
  );
}
```

### 3.3 Payment Result Handling (Web)

**ADYEN:** Uses `onPaymentCompleted` callback with `resultCode` (Authorised, Refused, etc.)

**JUSPAY:** Redirects to `return_url` with query parameters, then you MUST verify server-side.

```jsx
// Result page component
function CheckoutResult() {
  const [status, setStatus] = useState("loading");
  const searchParams = new URLSearchParams(window.location.search);

  useEffect(() => {
    const orderId = searchParams.get("order_id");
    const clientStatus = searchParams.get("status");

    // MANDATORY: Verify with server-side Order Status API
    async function verifyPayment() {
      const res = await fetch(`/api/order-status/${orderId}`);
      const data = await res.json();

      // Trust server-side status, NOT the URL query params
      setStatus(data.status);
    }
    verifyPayment();
  }, []);

  const statusDisplay = {
    CHARGED: { label: "Payment Successful", color: "green" },
    AUTHENTICATION_FAILED: { label: "Payment Failed", color: "red" },
    AUTHORIZATION_FAILED: { label: "Payment Declined", color: "red" },
    JUSPAY_DECLINED: { label: "Payment Error", color: "red" },
    PENDING_VBV: { label: "Payment Pending", color: "orange" },
    NEW: { label: "Payment Not Completed", color: "gray" },
    BACKPRESSED: { label: "Payment Cancelled", color: "gray" },
    USER_ABORTED: { label: "Payment Cancelled", color: "gray" },
  };

  const display = statusDisplay[status] || { label: status, color: "gray" };
  return <div style={{ color: display.color }}>{display.label}</div>;
}
```

---

## PHASE 4: FRONTEND MIGRATION — ANDROID

### 4.1 Remove Adyen Dependencies

In `build.gradle` (app level), remove:
```gradle
implementation "com.adyen.checkout:drop-in:5.x.x"
implementation "com.adyen.checkout:card:5.x.x"
// ... any other com.adyen.checkout dependencies
```

### 4.2 Add Juspay HyperSDK

**Project-level `build.gradle`:**
```gradle
buildscript {
    repositories {
        maven { url "https://maven.juspay.in/jp-build-packages/hyper-sdk/" }
    }
    dependencies {
        classpath 'in.juspay:hypersdk.plugin:2.0.6'
    }
}

allprojects {
    repositories {
        maven { url "https://maven.juspay.in/jp-build-packages/hyper-sdk/" }
    }
}
```

**App-level `build.gradle`:**
```gradle
plugins {
    id 'hypersdk.plugin'
}

hyperSdkPlugin {
    clientId = "<YOUR_JUSPAY_CLIENT_ID>"
    sdkVersion = "2.1.20"
}
```

Run: `gradle sync` and clean build.

### 4.3 Android SDK Integration

**ADYEN (before) — Kotlin:**
```kotlin
// Adyen Drop-in configuration
val dropInConfiguration = DropInConfiguration.Builder(context, DropInService::class.java, clientKey)
    .setEnvironment(Environment.TEST)
    .build()

// Start checkout with session
val checkoutSession = CheckoutSession(sessionModel, configuration)
DropIn.startPayment(context, dropInConfiguration, checkoutSession)

// Handle result in Activity
override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
    if (requestCode == DropIn.DROP_IN_REQUEST_CODE) {
        val result = DropIn.getDropInResult(data)
        when (result) {
            is SessionDropInResult.Finished -> handleResult(result.result)
            is SessionDropInResult.CancelledByUser -> handleCancellation()
            is SessionDropInResult.Error -> handleError(result.reason)
        }
    }
}
```

**JUSPAY (after) — Kotlin:**
```kotlin
import `in`.juspay.hypersdk.core.PaymentConstants
import `in`.juspay.hypersdk.data.JuspayResponseHandler
import `in`.juspay.hypersdk.ui.HyperPaymentsCallbackAdapter
import `in`.juspay.services.HyperServices

class CheckoutActivity : AppCompatActivity() {
    private lateinit var hyperServices: HyperServices

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        hyperServices = HyperServices(this)

        // Step 1: Initiate SDK
        val initiatePayload = JSONObject().apply {
            put("requestId", UUID.randomUUID().toString())
            put("service", "in.juspay.hyperpay")
            put("payload", JSONObject().apply {
                put("action", "initiate")
                put("merchantId", "<YOUR_MERCHANT_ID>")
                put("clientId", "<YOUR_CLIENT_ID>")
                put("environment", "sandbox") // or "production"
            })
        }

        hyperServices.initiate(this, initiatePayload, object : HyperPaymentsCallbackAdapter() {
            override fun onEvent(jsonObject: JSONObject, juspayResponseHandler: JuspayResponseHandler) {
                val event = jsonObject.optString("event", "")
                if (event == "initiate_result") {
                    // SDK ready — now create session from your backend
                    createSessionAndProcess()
                }
            }
        })
    }

    private fun createSessionAndProcess() {
        // Call your backend /api/session to get sdk_payload
        // Then process payment with the payload:

        val processPayload = JSONObject().apply {
            // Use the sdk_payload returned from your /api/session endpoint
            put("requestId", sdkPayload.getString("requestId"))
            put("service", sdkPayload.getString("service"))
            put("payload", sdkPayload.getJSONObject("payload"))
        }

        hyperServices.process(this, processPayload)
    }

    // Handle backpress
    override fun onBackPressed() {
        if (!hyperServices.onBackPressed()) {
            super.onBackPressed()
        }
    }

    // Handle activity result
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        hyperServices.onActivityResult(requestCode, resultCode, data)
    }
}
```

**KEY DIFFERENCES:**
- Adyen uses a single `DropIn.startPayment()` call. Juspay uses a two-step `initiate` then `process` pattern
- Adyen handles everything in `onActivityResult`. Juspay uses a callback adapter for all events
- Juspay requires explicit `onBackPressed()` and `onActivityResult()` forwarding
- Juspay `sdk_payload` comes from the server-side `/session` API response

### 4.4 Android Payment Response

In the Juspay callback:
```kotlin
override fun onEvent(jsonObject: JSONObject, juspayResponseHandler: JuspayResponseHandler) {
    val event = jsonObject.optString("event", "")
    when (event) {
        "process_result" -> {
            val payload = jsonObject.optJSONObject("payload")
            val status = payload?.optString("status")
            // Verify with Order Status API on your server
            verifyOrderStatus(payload?.optString("orderId"))
        }
        "backpress" -> {
            // User pressed back — you can call terminate
            finish()
        }
    }
}
```

---

## PHASE 5: FRONTEND MIGRATION — iOS

### 5.1 Remove Adyen Dependencies

**CocoaPods:** Remove from Podfile:
```ruby
# Remove these
pod 'Adyen'
pod 'AdyenDropIn'
pod 'AdyenCard'
```

**SPM:** Remove Adyen package from Xcode project.

### 5.2 Add Juspay HyperSDK

**Podfile:**
```ruby
pod 'HyperSDK', '2.1.31'

post_install do |installer|
  fuse_path = "./Pods/HyperSDK/Fuse.rb"
  clean_assets = true
  if File.exist?(fuse_path)
    system("ruby", fuse_path.to_s, clean_assets.to_s)
  end
end
```

**Create `MerchantConfig.txt`** in your iOS project directory (same directory as Podfile):
```
clientId = <YOUR_JUSPAY_CLIENT_ID>
```

Run:
```bash
pod repo update
pod install
```

### 5.3 iOS SDK Integration

**ADYEN (before) — Swift:**
```swift
// Adyen Session + Drop-in
let configuration = DropInComponent.Configuration()
let session = try await AdyenSession.initialize(with: sessionConfiguration)
let dropIn = DropInComponent(paymentMethods: session.paymentMethods, configuration: configuration)
dropIn.delegate = self
present(dropIn.viewController, animated: true)

// Delegate methods
func didComplete(with result: PaymentResult, component: Component, session: AdyenSession) {
    switch result.resultCode {
    case .authorised: // Success
    case .refused: // Failed
    }
}
```

**JUSPAY (after) — Swift:**
```swift
import HyperSDK

class CheckoutViewController: UIViewController {
    var hyperServices: HyperServices!

    override func viewDidLoad() {
        super.viewDidLoad()
        hyperServices = HyperServices()

        // Step 1: Initiate SDK
        let initiatePayload: [String: Any] = [
            "requestId": UUID().uuidString,
            "service": "in.juspay.hyperpay",
            "payload": [
                "action": "initiate",
                "merchantId": "<YOUR_MERCHANT_ID>",
                "clientId": "<YOUR_CLIENT_ID>",
                "environment": "sandbox"
            ]
        ]

        hyperServices.initiate(self, payload: initiatePayload) { [weak self] event in
            if let eventName = event["event"] as? String, eventName == "initiate_result" {
                self?.createSessionAndProcess()
            }
        }
    }

    func createSessionAndProcess() {
        // Call your backend /api/session, get sdk_payload
        // Then process:
        hyperServices.process(self, payload: sdkPayload)
    }

    // Handle callback
    func onEvent(_ event: [String: Any]) {
        guard let eventName = event["event"] as? String else { return }
        switch eventName {
        case "process_result":
            if let payload = event["payload"] as? [String: Any],
               let orderId = payload["orderId"] as? String {
                verifyOrderStatus(orderId)
            }
        case "backpress":
            dismiss(animated: true)
        default:
            break
        }
    }
}
```

---

## PHASE 6: FRONTEND MIGRATION — REACT NATIVE

### 6.1 Remove Adyen Dependencies

```bash
npm uninstall @adyen/react-native
```

Remove any Adyen native configurations in `android/` and `ios/`.

### 6.2 Add Juspay HyperSDK

```bash
npm install hyper-sdk-react
```

**Android setup** — In `android/build.gradle`:
```gradle
allprojects {
    repositories {
        maven { url "https://maven.juspay.in/jp-build-packages/hyper-sdk/" }
    }
}

ext {
    clientId = "<YOUR_JUSPAY_CLIENT_ID>"
    hyperSDKVersion = "2.1.20"
}
```

**iOS setup** — Add to `package.json`:
```json
{
  "hyperSdkIOSVersion": "2.2.2.8"
}
```

**iOS Podfile:**
```ruby
post_install do |installer|
  fuse_path = "./Pods/HyperSDK/Fuse.rb"
  clean_assets = false
  if File.exist?(fuse_path)
    system("ruby", fuse_path.to_s, clean_assets.to_s)
  end
end
```

Create `ios/MerchantConfig.txt`:
```
clientId = <YOUR_JUSPAY_CLIENT_ID>
```

Run: `cd ios && pod repo update && pod install`

### 6.3 React Native SDK Integration

**ADYEN (before):**
```jsx
import { AdyenCheckout } from "@adyen/react-native";

<AdyenCheckout
  config={checkoutConfig}
  session={session}
  onComplete={(result) => handleResult(result)}
  onError={(error) => handleError(error)}
>
  <AdyenCheckout.DropIn />
</AdyenCheckout>
```

**JUSPAY (after):**
```jsx
import HyperSdkReact from "hyper-sdk-react";

function Checkout() {
  const [sdkReady, setSdkReady] = useState(false);

  useEffect(() => {
    // Step 1: Initiate SDK
    const initiatePayload = JSON.stringify({
      requestId: Date.now().toString(),
      service: "in.juspay.hyperpay",
      payload: {
        action: "initiate",
        merchantId: "<YOUR_MERCHANT_ID>",
        clientId: "<YOUR_CLIENT_ID>",
        environment: "sandbox",
      },
    });

    HyperSdkReact.initiate(initiatePayload);

    // Listen for events
    const eventListener = HyperSdkReact.addEventListener("HyperEvent", (event) => {
      const data = JSON.parse(event);
      switch (data.event) {
        case "initiate_result":
          setSdkReady(true);
          break;
        case "process_result":
          const orderId = data.payload?.orderId;
          // Verify with Order Status API on your server
          verifyOrderStatus(orderId);
          break;
      }
    });

    return () => eventListener?.remove();
  }, []);

  const startPayment = async () => {
    // Call your backend /api/session
    const res = await fetch("/api/session", { /* ... */ });
    const { sdk_payload } = await res.json();

    // Step 2: Process payment
    HyperSdkReact.process(JSON.stringify(sdk_payload));
  };

  return (
    <Button title="Pay Now" onPress={startPayment} disabled={!sdkReady} />
  );
}
```

---

## PHASE 7: FRONTEND MIGRATION — FLUTTER

### 7.1 Remove Adyen Dependencies

In `pubspec.yaml`, remove:
```yaml
# Remove
adyen_checkout_flutter: ^x.x.x
```

### 7.2 Add Juspay HyperSDK

**`pubspec.yaml`:**
```yaml
dependencies:
  hypersdkflutter: ^4.0.31
```

**Android** — In `android/build.gradle`:
```gradle
ext {
    clientId = "<YOUR_JUSPAY_CLIENT_ID>"
    hyperSDKVersion = "2.1.15"
}
```

**iOS** — Create `ios/MerchantConfig.txt`:
```
clientId = <YOUR_JUSPAY_CLIENT_ID>
```

**iOS Podfile:**
```ruby
post_install do |installer|
  fuse_path = "./Pods/HyperSDK/Fuse.rb"
  if File.exist?(fuse_path)
    system("ruby", fuse_path.to_s, "true".to_s)
  end
end
```

Run: `flutter pub get && cd ios && pod repo update && pod install`

### 7.3 Flutter SDK Integration

**ADYEN (before):**
```dart
final configuration = DropInConfiguration(environment: Environment.test, clientKey: clientKey);
final session = await AdyenSession.create(sessionData);
final dropIn = DropIn(session: session, configuration: configuration);
dropIn.start();
```

**JUSPAY (after):**
```dart
import 'package:hypersdkflutter/hypersdkflutter.dart';
import 'dart:convert';

class CheckoutScreen extends StatefulWidget {
  @override
  _CheckoutScreenState createState() => _CheckoutScreenState();
}

class _CheckoutScreenState extends State<CheckoutScreen> {
  final hyperSDK = HyperSDK();
  bool sdkReady = false;

  @override
  void initState() {
    super.initState();
    _initiateSDK();
  }

  void _initiateSDK() {
    final initiatePayload = {
      "requestId": DateTime.now().millisecondsSinceEpoch.toString(),
      "service": "in.juspay.hyperpay",
      "payload": {
        "action": "initiate",
        "merchantId": "<YOUR_MERCHANT_ID>",
        "clientId": "<YOUR_CLIENT_ID>",
        "environment": "sandbox",
      },
    };

    hyperSDK.initiate(jsonEncode(initiatePayload), _hyperCallback);
  }

  void _hyperCallback(dynamic event) {
    final data = jsonDecode(event);
    final eventName = data["event"];

    switch (eventName) {
      case "initiate_result":
        setState(() => sdkReady = true);
        break;
      case "process_result":
        final orderId = data["payload"]?["orderId"];
        // Verify with Order Status API on your server
        _verifyOrderStatus(orderId);
        break;
    }
  }

  Future<void> _startPayment() async {
    // Call your backend /api/session
    final response = await http.post(Uri.parse("/api/session"), /* ... */);
    final sdkPayload = jsonDecode(response.body)["sdk_payload"];

    // Process payment
    hyperSDK.process(jsonEncode(sdkPayload), _hyperCallback);
  }

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: sdkReady ? _startPayment : null,
      child: Text("Pay Now"),
    );
  }
}
```

---

## PHASE 8: REMOVE ADYEN DEPENDENCIES

### 8.1 Backend Cleanup

**Node.js:**
```bash
npm uninstall @adyen/api-library
```

**Python:**
```bash
pip uninstall Adyen
```

**Java/Kotlin:** Remove from `pom.xml` or `build.gradle`:
```xml
<!-- Remove -->
<dependency>
    <groupId>com.adyen</groupId>
    <artifactId>adyen-java-api-library</artifactId>
</dependency>
```

### 8.2 Code Cleanup

- Remove all `import` statements referencing Adyen packages
- Remove Adyen configuration classes/objects
- Remove `ADYEN_*` environment variables from `.env`, deployment configs, CI/CD
- Update any Adyen-specific error handling
- Remove Adyen CSS imports (`@adyen/adyen-web/styles/adyen.css`)

---

## PHASE 9: TESTING

### 9.1 Test Credentials

**Juspay Sandbox:**
- Base URL: `https://sandbox.juspay.in`
- Use test API keys from Juspay Dashboard (sandbox mode)
- Use Juspay's Dummy PG for testing

**Test Cards (Juspay Dummy PG):**

For detailed test cards and credentials, use the Juspay Docs MCP tool:
- Call `list_doc_sources` with your platform and integration type
- Fetch the test resources page: `{platform}/resources/test-resources.md`

### 9.2 Testing Checklist

1. [ ] Create order/session successfully returns `sdk_payload` and `payment_links`
2. [ ] Payment page loads correctly (redirect or iframe)
3. [ ] Card payment completes with status `CHARGED`
4. [ ] Failed payment returns appropriate error status
5. [ ] User cancellation (back press) is handled
6. [ ] `return_url` redirect includes `order_id` and `status` params
7. [ ] Server-side Order Status API returns correct status
8. [ ] Webhook receives notifications
9. [ ] Webhook auth validation works
10. [ ] Refund API processes refund successfully
11. [ ] Refund webhook notification received
12. [ ] Amount validation: verify server-side amount matches expected

---

## PHASE 10: PRODUCTION READINESS

### 10.1 Switch Environment

```
JUSPAY_BASE_URL=https://api.juspay.in    # Change from sandbox
```

Update SDK environment:
- Web: No change (URL changes via backend)
- Android/iOS/RN/Flutter: Change `"environment": "production"` in initiate payload

### 10.2 Security Checklist

1. [ ] API keys stored securely (not in client-side code)
2. [ ] Webhook endpoint validates Basic Auth credentials
3. [ ] Order Status API called server-side to verify payment (never trust client-side status)
4. [ ] Amount validated server-side before order fulfillment
5. [ ] `return_url` is HTTPS
6. [ ] Webhook IPs whitelisted (if using IP filtering)
7. [ ] `x-routing-id` consistently passed for same customer across all API calls

### 10.3 Monitoring

Configure webhook monitoring in Juspay Dashboard:
- EC Operations > Orders > Webhooks Tab
- Monitor for failed webhook deliveries
- Set up alerts for repeated failures

---

## VALIDATION CHECKLIST

Use this checklist to validate the migration is complete. For each item, verify against Juspay documentation using the `fetch_docs` tool.

### Backend Validation
- [ ] Session/Order creation endpoint works (`POST /session`)
- [ ] Authentication uses Basic Auth with API key
- [ ] `x-merchantid` header is set on all API calls
- [ ] `x-routing-id` header is set consistently per customer
- [ ] Amount is in major units (string, e.g., "100.00")
- [ ] `order_id` is unique and max 21 characters
- [ ] `customer_id`, `customer_email`, `customer_phone` are provided
- [ ] `payment_page_client_id` matches your Juspay Client ID
- [ ] `return_url` is valid HTTPS URL
- [ ] Order Status API endpoint works (`GET /orders/{order_id}`)
- [ ] Refund endpoint works (`POST /orders/{order_id}/refunds`)
- [ ] Webhook handler returns HTTP 200
- [ ] Webhook validates Basic Auth credentials

### Frontend Validation
- [ ] Adyen SDK/packages completely removed
- [ ] Juspay SDK installed for target platform(s)
- [ ] SDK `initiate` call completes successfully
- [ ] SDK `process` call loads payment page
- [ ] Payment result callback is handled
- [ ] Back press / cancellation is handled
- [ ] Server-side status verification implemented (NOT trusting client-side status)

### Environment Validation
- [ ] All `ADYEN_*` env vars removed
- [ ] All `JUSPAY_*` env vars configured
- [ ] Sandbox testing passes
- [ ] Production env vars ready (separate from sandbox)

### Documentation Reference URLs

For detailed verification, fetch these Juspay documentation pages using the `fetch_docs` tool:

| What to Verify | Documentation URL |
|---|---|
| Session API | `https://juspay.io/in/docs/hyper-checkout/{platform}/base-sdk-integration/session.md` |
| Order Status API | `https://juspay.io/in/docs/hyper-checkout/{platform}/base-sdk-integration/order-status-api.md` |
| Refund API | `https://juspay.io/in/docs/hyper-checkout/{platform}/base-sdk-integration/refund-order-api.md` |
| Webhooks | `https://juspay.io/in/docs/hyper-checkout/{platform}/base-sdk-integration/webhooks.md` |
| SDK Setup | `https://juspay.io/in/docs/hyper-checkout/{platform}/base-sdk-integration/getting-sdk.md` |
| SDK Initiate | `https://juspay.io/in/docs/hyper-checkout/{platform}/base-sdk-integration/initiating-sdk.md` |
| Payment Page | `https://juspay.io/in/docs/hyper-checkout/{platform}/base-sdk-integration/open-hypercheckout-screen.md` |
| Handle Response | `https://juspay.io/in/docs/hyper-checkout/{platform}/base-sdk-integration/handle-payment-response.md` |
| Error Codes | `https://juspay.io/in/docs/hyper-checkout/{platform}/resources/error-codes.md` |
| Transaction Status | `https://juspay.io/in/docs/hyper-checkout/{platform}/resources/transaction-status.md` |
| Test Resources | `https://juspay.io/in/docs/hyper-checkout/{platform}/resources/test-resources.md` |
| Sample Payloads | `https://juspay.io/in/docs/hyper-checkout/{platform}/resources/sample-payloads.md` |

Replace `{platform}` with: `web`, `android`, `ios`, `react-native`, `flutter`
