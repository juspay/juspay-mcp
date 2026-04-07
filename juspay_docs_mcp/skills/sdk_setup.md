# SDK Setup & Installation

## Intent

Install and configure the Juspay HyperSDK for your target platform. This step must be completed before SDK initialization or payment processing.

---

## Web

**No SDK package is required for web integration.** The payment UI is fully hosted by Juspay.

After calling the Session API, use the `payment_links.web` URL from the response to either:
- **Redirect** the user to the hosted payment page, or
- **Embed** it in an iframe on your page

No npm packages, script tags, or build configuration needed for web.

---

## Android

### 1. Project-level `build.gradle`

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

### 2. App-level `build.gradle`

```gradle
plugins {
    id 'hypersdk.plugin'
}

hyperSdkPlugin {
    clientId = "<CLIENT_ID>"
    sdkVersion = "2.1.20"
}
```

### 3. Build

Run Gradle sync, then a clean build:

```bash
./gradlew clean build
```

---

## iOS

### 1. Podfile

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

### 2. MerchantConfig.txt

Create a file named `MerchantConfig.txt` in the **same directory as the Podfile** with this content:

```
clientId = <CLIENT_ID>
```

### 3. Install

```bash
pod repo update && pod install
```

---

## React Native

### 1. Install Package

```bash
npm install hyper-sdk-react
```

### 2. Android Configuration

In the **root-level `build.gradle`**, add the Juspay Maven repository and SDK properties:

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

ext {
    clientId = "<CLIENT_ID>"
    hyperSDKVersion = "2.1.20"
}
```

In the **app-level `build.gradle`**:

```gradle
plugins {
    id 'hypersdk.plugin'
}
```

### 3. iOS Configuration

Add to `package.json`:

```json
{
  "hyperSdkIOSVersion": "2.2.2.8"
}
```

Add the Fuse.rb post_install hook to `ios/Podfile`:

```ruby
post_install do |installer|
  fuse_path = "./Pods/HyperSDK/Fuse.rb"
  clean_assets = true
  if File.exist?(fuse_path)
    system("ruby", fuse_path.to_s, clean_assets.to_s)
  end
end
```

Create `ios/MerchantConfig.txt`:

```
clientId = <CLIENT_ID>
```

### 4. Install

```bash
cd ios && pod repo update && pod install
```

---

## Flutter

### 1. Install Package

Add to `pubspec.yaml`:

```yaml
dependencies:
  hypersdkflutter: ^4.0.31
```

Run:

```bash
flutter pub get
```

### 2. Android Configuration

In the **root-level `build.gradle`**:

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

ext {
    clientId = "<CLIENT_ID>"
    hyperSDKVersion = "2.1.15"
}
```

In the **app-level `build.gradle`**:

```gradle
plugins {
    id 'hypersdk.plugin'
}
```

### 3. iOS Configuration

Add the Fuse.rb post_install hook to `ios/Podfile`:

```ruby
post_install do |installer|
  fuse_path = "./Pods/HyperSDK/Fuse.rb"
  clean_assets = true
  if File.exist?(fuse_path)
    system("ruby", fuse_path.to_s, clean_assets.to_s)
  end
end
```

Create `ios/MerchantConfig.txt`:

```
clientId = <CLIENT_ID>
```

### 4. Install

```bash
cd ios && pod repo update && pod install
```

---

## Platform Version Summary

| Platform | Package / SDK | Version |
|---|---|---|
| Web | None (hosted) | N/A |
| Android | HyperSDK Plugin | 2.0.6 (plugin), 2.1.20 (SDK) |
| iOS | HyperSDK Pod | 2.1.31 |
| React Native | hyper-sdk-react | Latest via npm |
| Flutter | hypersdkflutter | ^4.0.31 |

---

## Common Issues

- **Android build fails:** Ensure the Juspay Maven URL is in both `buildscript.repositories` and `allprojects.repositories`.
- **iOS pod install fails:** Run `pod repo update` before `pod install`. Ensure `MerchantConfig.txt` exists in the same directory as the Podfile.
- **Client ID mismatch:** The `clientId` in build config must match the one used in Session API's `payment_page_client_id`.

---

## Documentation Links

- Web: `https://juspay.io/in/docs/hyper-checkout/web/base-sdk-integration/getting-sdk.md`
- Android: `https://juspay.io/in/docs/hyper-checkout/android/base-sdk-integration/getting-sdk.md`
- iOS: `https://juspay.io/in/docs/hyper-checkout/ios/base-sdk-integration/getting-sdk.md`
- React Native: `https://juspay.io/in/docs/hyper-checkout/react-native/base-sdk-integration/getting-sdk.md`
- Flutter: `https://juspay.io/in/docs/hyper-checkout/flutter/base-sdk-integration/getting-sdk.md`
