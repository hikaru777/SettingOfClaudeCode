#!/usr/bin/env python3
"""PreToolUse(Edit|Write|MultiEdit) — ディレクターによるプロダクトコードの直接編集を止める。

CLAUDE.md「触ってよい物の線引き」の機械的な強制。

判別の仕組み:
  UserPromptSubmit はユーザーが直接入力した時にしか発火しない。teammate / subagent は
  ユーザー入力を受け取らないので、そこを通るのは「人と対話しているセッション = ディレクター」
  だけ。skill-dispatch.py が ~/.claude/.director-sessions/<session_id> に印を残すので、
  ここでは現在の session_id に印があるかどうかを見る。
  印がある = ディレクター → プロダクトコードの編集を止める。
  印がない = teammate / worker → 通す。

  ※ teammateMode: tmux で teammate が別プロセス・別 session_id になることを実測で確認済み
    （2026-08-15: ディレクター %1 / 7f0c678e に対し teammate は %3 / 77f32add）。

止めないもの（ディレクター業務として許可されている）:
  .md / .txt / .reports/ / ~/.claude 配下 / scratchpad / 一時ディレクトリ / Obsidian Vault

環境が想定と違う時は必ず通す（フェイルオープン）。作業を止める方が害が大きいため。
"""
import json
import os
import sys
import time

MARK_DIR = os.path.expanduser("~/.claude/.director-sessions")
METRICS = os.path.expanduser("~/.claude/.metrics")


def log(kind: str, **fields) -> None:
    """運用指標を記録する。ops-report.py が読む。失敗しても本処理は止めない。"""
    try:
        os.makedirs(METRICS, exist_ok=True)
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "kind": kind}
        rec.update(fields)
        with open(os.path.join(METRICS, "ops.jsonl"), "a") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass

ALLOWED_SUFFIX = (".md", ".txt", ".log", ".jsonl")
ALLOWED_SUBSTR = (
    "/.reports/",
    "/.claude/",
    "/scratchpad/",
    "/private/tmp/",
    "/tmp/",
    "/Documents/輝/",
    "/memory/",
)

MESSAGE = """BLOCKED: ディレクターはプロダクトのコードを直接編集できない（CLAUDE.md「触ってよい物の線引き」）。

  対象: {path}

  委譲すること:
    - 手で並べきれない数 / schema で型を強制 / 再開が要る / コンテキストを空けたい
      → Workflow
    - それ以外（既定）→ Agent で部署長を立て、部署長が worker を並列起動する

  「1行だけ」「簡単だから」は理由にならない。実測で30日576件がその論法で積み上がった。"""


def is_product_code(path: str) -> bool:
    if not path:
        return False
    if any(s in path for s in ALLOWED_SUBSTR):
        return False
    if path.endswith(ALLOWED_SUFFIX):
        return False
    return True


def is_director() -> bool:
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not sid:
        return False  # 判別できない → 通す
    return os.path.exists(os.path.join(MARK_DIR, sid))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # 読めない → 通す

    path = (payload.get("tool_input") or {}).get("file_path", "")
    if not is_product_code(path):
        return 0

    if not is_director():
        log("delegated_edit", path=path, tool=payload.get("tool_name"))
        return 0  # teammate / worker の編集は通す

    log("block", path=path, tool=payload.get("tool_name"))
    print(MESSAGE.format(path=path), file=sys.stderr)
    return 2  # exit 2 = ブロック


if __name__ == "__main__":
    sys.exit(main())
