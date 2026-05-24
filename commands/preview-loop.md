# /preview-loop — SwiftUI Preview ループ

XcodeBuildMCP の Xcode IDE ブリッジ `RenderPreview` を使い、コード修正 → プレビュー確認 → 修正 を自律的に繰り返す。

## 前提条件

- XcodeBuildMCP が MCP サーバーとして設定されていること（`.mcp.json`）
- `.xcodebuildmcp/config.yaml` で `xcode-ide` ワークフローが有効であること
- Xcode でワークスペース/プロジェクトが開かれていること
- Xcode の MCP ブリッジ承認が完了していること

## 引数

- `$ARGUMENTS`: 修正対象の説明（例: "HomeContentのiPadレイアウトを改善して"）

## セットアップ

1. `xcode_tools_bridge_status` でブリッジ接続を確認する
2. 接続されていない場合は `xcode_tools_bridge_sync` で同期する
3. `XcodeListWindows` で対象ワークスペースの `tabIdentifier` を取得する

## ループ手順

以下のステップを **最大10回** 繰り返す。

### Step 1: 現状把握

対象ファイルを読み、修正すべき点を特定する。初回は `$ARGUMENTS` の指示に従う。2回目以降は前回のプレビュー結果から問題点を特定する。

### Step 2: コード修正

Edit ツールで対象ファイルを修正する。一度に1つの問題に集中すること。

### Step 3: ビルド → プレビュー確認

**★ 必ず BuildProject → RenderPreview の順で呼ぶこと。省略禁止。**

```
// Step 3a: ビルドキャッシュをクリア
remoteTool: "BuildProject"
arguments: { "tabIdentifier": "<windowtabN>" }
timeoutMs: 120000

// Step 3b: プレビューレンダリング
remoteTool: "RenderPreview"
arguments: {
  "tabIdentifier": "<windowtabN>",
  "sourceFilePath": "<ワークスペースルートからの相対パス>",
  "timeout": 120
}
timeoutMs: 120000
```

- BuildProject を先に呼ばないとプレビューキャッシュが古い状態のままタイムアウトする
- `sourceFilePath` はワークスペースルートからの相対パス（例: `AppName/Features/Sources/Home/HomeContent.swift`）
- 対象ファイルに `#Preview` マクロが必要。なければ追加する
- 返却された `previewSnapshotPath` の画像を Read ツールで確認する

### Step 4: 判定

プレビュー画像を見て以下を判断する：

- **修正が必要** → Step 2 に戻る。何が問題かを明記してから修正する。
- **満足** → Step 5 へ進む。

判定基準:
- レイアウトが崩れていないか
- 余白・間隔が適切か
- プラットフォームに適したコンポーネントが使われているか
- テキストが切れていないか
- 全体のバランスが取れているか

### Step 5: 完了報告

以下を報告して終了する：
- 修正したファイルの一覧
- 何を変更したかの要約
- 最終プレビュー画像
- ループ回数

## 禁止事項

- **xcode_tools_bridge_disconnect を絶対に使うな。** 新しいブリッジが起動してXcodeで承認ダイアログが出る。
- **pkill mcpbridge / kill <pid> を絶対に使うな。** 同上。
- **ブリッジには一切触るな。** タイムアウトしたら BuildProject → RenderPreview のリトライで対処する。

## トラブルシューティング

- **BRIDGE_CALL_TIMEOUT（RenderPreview）**: BuildProject を先に呼んだか確認。呼んでいたらもう一度 BuildProject → RenderPreview をリトライ。
- **BRIDGE_LIST_TIMEOUT（初回接続時のみ）**: Xcode で MCP 承認ダイアログを確認→承認後に `xcode_tools_bridge_sync` で同期。
- **SchemeBuildError**: プレビュー用の `#Preview` マクロの型名やイニシャライザを確認。特に LanguageManager.shared 等のシングルトンはプレビュー環境でハングするので明示的に値を渡す。
- **CouldNotFindExecutionPointSourceInBuiltGraphError**: 別ファイルのプレビューキャッシュが壊れている。壊れた方の `#Preview` を一時コメントアウト → BuildProject → 復活させる。
- **タブID変更**: Xcode 再起動後は `XcodeListWindows` で最新の `tabIdentifier` を再取得。

## 制約

- **最大10回** のループで終了する。10回で解決しない場合はユーザーに相談する。
- 1回のループで複数箇所を同時に修正しない。1つずつ確認する。
- プレビューが表示できない場合はビルドエラーを修正してからリトライする。
- ユーザーが Esc で中断した場合は、それまでの変更を報告する。
