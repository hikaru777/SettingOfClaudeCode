---
name: disband-agents
description: Disband Claude Code sub-agents spawned inside the CURRENT tmux session only — kills agent panes in this session (excluding the current pane), and wipes the teams/tasks entries owned by this session. Use when the user says things like "チーム解散", "全エージェント消して", "disband all", "エージェント全部落として", "他のエージェントも消して", "クリーンな状態にして". Do NOT touch other tmux sessions. Do NOT kill the current pane.
---

# disband-agents

現在の tmux セッション内で立ち上げたサブエージェント（OMC チーム駆動の Claude プロセス）と、このセッションが作ったチーム/タスク定義だけを解散・削除するスキル。**他のセッションには絶対に触らない**。

## いつ使うか

- ユーザーが「チーム解散」「全部消して」「他のエージェント落として」等と明示的に指示したとき
- 新しい作業に入る前に、今のセッションのエージェントだけクリーンにしたいとき

**使わないケース**: 現在作業中の単一タスクを中断したいだけのとき、または他の tmux セッション（別の Claude 会話）にも影響を及ぼしたいとき。このスキルは**現セッション限定**。

## 前提

- 現在のセッションは tmux 上で動いている
- 他の tmux セッションに別の Claude 会話が走っている可能性があるので、`-a`（全セッション対象）の列挙・kill は禁止
- 現在のペインを誤って殺さないこと（自殺すると会話ごと落ちる）

## 手順

### 1. 現在のセッション名とペインを特定

```bash
CURRENT_SESSION=$(tmux display-message -p '#{session_name}')
CURRENT_PANE=$(tmux display-message -p '#{session_name}:#{window_index}.#{pane_index}')
echo "session: $CURRENT_SESSION"
echo "current pane: $CURRENT_PANE"
```

### 2. 現セッション内の Claude ペインを列挙

`tmux list-panes -t "$CURRENT_SESSION"` を使う。**`-a` は使わない**（他セッションを巻き込む）。

```bash
tmux list-panes -s -t "$CURRENT_SESSION" \
  -F "#{session_name}:#{window_index}.#{pane_index} | #{pane_current_command} | #{pane_title}"
```

`-s` はそのセッションの全ウィンドウ横断。ウィンドウが 1 つなら `-t` だけでも可。

### 3. 現セッション内の自分以外の Claude ペインだけを kill

```bash
tmux list-panes -s -t "$CURRENT_SESSION" \
  -F "#{session_name}:#{window_index}.#{pane_index}|#{pane_current_command}" \
  | grep -E "\|2\.1\." \
  | awk -F'|' '{print $1}' \
  | grep -v "^${CURRENT_PANE}$" \
  | while read pane; do tmux kill-pane -t "$pane" 2>&1; done
```

**注意**: ペインを kill するとインデックスが詰まる。取りこぼしたら再実行。

### 4. 残存ペインを確認（現セッション内のみ）

```bash
tmux list-panes -s -t "$CURRENT_SESSION" \
  -F "#{session_name}:#{window_index}.#{pane_index} | #{pane_title}" \
  | grep -v "^${CURRENT_PANE} "
```

Claude スピナー（`✳`/`⠐`/`⠂`）が残っていたら手順 3 を再実行。

### 5. このセッションが作ったチーム・タスク定義だけ削除

全削除は禁止（他セッションのチームも消える）。`~/.claude/teams/*/config.json` の `leadSessionId` が現在のセッション ID と一致するものだけを対象にする。

```bash
echo "current session id: $CLAUDE_SESSION_ID"
ls ~/.claude/teams/ 2>/dev/null
```

```bash
# leadSessionId が一致するチームだけ削除
for dir in ~/.claude/teams/*/; do
  [ -f "$dir/config.json" ] || continue
  lead=$(jq -r '.leadSessionId // empty' "$dir/config.json" 2>/dev/null)
  if [ "$lead" = "$CLAUDE_SESSION_ID" ]; then
    team=$(basename "$dir")
    rm -rf "$dir" ~/.claude/tasks/"$team"
    echo "disbanded: $team"
  fi
done
```

`leadSessionId` フィールドが無い古い形式は、ユーザーに確認してから個別削除。勝手に全消ししない。

### 6. 最終確認

```bash
tmux list-panes -s -t "$CURRENT_SESSION" | wc -l
ls ~/.claude/teams/
```

ユーザーに「現セッションのエージェント解散・残ペイン N」と一行報告して終了。

## 注意事項

- **`tmux list-panes -a` は使うな**。他セッションの Claude を巻き添えにする（過去の実害あり）。
- **絶対に現在のペインを kill するな**。自殺 = 会話喪失。
- **`rm -rf ~/.claude/teams/* ~/.claude/tasks/*` は禁止**。他セッションのチーム定義まで消える。
- tmux が動いていないシェル環境では即エラーで抜ける。
- `.omc/state/sessions/` 配下は触らない。
