# Initiate SDK

## Intent

Initialize the Juspay HyperSDK on the client side. This is a fire-and-forget call that pre-loads payment resources. It must complete before `process()` can be called. Call it once per SDK instance, typically on home screen or app launch.

---

## Web

**Not required.** Web integration uses redirect or iframe -- there is no client-side SDK to initialize.

---

## Android

### Java

```java
// 1. Create the HyperServices instance (in Activity)
HyperServicesHolder hyperServicesHolder = new HyperServicesHolder(this);

// 2. Build the initiate payload
private JSONObject createInitiatePayload() {
    JSONObject sdkPayload = new JSONObject();
    JSONObject innerPayload = new JSONObject();
    try {
        innerPayload.put("action", "initiate");
        innerPayload.put("merchantId", "<MERCHANT_ID>");
        innerPayload.put("clientId", "<CLIENT_ID>");
        innerPayload.put("xRoutingId", "<X_ROUTING_ID>");
        innerPayload.put("environment", "production"); // or "sandbox"
        sdkPayload.put("requestId", UUID.randomUUID().toString());
        sdkPayload.put("service", "in.juspay.hyperpay");
        sdkPayload.put("payload", innerPayload);
    } catch (JSONException e) {
        e.printStackTrace();
    }
    return sdkPayload;
}

// 3. Set callback and initiate
hyperServicesHolder.setCallback(createHyperPaymentsCallbackAdapter());
hyperServicesHolder.initiate(createInitiatePayload());
```

### Kotlin

```kotlin
// 1. Create the HyperServices instance
val hyperServicesHolder = HyperServicesHolder(this)

// 2. Build the initiate payload
private fun createInitiatePayload(): JSONObject {
    val innerPayload = JSONObject().apply {
        put("action", "initiate")
        put("merchantId", "<MERCHANT_ID>")
        put("clientId", "<CLIENT_ID>")
        put("xRoutingId", "<X_ROUTING_ID>")
        put("environment", "production") // or "sandbox"
    }
    return JSONObject().apply {
        put("requestId", UUID.randomUUID().toString())
        put("service", "in.juspay.hyperpay")
        put("payload", innerPayload)
    }
}

// 3. Set callback and initiate
hyperServicesHolder.setCallback(createHyperPaymentsCallbackAdapter())
hyperServicesHolder.initiate(createInitiatePayload())
```

---

## iOS

### Swift

```swift
import HyperSDK

// 1. Create the HyperServices instance
let hyperInstance = HyperServices()

// 2. Build the initiate payload
func createInitiatePayload() -> [String: Any] {
    let innerPayload: [String: Any] = [
        "action": "initiate",
        "merchantId": "<MERCHANT_ID>",
        "clientId": "<CLIENT_ID>",
        "xRoutingId": "<X_ROUTING_ID>",
        "environment": "sandbox" // or "production"
    ]
    return [
        "requestId": UUID().uuidString,
        "service": "in.juspay.hyperpay",
        "payload": innerPayload
    ]
}

// 3. Initiate
hyperInstance.initiate(self, payload: createInitiatePayload(), callback: hyperCallbackHandler)
```

### Objective-C

```objectivec
#import <HyperSDK/HyperSDK.h>

// 1. Create instance
HyperServices *hyperInstance = [[HyperServices alloc] init];

// 2. Build payload
NSDictionary *innerPayload = @{
    @"action": @"initiate",
    @"merchantId": @"<MERCHANT_ID>",
    @"clientId": @"<CLIENT_ID>",
    @"xRoutingId": @"<X_ROUTING_ID>",
    @"environment": @"production"
};
NSDictionary *sdkPayload = @{
    @"requestId": [[NSUUID UUID] UUIDString],
    @"service": @"in.juspay.hyperpay",
    @"payload": innerPayload
};

// 3. Initiate
[hyperInstance initiate:self payload:sdkPayload callback:^(NSDictionary *response) {
    // callback handler
}];
```

---

## React Native

```javascript
import HyperSdkReact from 'hyper-sdk-react';
import uuid from 'react-native-uuid';

// 1. Create HyperServices instance
HyperSdkReact.createHyperServices();

// 2. Build the initiate payload
const initiate_payload = {
  requestId: uuid.v4(),
  service: 'in.juspay.hyperpay',
  payload: {
    action: 'initiate',
    merchantId: '<MERCHANT_ID>',
    clientId: '<CLIENT_ID>',
    XRoutingId: '<X_ROUTING_ID>',
    environment: 'production', // or 'sandbox'
  },
};

// 3. Initiate
HyperSdkReact.initiate(JSON.stringify(initiate_payload));
```

---

## Flutter

```dart
import 'package:hypersdkflutter/hypersdkflutter.dart';
import 'package:uuid/uuid.dart';

// 1. Create HyperSDK instance
final hyperSDK = HyperSDK();

// 2. Build the initiate payload
var initiatePayload = {
  "requestId": const Uuid().v4(),
  "service": "in.juspay.hyperpay",
  "payload": {
    "action": "initiate",
    "merchantId": "<MERCHANT_ID>",
    "clientId": "<CLIENT_ID>",
    "xRoutingId": "<X_ROUTING_ID>",
    "environment": "production" // or "sandbox"
  }
};

// 3. Initiate
await hyperSDK.initiate(initiatePayload, initiateCallbackHandler);

// Callback handler
void initiateCallbackHandler(MethodCall methodCall) {
  if (methodCall.method == "initiate_result") {
    // SDK is ready for process()
  }
}
```

---

## Initiate Payload Structure

```json
{
  "requestId": "<unique_uuid>",
  "service": "in.juspay.hyperpay",
  "payload": {
    "action": "initiate",
    "merchantId": "<MERCHANT_ID>",
    "clientId": "<CLIENT_ID>",
    "xRoutingId": "<X_ROUTING_ID>",
    "environment": "production"
  }
}
```

| Field | Value | Notes |
|---|---|---|
| `requestId` | UUID | Unique per call |
| `service` | `"in.juspay.hyperpay"` | Always this value |
| `payload.action` | `"initiate"` | Always this value |
| `payload.merchantId` | Your Merchant ID | From Dashboard |
| `payload.clientId` | Your Client ID | From Dashboard |
| `payload.xRoutingId` | Customer ID | Must match `x-routing-id` header |
| `payload.environment` | `"production"` or `"sandbox"` | Must match your API base URL |

---

## Critical Notes

- **Fire-and-forget:** `initiate()` pre-loads resources asynchronously. You do not need to wait for a response before navigating the user.
- **Call only once per instance.** Creating a new instance and calling initiate again will cause issues.
- **Call on home screen / app launch.** The earlier you call it, the faster checkout will load.
- **Must complete before `process()`.** The SDK will not function if `process()` is called before `initiate()` finishes loading.
- **Environment must match.** If your server calls `sandbox.juspay.in`, set environment to `"sandbox"`. If it calls `api.juspay.in`, set `"production"`.

---

## Documentation Links

- Android: `https://juspay.io/in/docs/hyper-checkout/android/base-sdk-integration/initiate.md`
- iOS: `https://juspay.io/in/docs/hyper-checkout/ios/base-sdk-integration/initiate.md`
- React Native: `https://juspay.io/in/docs/hyper-checkout/react-native/base-sdk-integration/initiate.md`
- Flutter: `https://juspay.io/in/docs/hyper-checkout/flutter/base-sdk-integration/initiate.md`
