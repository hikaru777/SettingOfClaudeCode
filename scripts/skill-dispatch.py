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
# UserPromptSubmit はユーザーが直接入力した時にしか発火しない。
# teammate / subagent はユーザー入力を受け取らないので、ここを通るのは
# 「人と対話しているセッション = ディレクター」だけ。
# その session_id に印を付けておき、block-director-code-edit.py が参照する。
def _mark_director() -> None:
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
    _mark_director()

    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    prompt = payload.get("prompt") or ""
    if not isinstance(prompt, str) or not prompt.strip():
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
