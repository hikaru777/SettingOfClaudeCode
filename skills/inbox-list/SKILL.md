---
name: inbox-list
description: Claude Inbox に溜まっているタスクの一覧を表示する。`/inbox` (引数なし) と同等だが明示的に呼ぶ用。
---

# /inbox-list

Claude Inbox の現在のキュー状態を表示する read-only スキル。

## 手順

1. `mcp__claude-inbox__inbox_list` を `status: "all"` で呼ぶ
2. 結果を以下フォーマットで表示：

```
📥 Claude Inbox

🟡 pending (N)
  - {text} (#{id8})

🔵 in_progress (N)
  - {text} (#{id8})

🟠 awaiting_user (N)
  - {text} (#{id8})
    Q: {question}

⚪ done (N) — 直近3件のみ表示
  - {text} → {summary}
```

何もなければ `📥 Inbox は空です`。

## 禁止

- タスクを実行しない
- 状態を変更しない（read-only）

## 対応する MCP tools

- `mcp__claude-inbox__inbox_list(status: "all")`
