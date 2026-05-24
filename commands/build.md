# /build — iOS アプリをビルドする

カレントディレクトリの iOS プロジェクトをビルドする。起動はしない。

## 引数

- 引数なし または `simulator`: シミュレーター向けにビルド（デフォルト）
- `mac`: macOS 向けにビルド（Designed for iPhone）
- `release`: リリース構成でビルド
- `clean`: ビルドキャッシュを削除してからビルド

複数組み合わせ可能（例: `mac release`、`clean simulator`）

---

## 手順

### 1. プロジェクト情報を取得する

```bash
find . -maxdepth 2 -name "*.xcodeproj" | head -1
xcodebuild -project <XCODEPROJ> -list 2>/dev/null
```

アプリターゲットの scheme を特定する。

### 2. `clean` 指定がある場合

```bash
xcodebuild -project <XCODEPROJ> -scheme <SCHEME> clean 2>&1 | tail -5
```

### 3. ビルドを実行する

#### simulator（デフォルト）

```bash
SDK_VERSION=$(xcrun --sdk iphonesimulator --show-sdk-version)

xcodebuild \
  -project <XCODEPROJ> \
  -scheme <SCHEME> \
  -configuration <Debug|Release> \
  -sdk iphonesimulator${SDK_VERSION} \
  CONFIGURATION_BUILD_DIR=build/<Config>-iphonesimulator \
  build 2>&1 | tail -20
```

#### mac（Designed for iPhone）

```bash
xcodebuild \
  -project <XCODEPROJ> \
  -scheme <SCHEME> \
  -configuration <Debug|Release> \
  -destination 'platform=macOS,variant=Mac Catalyst' \
  CONFIGURATION_BUILD_DIR=build/<Config>-maccatalyst \
  build 2>&1 | tail -20
```

※ Mac Catalyst 非対応のプロジェクトの場合は「Designed for iPhone として実行するにはシミュレーターでビルドしてください」と伝える。

### 4. 結果を報告する

- 成功: ビルド成功・出力パスを表示
- 失敗: エラー行を抽出して表示
  ```bash
  ... build 2>&1 | grep -E "^.*error:.*$" | head -20
  ```
