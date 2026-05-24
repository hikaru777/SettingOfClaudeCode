#!/usr/bin/env bash
# ~/.claude/scripts/swift-precheck.sh
#
# Swift 軽量構文・パターンチェッカー
# Claude Code PostToolUse hook から呼ばれる
# stdin: JSON { tool_input: { file_path: "..." }, ... }
#
# チェック内容:
#   1. 全角スペース (U+3000) の混入
#   2. 幻覚API: .foregroundStyle(.accent)
#   3. import Foundation 不足 (Date/DateFormatter 使用時)
#   4. swiftc -parse による構文チェック (型チェックなし・ms 単位)

set -uo pipefail

# ── stdin を先に全部読み込む (ヒアドック使用前に必須) ───────────────────────
INPUT=$(cat)

# ── stdin JSON からファイルパスを抽出 ────────────────────────────────────────
FILE=$(printf '%s' "$INPUT" | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" \
  2>/dev/null || true)

# ── .swift ファイル以外はスキップ ───────────────────────────────────────────
case "$FILE" in
  *.swift) ;;
  *) exit 0 ;;
esac

# ── ファイルが実在しない場合はスキップ ──────────────────────────────────────
[ -f "$FILE" ] || exit 0

FOUND_ISSUES=0

# ── 1. 全角スペース (U+3000 = UTF-8: \xe3\x80\x80) チェック ────────────────
if grep -q $'\xe3\x80\x80' "$FILE" 2>/dev/null; then
  echo "[swift-precheck] ⚠️  全角スペース(U+3000)が混入しています: $FILE" >&2
  FOUND_ISSUES=1
fi

# ── 2. 幻覚API: .foregroundStyle(.accent) チェック ──────────────────────────
if grep -qE '\.foregroundStyle\(\.accent\)' "$FILE" 2>/dev/null; then
  echo "[swift-precheck] ⚠️  幻覚API検出: .foregroundStyle(.accent) は存在しません" >&2
  echo "                    → .foregroundStyle(.tint) または .foregroundColor(.accentColor) を使ってください" >&2
  echo "                    ファイル: $FILE" >&2
  FOUND_ISSUES=1
fi

# ── 3. import Foundation 不足チェック ───────────────────────────────────────
# Date / DateFormatter / Calendar / DateComponents / TimeInterval を使っているのに
# import Foundation / SwiftUI / UIKit / AppKit がない場合に警告
if grep -qE '\b(Date|DateFormatter|Calendar|DateComponents|TimeInterval)\b' "$FILE" 2>/dev/null; then
  if ! grep -qE '^import (Foundation|SwiftUI|UIKit|AppKit)' "$FILE" 2>/dev/null; then
    echo "[swift-precheck] ⚠️  import Foundation が不足しています" >&2
    echo "                    (Date/DateFormatter/Calendar 等を使用中): $FILE" >&2
    FOUND_ISSUES=1
  fi
fi

# ── 4. swiftc -parse 構文チェック (型チェックなし) ──────────────────────────
# -parse: 構文解析のみ。コンパイル・型チェックを一切行わないため ms 単位で完了
SYNTAX_OUT=$(swiftc -parse "$FILE" 2>&1 | head -5 || true)
if [ -n "$SYNTAX_OUT" ]; then
  echo "[swift-precheck] ❌ 構文エラーを検出しました: $FILE" >&2
  echo "$SYNTAX_OUT" >&2
  FOUND_ISSUES=1
fi

# ── 結果 ─────────────────────────────────────────────────────────────────────
if [ "$FOUND_ISSUES" -eq 1 ]; then
  exit 1
fi

exit 0
