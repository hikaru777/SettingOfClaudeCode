#!/usr/bin/env python3
"""一時的な調査用フック。PreToolUse(Edit|Write) の発火元を記録する。

目的: teammateMode を tmux にすると、ディレクターの編集と subagent の編集を
機械的に判別できるようになるかを確かめる。
判別できるなら「プロダクトのコード編集はディレクター禁止」を構造で強制できる。

調査が終わったら settings.json から外して削除すること。
"""
import json
import os
import sys

try:
    payload = json.load(sys.stdin)
except Exception as e:
    payload = {"_parse_error": str(e)}

record = {
    "payload_keys": sorted(payload.keys()),
    "payload_session_id": payload.get("session_id"),
    "env_session_id": os.environ.get("CLAUDE_CODE_SESSION_ID"),
    "child_session": os.environ.get("CLAUDE_CODE_CHILD_SESSION"),
    "tmux_pane": os.environ.get("TMUX_PANE"),
    "ppid": os.getppid(),
    "tool": payload.get("tool_name"),
    "file": (payload.get("tool_input") or {}).get("file_path"),
    "sid_match": payload.get("session_id") == os.environ.get("CLAUDE_CODE_SESSION_ID"),
}

with open("/tmp/probe-origin.jsonl", "a") as fh:
    fh.write(json.dumps(record, ensure_ascii=False) + "\n")

sys.exit(0)
