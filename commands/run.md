# /run — iOS アプリをビルドしてシミュレーターで起動する

カレントディレクトリの iOS プロジェクトをビルドして、シミュレーターに起動する。

## 手順

### 1. プロジェクト情報を取得する

```bash
# xcodeproj を探す（ルート直下の .xcodeproj を優先する）
find . -maxdepth 1 -name "*.xcodeproj" | head -1 || find . -maxdepth 2 -name "*.xcodeproj" | head -1

# 利用可能な scheme を確認
xcodebuild -project <XCODEPROJ> -list 2>/dev/null
```

アプリターゲットの scheme を特定する（Tests/UITests 以外）。

### 2. ターゲットシミュレーターを決める

引数が指定されていればそのデバイス名を使う。なければ：
1. 現在 Booted のシミュレーターを使う
2. Booted がなければユーザーに `/simulator` で選ぶよう促して止まる

```bash
xcrun simctl list devices available | grep Booted
```

### 3. SDK バージョンを確認する

```bash
xcrun --sdk iphonesimulator --show-sdk-version
```

### 4. ビルドする

```bash
xcodebuild \
  -workspace <XCODEPROJ>/project.xcworkspace \
  -scheme <SCHEME> \
  -configuration Debug \
  -sdk iphonesimulator<VERSION> \
  -destination 'id=<DEVICE_UDID>' \
  -derivedDataPath build \
  build 2>&1 | tail -20
```

成功時は「ビルド成功」とだけ伝える。失敗時はエラー行を抽出して表示する：
```bash
... build 2>&1 | grep -E "error:|BUILD FAILED|warning:" | head -20
```

### 5. シミュレーターを起動してアプリをインストール・起動する

```bash
# Shutdown の場合は起動
xcrun simctl boot <DEVICE_UDID> 2>/dev/null
open -a Simulator

# .app のパスを探す
find build/Build/Products/Debug-iphonesimulator -name "*.app" -maxdepth 1 | head -1

# Bundle ID を取得
BUNDLE_ID=$(/usr/libexec/PlistBuddy -c "Print CFBundleIdentifier" <APP_PATH>/Info.plist)

# インストール＆起動
xcrun simctl install <DEVICE_UDID> <APP_PATH>
xcrun simctl launch <DEVICE_UDID> $BUNDLE_ID

# Simulator を最前面に表示
open -a Simulator
```

## 引数

- 引数なし: Booted のシミュレーターを使う
- デバイス名（例: `iPhone 17 Pro`）: 指定のシミュレーターを使う（Shutdown なら起動する）
- `macos`: Mac Catalyst でビルドして macOS で起動する

## macOS 起動の場合（引数が `macos` のとき）

```bash
xcodebuild \
  -workspace <XCODEPROJ>/project.xcworkspace \
  -scheme <SCHEME> \
  -configuration Debug \
  -destination 'platform=macOS,variant=Mac Catalyst' \
  -derivedDataPath build \
  build 2>&1 | grep -E "error:|BUILD SUCCEEDED|BUILD FAILED" | grep -v "note:" | head -20

# 起動
open build/Build/Products/Debug-maccatalyst/<APPNAME>.app
```
