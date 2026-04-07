# Handle Payment Response

## Intent

Process the payment result after the user completes (or abandons) the payment flow. On web, this is handled via return URL query parameters. On mobile, this is handled via SDK callback events.

---

## Web

After payment, the user is redirected to the `return_url` specified in the Session API call. Juspay appends query parameters:

```
https://shop.merchant.com?status=CHARGED&order_id=testing-order-one&signature=xxxxxxxx&signature_algorithm=HMAC-SHA256
```

### Query Parameters

| Parameter | Description |
|---|---|
| `status` | Payment status (e.g., `CHARGED`, `AUTHENTICATION_FAILED`) |
| `order_id` | The order ID from the session |
| `signature` | HMAC signature for verification |
| `signature_algorithm` | `HMAC-SHA256` |

**MANDATORY:** Do NOT trust the query parameters alone. Always call the Order Status API server-side to verify the payment status.

---

## Android

### Java Callback

```java
public void onEvent(JSONObject jsonObject, JuspayResponseHandler responseHandler) {
    String event = jsonObject.getString("event");

    if (event.equals("process_result")) {
        boolean error = jsonObject.optBoolean("error");
        JSONObject innerPayload = jsonObject.optJSONObject("payload");
        String status = innerPayload.optString("status");

        if (!error) {
            switch (status) {
                case "charged":
                    // Payment successful
                    // Call Order Status API to verify
                    break;
                case "cod_initiated":
                    // Cash on delivery order placed
                    break;
            }
        } else {
            switch (status) {
                case "backpressed":
                    // User pressed back button
                    break;
                case "user_aborted":
                    // User cancelled the payment
                    break;
                case "pending_vbv":
                    // Awaiting 3DS authentication
                    break;
                case "authorizing":
                    // Payment is being processed
                    break;
                case "authorization_failed":
                    // Bank declined the transaction
                    break;
                case "authentication_failed":
                    // 3DS / OTP verification failed
                    break;
                case "api_failure":
                    // System error occurred
                    break;
            }
        }
    } else if (event.equals("hide_loader")) {
        // Hide your loading indicator
        // Payment page is now visible to the user
    }
}
```

### Kotlin Callback

```kotlin
override fun onEvent(jsonObject: JSONObject, responseHandler: JuspayResponseHandler) {
    val event = jsonObject.getString("event")

    when (event) {
        "process_result" -> {
            val error = jsonObject.optBoolean("error")
            val innerPayload = jsonObject.optJSONObject("payload")
            val status = innerPayload?.optString("status") ?: ""

            if (!error) {
                when (status) {
                    "charged" -> { /* Payment successful - verify via Order Status API */ }
                    "cod_initiated" -> { /* COD order placed */ }
                }
            } else {
                when (status) {
                    "backpressed" -> { /* User pressed back */ }
                    "user_aborted" -> { /* User cancelled */ }
                    "pending_vbv" -> { /* Awaiting auth */ }
                    "authorizing" -> { /* In progress */ }
                    "authorization_failed" -> { /* Bank declined */ }
                    "authentication_failed" -> { /* 3DS/OTP failed */ }
                    "api_failure" -> { /* System error */ }
                }
            }
        }
        "hide_loader" -> {
            // Hide loading indicator
        }
    }
}
```

### Back Button Handling (Android)

```java
@Override
public void onBackPressed() {
    boolean handled = hyperServicesHolder.onBackPressed();
    if (!handled) {
        super.onBackPressed();
    }
}
```

```kotlin
override fun onBackPressed() {
    if (!hyperServicesHolder.onBackPressed()) {
        super.onBackPressed()
    }
}
```

`onBackPressed()` returns `true` if the SDK handled the back press (e.g., dismissed a sub-screen). If it returns `false`, the SDK payment sheet is not active, and you should handle back navigation normally.

---

## iOS

### Swift Callback

```swift
func hyperCallbackHandler(response: [String: Any]) {
    guard let event = response["event"] as? String else { return }

    if event == "process_result" {
        let error = response["error"] as? Bool ?? false
        let payload = response["payload"] as? [String: Any] ?? [:]
        let status = payload["status"] as? String ?? ""

        if !error {
            switch status {
            case "charged":
                // Payment successful - verify via Order Status API
                break
            case "cod_initiated":
                // COD order placed
                break
            default:
                break
            }
        } else {
            switch status {
            case "backpressed", "user_aborted":
                // User cancelled
                break
            case "pending_vbv", "authorizing":
                // Payment pending
                break
            case "authorization_failed", "authentication_failed":
                // Payment failed
                break
            case "api_failure":
                // System error
                break
            default:
                break
            }
        }
    } else if event == "hide_loader" {
        // Hide loading indicator
    }
}
```

