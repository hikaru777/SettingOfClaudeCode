---
name: next
description: 「次のやつ」「溜まってるの消化して」「積んだタスクやって」と言われた時に必ず使う。自分から起動してよい。Claude Inbox の先頭1件だけを取り出して、それだけにフォーカスして実行する。inbox に溜めたタスクを「1件1集中」で消化する運用の主役。複数キューがあっても次の1件以外は読まない。
---

# /next

Claude Inbox の **先頭1件** を pop して、それ**だけ**にフォーカスして実行するスキル。

## 哲学

- 縦積みされたタスクを「一括 bulk read してまとめて処理」するのは禁止
- 1ターンで扱うのは pop した1件のみ
- 次のタスクは、ユーザーが再度 `/next` を叩いたら取りに行く
- これが「縦積みしたタスクが浅く読まれて雑に処理される」問題の防御線

## 手順

### 1. 先頭タスクを pop

`mcp__claude-inbox__inbox_pop` を呼ぶ。

- 戻り値が `null` (キュー空): `📥 Inbox は空です` と1行報告して終了
- 戻り値があれば、そのタスクの `id` と `text` をローカル変数に控える

### 2. ピックアップ報告

ユーザーに以下フォーマットで宣言：

```
🎯 着手: {text}
   id: {id の先頭8文字}
```

これでユーザーは「どのタスクが拾われたか」を即把握できる。

### 3. タスク実行

`text` の内容に従って実装・調査・修正を実施する。

- 必要なファイル読み込み・編集・コマンド実行はすべてここで行う
- 通常のタスクと同じ品質で対応する（手抜きしない）
- 不明点で詰まったら `mcp__claude-inbox__inbox_await_user(id, question)` を呼んで `awaiting_user` 状態に遷移し、ユーザーへ質問してターン終了

### 4. 完了報告 → MCP に書き戻し

タスクが完遂したら：

1. 何を変更したかの要約を1〜3文で作成
2. 変更ファイルがあれば diff サマリ（変更ファイル一覧 + 簡潔な説明）を作成
3. `mcp__claude-inbox__inbox_complete(id, summary, diff_summary?)` を呼ぶ
4. ユーザーに完了報告：
   ```
   ✅ 完了: {text}
      {summary}
      
      変更:
      {diff_summary}
   ```

### 5. ターン終了

**自動で次のタスクには進まない**。ユーザーが再度 `/next` を叩くまで待つ。

## 禁止

- 複数タスクを bulk pop しない（pop は1回だけ）
- inbox 内の他のタスクを覗き見しない
- 「ついでに」関連タスクをまとめてやらない
- 完了後に勝手に次の `/next` を呼ばない

## 対応する MCP tools

- `mcp__claude-inbox__inbox_pop`
- `mcp__claude-inbox__inbox_complete(id, summary, diff_summary?)`
- `mcp__claude-inbox__inbox_await_user(id, question)`
