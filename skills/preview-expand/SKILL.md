---
name: preview-expand
description: 指定された SwiftUI View ファイルの Preview を、典型的な状態を網羅するバリエーションに拡張する。引数にファイルの絶対パスを渡す。
---

# /preview-expand

SwiftUI View ファイルの `#Preview` ブロックを、そのビューの性質に応じた状態バリエーションに拡張するスキル。

## 手順

### 1. 対象ファイルの特定

引数（絶対パス）が渡された場合: そのファイルを対象とする。
引数なしの場合: `AskUserQuestion` で「どのファイルを対象にしますか？（絶対パスを教えてください）」と聞く。

### 2. ファイルを Read

`Read` ツールでファイル全体を読み込む。

- View の構造（プロパティ・引数・状態）を把握する
- 既存の `#Preview` ブロックをすべて把握する

### 3. 不足 variants を洗い出す

以下のリストから、**このビューの性質に応じて** 必要な variants を選択する（全部が必要とは限らない）:

| variant | 対象になる View の特徴 |
|---|---|
| `empty` | リスト・フィード・コレクション系（データゼロ状態） |
| `loading` | 非同期フェッチ・isLoading フラグを持つ View |
| `populated` | リスト・フィード（データが複数ある状態） |
| `error` | エラー状態・isError フラグを持つ View |
| `selected` | 選択可能アイテム・チェックボックス・トグル系 |
| `unread` | メッセージ・通知・バッジ系 |
| `disabled` | ボタン・入力フィールド・操作不可状態 |
| `dark mode` | 背景色・カラートークン依存が強い View |
| `long text` | タイトル・名前・本文が長い場合のレイアウト確認 |
| `no image` | アバター・サムネイルが nil の場合 |

既存 `#Preview` で既にカバーされている状態はスキップする。

### 4. `#if DEBUG` ブロックに variants を追加

`Edit` ツールを使って既存の `#Preview` ブロックを置き換えるか、末尾に追記する。

#### フォーマット例

```swift
#if DEBUG
// MARK: - Previews

#Preview("Default") {
    ExampleView(...)
}

#Preview("Empty") {
    ExampleView(items: [])
}

#Preview("Loading") {
    ExampleView(isLoading: true)
}

#Preview("Dark Mode") {
    ExampleView(...)
        .preferredColorScheme(.dark)
}
#endif
```

#### ルール

- 各 Preview に `"状態名"` のラベルをつける（ラベルなし Preview は1つだけ許容）
- `ViewState` や `ViewModel` を直接インジェクトできる場合はそちらを優先
- モックデータは `extension` の `static var mock` があれば使う、なければインラインで作る
- `#if DEBUG` ブロックで全 Preview を囲む（既にある場合はそのブロック内に収める）

### 5. 完了報告

追加した variants の一覧をユーザーに報告する。

```
✅ Preview variants を追加しました

対象: {ファイル名}
追加した variants:
  - Empty（データなし状態）
  - Loading（isLoading: true）
  - Dark Mode（カラースキーム反転）

既存: Default（変更なし）
```

## 禁止

- View の本体ロジックを変更しない（`#Preview` ブロック以外は触らない）
- 既存 Preview を削除しない
- モックデータのために新しいファイルを作らない（インラインで完結させる）
