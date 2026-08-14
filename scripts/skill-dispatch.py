#!/usr/bin/env python3
"""UserPromptSubmit hook — スキル発火のディスパッチ。

自作スキル(/ship /spec-lock /flow ...)が自発起動しない問題への機械的な矯正。
ユーザーの発話にキーワードが含まれたら、該当スキルを1行で思い出させる。

該当なしなら何も出さない（コンテキストを無駄に食わない）。
出力は常に 300 バイト以内。

パスに依存しないので Windows でもそのまま動く（python3 があれば可）。
"""
import json
import os
import sys
import time

METRICS = os.path.expanduser("~/.claude/.metrics")


def _log(kind: str, **fields) -> None:
    """運用指標を記録する。ops-report.py が読む。失敗しても本処理は止めない。"""
    try:
        os.makedirs(METRICS, exist_ok=True)
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "kind": kind}
        rec.update(fields)
        with open(os.path.join(METRICS, "ops.jsonl"), "a") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass

# --- ディレクター識別の印を残す ---------------------------------------------
# 当初「UserPromptSubmit はユーザーが直接入力した時にしか発火しない」と考えていたが、
# これは誤りだった（2026-08-15 実測）。teammate も次の経路でこのフックを通る:
#   - ディレクターからの SendMessage
#   - <task-notification>（子エージェントの完了通知）
#   - <cross-session-message>（他セッションからの着信）
# そのため印が teammate にも付き、worker のコード編集が誤ってブロックされた（実測5件）。
#
# 対策: 機械が生成した入力を弾き、人が打った発話だけで印を付ける。
# 判定を誤るなら「印を付けない」側に倒す（印が無ければブロックは通すので作業が止まらない）。

# 人の入力ではないもの（先頭がこれで始まる／これを含む）
_MACHINE_MARKERS = (
    "<task-notification>",
    "<cross-session-message",
    "<teammate-message",
    "Another Claude session sent a message",
    "[SYSTEM NOTIFICATION",
    "<system-reminder>",
    "<local-command-",
)


def _is_teammate_pane() -> bool:
    """自分が teammate のペインで動いているか。

    teammateMode: tmux では teammate は別ペインで立ち、ペインタイトルに
    エージェント名が入る（実測: `%1 Mac` がディレクター、`%3 sid-probe` が teammate）。
    ディレクターのペインはホスト名のまま。tmux 外なら判定不能で False。
    """
    pane = os.environ.get("TMUX_PANE")
    if not pane or not os.environ.get("TMUX"):
        return False
    try:
        import subprocess
        r = subprocess.run(
            ["tmux", "display-message", "-p", "-t", pane, "#{pane_title}"],
            capture_output=True, text=True, timeout=3,
        )
        title = (r.stdout or "").strip()
    except Exception:
        return False
    if not title:
        return False
    # ホスト名（= ディレクターのペイン）なら teammate ではない
    try:
        import socket
        host = socket.gethostname().split(".")[0]
    except Exception:
        host = ""
    return title != host and not title.startswith(host)


def _is_human_input(prompt: str) -> bool:
    """人がキーボードで打った発話か。判断がつかない時は False（安全側）。"""
    if not prompt or not prompt.strip():
        return False
    # teammate のペインで動いているなら、届く入力は全て機械由来
    if _is_teammate_pane():
        return False
    head = prompt.lstrip()[:400]
    return not any(m in head for m in _MACHINE_MARKERS)


def _mark_director(prompt: str) -> None:
    if not _is_human_input(prompt):
        return
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not sid:
        return
    d = os.path.expanduser("~/.claude/.director-sessions")
    try:
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, sid), "w").close()
    except OSError:
        pass

# (キーワード群, 注入する一行) — 上から評価し、最初に当たったものだけを出す
RULES = [
    (("宣伝", "広め", "告知", "ローンチ", "リリースを打ち出"),
     "宣伝の依頼 → `produce`（方針が未定なら先に `produce-plan`）を叩いてから動くこと。"),

    (("作りながら", "とりあえず形", "動かしながら"),
     "作りながら決める依頼 → `flow` を叩いてから動くこと。"),

    # ★ 実装の動詞を構想の語より先に置く。両方混ざったプロンプト
    #   （例「仕様は決まってる、実装して。どう思う？」）では実装側を優先する。
    #   ship の一行自体が「未確定なら spec-lock」と両にらみになっているため、
    #   取り違えた時の損失がこちら向きの方が小さい。
    (("実装して", "実装しよ", "実装を", "進めて", "作って", "終わらせて", "続きやって", "続きを",
      "直して", "修正して", "バグ", "リファクタ", "エラーを", "落ちる", "動かない"),
     "実装の依頼 → **プロダクトのコードを自分で編集するな。必ず委譲する**。仕様が固まっているなら `ship`、未確定なら `spec-lock`。"),

    (("作りたい", "どう思う", "アイデア", "相談", "仕様を詰め", "考えたい"),
     "構想段階の相談 → `spec-lock` を叩いてから動くこと。決めつけで実装に入らない。"),

    (("デザイン", "UI を", "UIを", "画面を", "フロント", "見た目"),
     "UI を書く/直す → プラグインスキル `frontend-design` を先に読むこと（Web の場合）。"),

    (("レビュー", "見てほしい", "チェックして"),
     "レビュー依頼 → 組み込みの `/code-review` が正。superpowers の review 系には流れない。"),
]

MAX_BYTES = 300


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    prompt = payload.get("prompt") or ""
    if not isinstance(prompt, str) or not prompt.strip():
        return 0

    # 人が打った発話の時だけディレクターの印を付ける
    _mark_director(prompt)

    # 機械由来の入力にはスキル注入もしない（teammate に的外れな指示が入るのを防ぐ）
    if not _is_human_input(prompt):
        return 0

    line = None
    hit = None
    for keywords, message in RULES:
        for k in keywords:
            if k in prompt:
                line, hit = message, k
                break
        if line:
            break

    if line is None:
        _log("no_dispatch", head=prompt[:50])
        return 0

    # 誤検知率をあとで測れるように、当たった語とプロンプト冒頭を残す
    _log("dispatch", keyword=hit, rule=line[:24], head=prompt[:50])

    context = "[SKILL-DISPATCH] " + line
    while len(context.encode("utf-8")) > MAX_BYTES:
        context = context[:-1]

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": context,
            }
        },
        sys.stdout,
        ensure_ascii=False,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
