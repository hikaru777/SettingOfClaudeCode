#!/usr/bin/env python3
"""運用指標の総合レポート。2026-08-15 に決めた規律が実際に効いているかを1枚で見る。

見るもの:
  1. ディレクターのコード直接編集 … ブロック発動数 / すり抜けた違反数（目標ゼロ）
  2. スキル発火 … 注入数・当たった語・実際にスキルが起動された数（誤検知の目安）
  3. 委譲の実態 … Agent / Workflow / Skill の起動数
  4. 脱出口 … ディレクター印を消してブロックを外した形跡

データ源:
  ~/.claude/.metrics/ops.jsonl … フックが書く即時ログ（block / dispatch / delegated_edit）
  ~/.claude/projects/**/*.jsonl … 実際のツール使用（Skill・Agent・Workflow・Edit）

使い方:
  python3 ~/.claude/scripts/ops-report.py [日数]     # 既定7日
  ※ /prompt-coach を回す時は、これも一緒に出して総合で見ること
"""
import json
import os
import sys
import time
from collections import Counter

HOME = os.path.expanduser("~")
METRICS = os.path.join(HOME, ".claude/.metrics/ops.jsonl")
PROJECTS = os.path.join(HOME, ".claude/projects")

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
EXCLUDE_DIRS = ("--claude-mem-observer-sessions", "-private-tmp-", "--claude-plugins-")

ALLOWED_SUFFIX = (".md", ".txt", ".log", ".jsonl")
ALLOWED_SUBSTR = (
    "/.reports/", "/.claude/", "/scratchpad/",
    "/private/tmp/", "/tmp/", "/Documents/輝/", "/memory/",
)


def is_product_code(path: str) -> bool:
    if not path:
        return False
    if any(s in path for s in ALLOWED_SUBSTR):
        return False
    if path.endswith(ALLOWED_SUFFIX):
        return False
    return True


def read_metrics(cutoff_str: str):
    """フックの即時ログを読む。"""
    out = []
    if not os.path.exists(METRICS):
        return out
    for line in open(METRICS, errors="ignore"):
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get("ts", "") >= cutoff_str:
            out.append(d)
    return out


def scan_transcripts(cutoff: float):
    """実際のツール使用をログから数える。主スレッドと委譲先を分ける。"""
    stats = {
        "skill": Counter(), "agent": 0, "workflow": 0,
        "violation": Counter(), "delegated_edit": 0, "files": 0,
    }
    if not os.path.isdir(PROJECTS):
        return stats
    for entry in os.listdir(PROJECTS):
        if any(x in entry for x in EXCLUDE_DIRS):
            continue
        base = os.path.join(PROJECTS, entry)
        if not os.path.isdir(base):
            continue
        for root, _dirs, files in os.walk(base):
            nested = "subagents" in root
            for fn in files:
                if not fn.endswith(".jsonl"):
                    continue
                fp = os.path.join(root, fn)
                try:
                    if os.path.getmtime(fp) < cutoff:
                        continue
                except OSError:
                    continue
                stats["files"] += 1
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
                    side = nested or bool(d.get("isSidechain"))
                    for c in d.get("message", {}).get("content", []) or []:
                        if not isinstance(c, dict) or c.get("type") != "tool_use":
                            continue
                        name = c.get("name")
                        inp = c.get("input") or {}
                        if name == "Skill":
                            stats["skill"][inp.get("skill", "?")] += 1
                        elif name == "Agent":
                            stats["agent"] += 1
                        elif name == "Workflow":
                            stats["workflow"] += 1
                        elif name in EDIT_TOOLS:
                            path = inp.get("file_path", "")
                            if not is_product_code(path):
                                continue
                            if side:
                                stats["delegated_edit"] += 1
                            else:
                                stats["violation"][path] += 1
    return stats


def main() -> int:
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    cutoff = time.time() - days * 86400
    cutoff_str = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(cutoff))

    m = read_metrics(cutoff_str)
    kinds = Counter(x.get("kind") for x in m)
    s = scan_transcripts(cutoff)
    violations = sum(s["violation"].values())

    print(f"╭─ 運用レポート（直近{days}日 / {s['files']}ファイル走査）")
    print("│")
    print("├─ 1. ディレクターのコード直接編集")
    print(f"│    ブロック発動 ............ {kinds.get('block', 0):>5} 回  ← 機械が止めた")
    print(f"│    すり抜けた違反 .......... {violations:>5} 件  ← ★目標ゼロ")
    print(f"│    委譲先による編集 ........ {s['delegated_edit']:>5} 件  （正常）")
    if violations:
        print("│    違反の内訳 上位5:")
        for p, n in s["violation"].most_common(5):
            print(f"│      {n:>3}  {p.replace(HOME, '~')}")
    print("│")
    print("├─ 2. スキル発火")
    disp = kinds.get("dispatch", 0)
    nodisp = kinds.get("no_dispatch", 0)
    skill_total = sum(s["skill"].values())
    print(f"│    注入した ............... {disp:>5} 回 / 全 {disp + nodisp} 発話")
    print(f"│    実際に Skill を起動 .... {skill_total:>5} 回  （基準: 7日で3回）")
    if disp:
        kw = Counter(x.get("keyword") for x in m if x.get("kind") == "dispatch")
        print(f"│    当たった語 上位5: {', '.join(f'{k}({n})' for k, n in kw.most_common(5))}")
    if s["skill"]:
        print(f"│    起動されたスキル: {', '.join(f'{k}({n})' for k, n in s['skill'].most_common(8))}")
    print("│")
    print("├─ 3. 委譲の実態")
    print(f"│    Agent 起動 ............. {s['agent']:>5} 回")
    print(f"│    Workflow 起動 .......... {s['workflow']:>5} 回")
    print("│")
    print("├─ 4. 脱出口")
    mark_dir = os.path.join(HOME, ".claude/.director-sessions")
    n_marks = len(os.listdir(mark_dir)) if os.path.isdir(mark_dir) else 0
    print(f"│    ディレクター印 ......... {n_marks:>5} 個  （0 ならブロックは無効化されている）")
    print("│")
    print("╰─ 判定: " + ("★ 違反あり。原因を報告すること" if violations else "違反ゼロ"))
    print("\n※ /prompt-coach を回す時は、このレポートも一緒に出して総合で見ること")
    return 0


if __name__ == "__main__":
    sys.exit(main())
