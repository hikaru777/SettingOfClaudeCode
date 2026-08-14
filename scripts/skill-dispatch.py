#!/usr/bin/env python3
"""UserPromptSubmit hook — スキル発火のディスパッチ。

自作スキル(/ship /spec-lock /flow ...)が自発起動しない問題への機械的な矯正。
ユーザーの発話にキーワードが含まれたら、該当スキルを1行で思い出させる。

該当なしなら何も出さない（コンテキストを無駄に食わない）。
出力は常に 300 バイト以内。

パスに依存しないので Windows でもそのまま動く（python3 があれば可）。
"""
import json
import sys

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
    (("実装して", "実装しよ", "実装を", "進めて", "作って", "終わらせて", "続きやって", "続きを"),
     "実装の依頼 → 仕様が固まっているなら `ship` を叩くこと。未確定なら `spec-lock`。"),

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

    line = None
    for keywords, message in RULES:
        if any(k in prompt for k in keywords):
            line = message
            break

    if line is None:
        return 0

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