---

## React Native

```javascript
HyperSdkReact.onEvent((event) => {
  const eventData = JSON.parse(event);
  const eventName = eventData.event;

  if (eventName === 'process_result') {
    const error = eventData.error;
    const payload = eventData.payload;
    const status = payload.status;

    if (!error) {
      if (status === 'charged') {
        // Payment successful - verify via Order Status API
      } else if (status === 'cod_initiated') {
        // COD order placed
      }
    } else {
      // Handle error statuses: backpressed, user_aborted,
      // pending_vbv, authorizing, authorization_failed,
      // authentication_failed, api_failure
    }
  } else if (eventName === 'hide_loader') {
    // Hide loading indicator
  }
});
```

### Back Button (React Native Android)

```javascript
// In your component
BackHandler.addEventListener('hardwareBackPress', () => {
  return HyperSdkReact.onBackPressed();
});
```

---

## Flutter

```dart
void processCallbackHandler(MethodCall methodCall) {
  if (methodCall.method == "process_result") {
    var args = json.decode(methodCall.arguments);
    var error = args["error"] ?? false;
    var payload = args["payload"] ?? {};
    var status = payload["status"] ?? "";

    if (!error) {
      switch (status) {
        case "charged":
          // Payment successful - verify via Order Status API
          break;
        case "cod_initiated":
          // COD order placed
          break;
      }
    } else {
      switch (status) {
        case "backpressed":
        case "user_aborted":
          // User cancelled
          break;
        case "pending_vbv":
        case "authorizing":
          // Payment pending
          break;
        case "authorization_failed":
        case "authentication_failed":
          // Payment failed
          break;
        case "api_failure":
          // System error
          break;
      }
    }
  } else if (methodCall.method == "hide_loader") {
    // Hide loading indicator
  }
}
```

### Back Button (Flutter Android)

```dart
// Override back button in your widget
@override
Widget build(BuildContext context) {
  return WillPopScope(
    onWillPop: () async {
      var result = await hyperSDK.onBackPressed();
      if (result) {
        return false; // SDK handled the back press
      }
      return true; // Let Flutter handle it
    },
    child: // your widget
  );
}
```

---

## Payment Status Reference

| Status | Error | Meaning | Action |
|---|---|---|---|
| `charged` | false | Payment successful | Verify via Order Status API, fulfill order |
| `cod_initiated` | false | Cash on delivery placed | Confirm order, collect on delivery |
| `authentication_failed` | true | 3DS / OTP verification failed | Prompt retry |
| `authorization_failed` | true | Bank declined the transaction | Prompt different payment method |
| `pending_vbv` | true | Awaiting 3DS authentication | Poll Order Status API |
| `authorizing` | true | Payment is being processed | Poll Order Status API |
| `backpressed` | true | User pressed the back button | Return to cart/checkout |
| `user_aborted` | true | User explicitly cancelled | Return to cart/checkout |
| `api_failure` | true | System/network error | Prompt retry |

---

## SDK Events Reference

| Event | When |
|---|---|
| `process_result` | Payment flow completed (success or failure) |
| `hide_loader` | Payment page is visible; hide your loading spinner |

---

## Critical Notes

- **MANDATORY: After receiving `process_result` from the SDK, you MUST call the Order Status API server-to-server to determine the final payment status.** The client-side status is for UI purposes only and should not be used for order fulfillment decisions.
- **Verify BOTH `order_id` AND `amount`** in the Order Status API response to prevent tampering.
- **Do not trust `return_url` query parameters** on web without server-side verification.
- **`hide_loader` event** indicates the payment UI is visible. Use it to remove your loading spinner and prevent double-loading UX.
- **Back button handling** is required on Android to properly dismiss SDK sub-screens.

---

## Documentation Links

- Android: `https://juspay.io/in/docs/hyper-checkout/android/base-sdk-integration/handle-response.md`
- iOS: `https://juspay.io/in/docs/hyper-checkout/ios/base-sdk-integration/handle-response.md`
- React Native: `https://juspay.io/in/docs/hyper-checkout/react-native/base-sdk-integration/handle-response.md`
- Flutter: `https://juspay.io/in/docs/hyper-checkout/flutter/base-sdk-integration/handle-response.md`
