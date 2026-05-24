---
name: inbox
description: Claude Inbox にタスクを追加 / 一覧表示する。`/inbox <タスク内容>` で末尾にタスク追加、`/inbox` (引数なし) でアクティブなタスク一覧を表示。話す必要のない「後でやって欲しい」タスクを縦積みする運用。実行や消化は `/next` を使う。
---

# /inbox

Claude Inbox の入口スキル。タスクの追加と一覧表示のみ行う。**消化（実行）はしない** — それは `/next` の役目。

## 振る舞い

### 引数あり: タスク追加

`/inbox <text>` の形で呼ばれた場合、`<text>` をそのまま inbox キューの末尾に追加する。

実行手順：

1. MCP tool `mcp__claude-inbox__inbox_add` を呼ぶ。`text` 引数に渡されたテキストを丸ごと渡す
2. 戻り値の `task.id` と `task.text` を1行で報告する：
   ```
   ✓ inbox に追加: {text} (#{id の先頭8文字})
   ```
3. **追加だけで止まる**。消化はしない

### 引数なし: 一覧表示

引数が空の場合、`mcp__claude-inbox__inbox_list` を `status: "active"` で呼び、pending / in_progress / awaiting_user のタスクを以下の形式で表示：

```
📥 Inbox (N 件)
  1. [pending] {text}
  2. [in_progress] {text}
  3. [awaiting_user] {text} — Q: {question}
```

何もなければ `📥 Inbox は空です`。

## 禁止

- 追加されたタスクを勝手に着手しない（消化は `/next` の責務）
- ユーザーに「やりますか？」と確認しない（追加だけでターン終了）
- inbox の中身を編集・削除しない（クリーンアップは `/inbox-clear` または手動）

## 対応する MCP tools

- `mcp__claude-inbox__inbox_add(text)`
- `mcp__claude-inbox__inbox_list(status?)`
