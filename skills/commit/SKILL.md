---
name: commit
description: 「コミットして」「commit して」「今の変更を記録して」と言われた時に必ず使う。自分から起動してよい。直近の変更をユーザー確認の上で git commit する。push は絶対しない。引数に commit メッセージの草案を渡してもよい。
---

# /commit

直近の変更を確認し、ユーザーの承認を得てから git commit するスキル。**push は絶対にしない。**

## 絶対ルール

- **push は絶対しない**（「pushっていうまでadd,commit,pushはするな」）
- `.env` / `GoogleService-Info.plist` / `Secrets.swift` は絶対に `git add` しない
- `--no-verify` は使わない（hooks をスキップしない）
- `--amend` は使わない（新規 commit を作る）

## 手順

### 1. 現状把握（並列実行）

以下を **同時に** 実行する:

```bash
git status
git diff HEAD  # staged + unstaged 両方
git log --oneline -5
```

### 2. 変更内容を分析

- **何が変わったか**（ファイル一覧・変更の種類）を把握
- **なぜ変わったか**（会話の文脈から推定）を考える
- `.env` / `GoogleService-Info.plist` / `Secrets.swift` が含まれていないか確認。含まれていたら **絶対に add しない**（ユーザーに警告する）

### 3. Conventional Commit メッセージ案を作成

以下のプレフィックスから適切なものを選択:

| prefix | 用途 |
|---|---|
| `feat:` | 新機能 |
| `fix:` | バグ修正 |
| `refactor:` | 動作変更なしのコード整理 |
| `style:` | フォーマット・命名など（ロジック変更なし） |
| `docs:` | ドキュメントのみ |
| `test:` | テストの追加・修正 |
| `chore:` | ビルド設定・依存・その他 |
| `perf:` | パフォーマンス改善 |

引数にメッセージ草案が渡された場合はそれをベースに整形する。

フォーマット:
```
{prefix}: {変更の要旨（命令形・英語 or 日本語）}

{変更の詳細（省略可）}
```

### 4. ユーザーに確認

`AskUserQuestion` で以下を聞く:

- 質問: 「このメッセージで commit しますか？」
- 選択肢:
  - 「このメッセージで commit する」（推奨）
  - 「メッセージを修正したい」
  - 「やめる（commit しない）」

### 5-a. OK の場合 → commit 実行

```bash
# 安全なファイルのみ add（secrets 系は除外）
git add {変更ファイル一覧から secrets を除いたもの}

# HEREDOC で commit メッセージを渡す
git commit -m "$(cat <<'EOF'
{確定したメッセージ}

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

commit 後に `git status` で成功を確認し、ユーザーに報告する。

### 5-b. 「修正したい」の場合

修正案を `AskUserQuestion` で聞いて、手順 4 に戻る。

### 5-c. 「やめる」の場合

「commit をキャンセルしました」と報告して終了。

## 禁止

- `git push` は絶対に呼ばない
- `git add .` や `git add -A` で全ファイルを一括 add しない（個別に列挙する）
- secrets ファイルを add しない
- `--no-verify` でフックをスキップしない
- 確認なしに commit を実行しない
