# Open Payment Page (Process)

## Intent

Launch the Juspay payment UI using the `sdk_payload` received from the Session API. On web, this means redirecting or embedding an iframe. On mobile, this means calling the SDK's `process()` method.

---

## Prerequisites

1. **Session API called** -- you have the response containing `payment_links.web` (for web) or `sdk_payload` (for mobile).
2. **SDK installed and initiated** (mobile only) -- `initiate()` must have completed on the same SDK instance.
3. **Final payable amount available** -- only call `process()` after the user's cart/amount is finalized.

---

## Web

### Option 1: Full-Page Redirect

```javascript
// After receiving session API response
const sessionData = await createSession(); // your server call

// Redirect user to Juspay-hosted payment page
window.location.replace(sessionData.payment_links.web);
```

### Option 2: Iframe Embed

```html
<iframe
  src="SESSION_PAYMENT_LINK_WEB_URL"
  allow="payment *;"
  style="width: 100%; height: 100%; min-width: 700px; border: none;">
</iframe>
```

**Important iframe notes:**
- The `allow="payment *;"` attribute is **required** for UPI intent payments to work.
- Minimum width of **700px** recommended for desktop layouts.
- On mobile web, full-page redirect is preferred over iframe.

---

## Android

### Kotlin

```kotlin
// sdk_payload is the JSONObject from session API response's sdk_payload field
hyperServicesHolder?.process(sdk_payload)
```

### Java

```java
// sdk_payload is the JSONObject from session API response's sdk_payload field
hyperServicesHolder.process(sdk_payload);
```

The `sdk_payload` is the entire `sdk_payload` object from the Session API response, passed as a `JSONObject`. Do not modify it.

---

## iOS

### Swift

```swift
// sdkProcessPayload is the dictionary from session API response's sdk_payload field
hyperInstance.process(sdkProcessPayload)
```

### Objective-C

```objectivec
[hyperInstance process:sdkProcessPayload];
```

The `sdkProcessPayload` is the `sdk_payload` dictionary from the Session API response.

---

## React Native

```javascript
// sdk_payload is the object from session API response's sdk_payload field
HyperSdkReact.process(JSON.stringify(sdk_payload));
```

Note: The payload must be **stringified** before passing to `process()`.

---

## Flutter

```dart
// sdkPayload is the Map from session API response's sdk_payload field
await hyperSDK.process(sdkPayload, processCallbackHandler);

void processCallbackHandler(MethodCall methodCall) {
  if (methodCall.method == "process_result") {
    var args = json.decode(methodCall.arguments);
    var error = args["error"];
    var innerPayload = args["payload"];
    var status = innerPayload["status"];
    // Handle payment result
  }
}
```

---

## What Happens After `process()`

1. The Juspay payment sheet opens, showing available payment methods.
2. The user selects a method, enters details, and completes authentication (3DS, OTP, etc.).
3. The SDK fires a callback event with the result (see `handle_payment_response` skill).
4. For web redirect, the user is sent back to `return_url` with query parameters.

---

## Critical Notes

- **Same instance required:** `process()` must be called on the **same SDK instance** where `initiate()` was called. Do not create a new instance.
- **Do not modify `sdk_payload`:** Pass the Session API's `sdk_payload` response as-is to `process()`. Modifying fields will cause failures.
- **Call only after amount is final:** If the user can still change their cart after you create a session, you need a new session with the updated amount.
- **One active process at a time:** Do not call `process()` again while a payment sheet is already open.

---

## Documentation Links

- Web: `https://juspay.io/in/docs/hyper-checkout/web/base-sdk-integration/process.md`
- Android: `https://juspay.io/in/docs/hyper-checkout/android/base-sdk-integration/process.md`
- iOS: `https://juspay.io/in/docs/hyper-checkout/ios/base-sdk-integration/process.md`
- React Native: `https://juspay.io/in/docs/hyper-checkout/react-native/base-sdk-integration/process.md`
- Flutter: `https://juspay.io/in/docs/hyper-checkout/flutter/base-sdk-integration/process.md`
