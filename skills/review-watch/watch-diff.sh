#!/usr/bin/env bash
# watch-diff.sh — *.swift の前回スナップショットとの unified diff を出力し、スナップショットをローテートする。
#
# usage:
#   watch-diff.sh <target> --where      # この target 用の状態ディレクトリ(BASE)を表示して終了
#   watch-diff.sh <target> [--reset]    # 差分を出力。--reset で「今」を基準に取り直す（snap のみ。ledger/state は温存）
#
# 出力マーカー（呼び出し側はこれで分岐する）:
#   __TARGET_NOT_FOUND__              : target が存在しない/ディレクトリでない（exit 3）
#   __BASELINE_ESTABLISHED__         : 初回/再取得。基準を取っただけ（レビュー不要）
#   <unified diff> ... __TICK_OK__   : 変更あり（diff を出した後に必ず __TICK_OK__）
#   __TICK_OK__ のみ                 : 変更なし
#   どのマーカーも無い                : スクリプト異常 → 呼び出し側はエラー扱い（無音で流すな）
set -eu

TARGET_IN="${1:?target dir required}"
MODE="${2:-}"

# --- TARGET 正規化（symlink 解決・存在検証）。存在しなければ loud に失敗 ---
if [ ! -d "$TARGET_IN" ]; then
  echo "__TARGET_NOT_FOUND__"
  exit 3
fi
TARGET="$(cd "$TARGET_IN" && pwd -P)"

# --- BASE を target から決定的に導出（呼び出し側はハッシュ計算不要＝表記揺れで孤児化しない）---
HASH="$(printf '%s' "$TARGET" | shasum | cut -c1-12)"
BASE="${TMPDIR:-/tmp}/review-watch/$HASH"

if [ "$MODE" = "--where" ]; then
  echo "$BASE"
  exit 0
fi

OLD="$BASE/snap"
NEW="$BASE/snap.new"
STALE_MIN=15   # snap がこれより古ければ自動で取り直す（監視が途切れた後は「今」が基準）

mkdir -p "$BASE"

# --- 同一 target の多重実行ガード（アトミック mkdir ロック）---
LOCK="$BASE/lock"
if ! mkdir "$LOCK" 2>/dev/null; then
  echo "__TICK_OK__"   # 別ティック処理中 → 今回はスキップ（変更なし扱い）
  exit 0
fi
trap 'rm -rf "$LOCK"' EXIT

# --- リセット判定: snap だけ消す（ledger.md / state は絶対に消さない）---
if [ "$MODE" = "--reset" ]; then
  rm -rf "$OLD" "$NEW"
elif [ -d "$OLD" ] && [ -n "$(find "$OLD" -maxdepth 0 -mmin +"$STALE_MIN" 2>/dev/null)" ]; then
  rm -rf "$OLD" "$NEW"
fi

# --- 現在の swift をミラー（cp ループ。macOS の symlink 付き temp でも安全）---
rm -rf "$NEW"; mkdir -p "$NEW"
while IFS= read -r -d '' f; do
  f="${f#./}"
  mkdir -p "$NEW/$(dirname "$f")"
  cp "$TARGET/$f" "$NEW/$f"
done < <(cd "$TARGET" && find . -name '*.swift' \
    -not -path '*/.build/*' \
    -not -path '*/.swiftpm/*' \
    -not -path '*/DerivedData/*' \
    -not -path '*/.git/*' -print0)

# --- 初回はベースライン確立のみ ---
if [ ! -d "$OLD" ]; then
  mv "$NEW" "$OLD"
  echo "__BASELINE_ESTABLISHED__"
  exit 0
fi

# --- 差分出力（パスを実プロジェクトパスへ整形 → file:line がクリック可能）---
diff -ruN "$OLD" "$NEW" \
  | sed -e "s#${OLD}/#${TARGET}/#g" -e "s#${NEW}/#${TARGET}/#g" || true

# --- ローテート（今回を次回の基準に）し、成功マーカーを必ず出す ---
rm -rf "$OLD"; mv "$NEW" "$OLD"
echo "__TICK_OK__"
