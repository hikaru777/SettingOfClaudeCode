#!/usr/bin/env python3
"""ディレクターがプロダクトのコードを直接編集した回数を数える。

CLAUDE.md「触ってよい物の線引き」の遵守を検証するための計測。
機械的にブロックできない（in-process では編集主体を判別できない）ので、
違反が必ず数字に出るようにして、検証で守る。

判別方法:
  - 主スレッド = ~/.claude/projects/<dir>/*.jsonl の直下ファイル
  - 委譲先     = 同じ配下の subagents/**/*.jsonl（入れ子。ここは違反ではない）
  ※ 直下ファイルでも isSidechain: true の行は委譲先なので除外する

違反とみなすもの:
  主スレッドの Edit / Write / MultiEdit で、プロダクトのソースを触ったもの。
  .md / .reports/ / ~/.claude 配下 / scratchpad / 一時ディレクトリは対象外（規約上ディレクター可）。

使い方:
  python3 ~/.claude/scripts/count-director-edits.py [日数]   # 既定30日
  python3 ~/.claude/scripts/count-director-edits.py --weekly # 前回から7日経っていれば実行し記録する
"""
import json
import os
import sys
import time
from collections import Counter

STAMP = os.path.expanduser("~/.claude/.director-edit-audit.log")
WEEK = 7 * 86400

PROJECTS = os.path.expanduser("~/.claude/projects")
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}

# ディレクターが触ってよいもの（違反に数えない）
ALLOWED_SUFFIX = (".md", ".txt", ".log")
ALLOWED_SUBSTR = (
    "/.reports/",
    "/.claude/",
    "/scratchpad/",
    "/private/tmp/",
    "/tmp/",
    "/Documents/輝/",
    "/memory/",
)

EXCLUDE_DIRS = ("--claude-mem-observer-sessions", "-private-tmp-", "--claude-plugins-")


def is_product_code(path: str) -> bool:
    if not path:
        return False
    if any(s in path for s in ALLOWED_SUBSTR):
        return False
    if path.endswith(ALLOWED_SUFFIX):
        return False
    return True


def due_for_weekly() -> bool:
    """前回の週次監査から7日以上経っていれば True。"""
    try:
        return (time.time() - os.path.getmtime(STAMP)) >= WEEK
    except OSError:
        return True  # 一度も走っていない


def main() -> int:
    weekly = "--weekly" in sys.argv
    if weekly and not due_for_weekly():
        return 0  # まだ7日経っていない。何もしない

    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    days = int(args[0]) if args else 30
    cutoff = time.time() - days * 86400

    violations = Counter()
    delegated = 0
    scanned = 0

    for entry in os.listdir(PROJECTS):
        if any(x in entry for x in EXCLUDE_DIRS):
            continue
        base = os.path.join(PROJECTS, entry)
        if not os.path.isdir(base):
            continue
        for root, _dirs, files in os.walk(base):
            nested = "subagents" in root  # 委譲先の入れ子トランスクリプト
            for fn in files:
                if not fn.endswith(".jsonl"):
                    continue
                fp = os.path.join(root, fn)
                try:
                    if os.path.getmtime(fp) < cutoff:
                        continue
                except OSError:
                    continue
                scanned += 1
                try:
                    fh = open(fp, errors="ignore")
                except OSError:
                    continue
                for line in fh:
                    if '"tool_use"' not in line:
                        continue
                    try:
                        d = json.loads(line)
                    except Exception:
                        continue
                    if d.get("type") != "assistant":
                        continue
                    sidechain = bool(d.get("isSidechain"))
                    for c in d.get("message", {}).get("content", []) or []:
                        if not isinstance(c, dict) or c.get("type") != "tool_use":
                            continue
                        if c.get("name") not in EDIT_TOOLS:
                            continue
                        path = (c.get("input") or {}).get("file_path", "")
                        if not is_product_code(path):
                            continue
                        if nested or sidechain:
                            delegated += 1
                        else:
                            violations[path] += 1

    total = sum(violations.values())
    print(f"=== ディレクターの直接編集 監査（直近{days}日 / {scanned}ファイル走査）===")
    print(f"違反（主スレッドがプロダクトコードを編集）: {total} 件   ★ 規約上の目標はゼロ")
    print(f"参考: 委譲先による編集: {delegated} 件（これは正常）")
    if total:
        print("\n--- 違反の内訳 上位15 ---")
        for path, n in violations.most_common(15):
            print(f"{n:5}  {path.replace(os.path.expanduser('~'), '~')}")
    print("\n基準値: 576件/30日（2026-08-15 の線引き確定時点・本スクリプトでの実測）")

    if weekly:
        stamp = time.strftime("%Y-%m-%d %H:%M")
        with open(STAMP, "a") as fh:
            fh.write(f"{stamp}\t違反 {total} 件\t委譲 {delegated} 件\t（基準 576）\n")
        print(f"\n→ {STAMP} に記録した")
    return 0


if __name__ == "__main__":
    sys.exit(main())
