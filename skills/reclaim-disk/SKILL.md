---
name: reclaim-disk
description: Scan the Mac for unnecessary disk hogs (Xcode DerivedData, iOS Simulator cruft, old Downloads, ~/.claude/worktrees, Homebrew/npm/uv caches, Trash, stale Xcode DeviceSupport, VS Code/Cursor caches) and delete them safely with user approval. Use when the user says things like "容量空けて", "ディスク整理", "いらない容量食ってるもの消して", "Macの空き容量増やして", "reclaim disk", "disk cleanup". Always present the plan with reclaimable sizes before deleting, and never touch source code or user documents.
---

# reclaim-disk

Mac の無駄容量を洗い出して、安全なものから順にユーザー承認の上で削除していくスキル。開発ツールが再生成可能なキャッシュ・中間物を優先的に狩る。

## 哲学

- **絶対に消さない**: `~/Documents`, `~/Desktop`, `~/app`, `~/粋挺`, `~/.ssh`, `~/.config`（ユーザーの一次データ）
- **承認無しで消さない**: 全削除候補はサイズ付きでリスト提示、ユーザー承認後に実行
- **再生成可能を優先**: ビルド中間物・キャッシュ・ダウンロード済みインストーラが最初のターゲット
- **一気にやらない**: カテゴリ単位で「消す？」と聞く。大物は個別確認

## 手順

### 1. 現状把握

```bash
df -h / | grep -v Filesystem
du -sh ~/Library/Developer/Xcode/DerivedData \
       ~/Library/Developer/CoreSimulator/Devices \
       ~/Library/Developer/Xcode/iOS\ DeviceSupport \
       ~/Library/Developer/Xcode/Archives \
       ~/Library/Caches \
       ~/Library/Containers/com.apple.CoreSimulator.SimulatorTrampoline \
       ~/Downloads \
       ~/.Trash \
       ~/.claude/worktrees \
       ~/.npm ~/.cache ~/.cursor \
       ~/Library/Caches/Homebrew \
       2>/dev/null | sort -h
```

全体容量と TOP ディレクトリを一覧化してユーザーに提示。

### 2. 削除候補カテゴリ（安全順）

削除候補を以下のカテゴリごとにサイズ計測し、**合計サイズ付きの計画表**を提示する。

#### Tier 1: ほぼ無条件で安全（再生成可能・純粋キャッシュ）

| カテゴリ | コマンド |
|---|---|
| Xcode DerivedData | `rm -rf ~/Library/Developer/Xcode/DerivedData/*` |
| Xcode Archives（古い） | `find ~/Library/Developer/Xcode/Archives -mtime +90 -delete` |
| ゴミ箱 | `rm -rf ~/.Trash/*` |
| Homebrew キャッシュ | `brew cleanup -s && rm -rf $(brew --cache)` |
| npm キャッシュ | `npm cache clean --force` |
| uv キャッシュ | `uv cache clean` |
| pip キャッシュ | `rm -rf ~/Library/Caches/pip` |
| yarn/pnpm キャッシュ | `yarn cache clean 2>/dev/null; pnpm store prune 2>/dev/null` |
| macOS 汎用キャッシュ | `find ~/Library/Caches -mindepth 1 -maxdepth 2 -type d -mtime +30` をリストして確認 |

#### Tier 2: 確認が必要（状況依存）

| カテゴリ | 判定 |
|---|---|
| 使ってない iOS Simulator | `xcrun simctl delete unavailable` は無条件で実行 OK。加えて `xcrun simctl list devices` で古い OS の機種を列挙、ユーザーに「これ消していい？」 |
| 古い Xcode iOS DeviceSupport | `~/Library/Developer/Xcode/iOS DeviceSupport/` の古い iOS バージョンは消せる。現在接続する実機の iOS のみ残す |
| `~/.claude/worktrees` | `git worktree list` で参照されていないディレクトリを列挙。中で作業中のものがないか `git status` で確認してから削除 |
| Downloads 内の .xip/.dmg/.pkg/.zip | `find ~/Downloads -size +100M` でリスト、ユーザーに個別確認 |
| VS Code / Cursor のワークスペースキャッシュ | `~/Library/Application Support/Code/Cache*`, `~/.cursor` 内の `CachedData` など |
| Docker イメージ | `docker system df` で確認後、`docker system prune -a` はユーザー許可必須 |
| 古い iOS/macOS .ipsw/.xip | Downloads にある古いインストーラ |

#### Tier 3: 慎重に（消すと困る可能性あり）

| カテゴリ | 備考 |
|---|---|
| `~/Library/Application Support/Claude` | Claude Desktop アプリのデータ。10GB 超でも消すな。ユーザーに必ず聞く |
| `~/Library/Containers/*` | アプリのサンドボックス。アプリごとに確認 |
| Arc/Chrome/Firefox プロファイル | ブラウザ履歴・ログイン情報。消すな |
| `~/.claude/projects` | 会話履歴。消すな（ユーザー明示指示時のみ） |

### 3. 削除前に計画を提示

フォーマット例：

```
🧹 削除計画

Tier 1（安全・即消し可）:
  DerivedData        20GB
  Trash              5GB
  Homebrew cache     2GB
  npm cache          1GB
  ----
  小計              28GB

Tier 2（要確認）:
  simctl unavailable      5GB  [推奨: 消す]
  ~/Downloads の Xcode.xip ×2  4.4GB  [推奨: 消す]
  古い iOS DeviceSupport (iOS 17) 2GB  [推奨: 消す]
  ----
  小計              11.4GB

合計: 39.4GB 回収見込み

Tier 1 だけ先に消す？全部やる？個別に確認する？
```

### 4. ユーザー承認後、カテゴリ単位で実行

- 各カテゴリ削除後に `df -h /` で空き容量の変化を報告
- 長時間かかる削除は `run_in_background: true` で実行し、後で結果回収

### 5. 仕上げ

```bash
df -h /
```

最終空き容量を一行で報告。「前回 X → 今 Y、+Z GB 回収」と差分を示す。

## 絶対禁止事項

- **`~/Documents`, `~/Desktop`, `~/app`, `~/粋挺`, `~/Library/Mobile Documents` (iCloud)** は絶対に触らない
- `~/.ssh`, `~/.config`, `~/.gitconfig`, `~/.zshrc` 等の設定ファイルは触らない
- `sudo rm` は絶対に使わない。システム領域は触らない
- `rm -rf /` 系の typo リスクがあるコマンドは変数展開を必ず確認してから実行
- Git worktree を消す前は `cd` して `git status` で未コミット変更がないことを確認
- ユーザーの承認なしに Tier 2/Tier 3 のものを消さない

## ユースケース

- 「容量が限界」「Mac の空き増やして」と言われたとき
- ビルドが「No space left on device」で失敗したとき
- メモリ swap が肥大していて、根本原因がディスク圧迫にあるとき
