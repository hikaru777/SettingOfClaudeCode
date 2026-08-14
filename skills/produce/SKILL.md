---
name: produce
description: 指定アプリの宣伝資産を一式生成し可能な範囲で配信まで実行する。`/produce <アプリ名 or リポジトリパス>` で起動。起動時に Claude Value/宣伝/<アプリ>/produce-plan.md があれば読みその固有戦略で動く。ストック掲載・コピー一式(X/Show HN/Product Hunt/Reddit)・faceless動画/Shorts台本を作り、X投稿(node x.mjs post)とフォーム入力(Chrome DevTools)は自動、HN/PH/Reddit認証は人間。複数アプリ量産者向けに人間の正味作業を10〜15分に固定する。
---

# /produce

宣伝を人間の正味作業10〜15分に圧縮して回す。土台は deep-research(107エージェント)検証済み事実。

## 起動
- `/produce <アプリ>` でアプリ名/パスから探す(~/app, ~/粋挺 等)。見つからなければ聞く。
- 起動直後に `/Users/hondahikaru/Documents/輝/Claude Value/宣伝/<アプリ>/produce-plan.md` を読む。あれば固有戦略で以下を上書き(Phase0は省略)。無ければ型がメニューバー以外なら先に `/produce-plan` を勧める。

## 設計思想
- ストック型(掲載/Homebrew/README/検索流入)は一発で全部やる。フロー型(SNS毎日投稿)は1アプリのためにやらない。
- 宣伝資産はアプリでなく作者@Ev0Devに貯める=新作のたび前作読者に届き固定費化。
- 初期フォロワーゼロなら動画起点は不発。初動はアルゴリズム拡散型(Shorts/TikTok/Reddit/HN)で発見を取る。
- 口調=master準拠。誇張・詩的ラベル禁止。言い切り。

## Phase 1 ストック資産(一回で永続)
- 多言語README(本体の対応言語に揃え、先頭に言語スイッチャー)。READMEに動くGIFを埋める。
- Homebrew Cask(macOS): brew install --cask が通る状態。自前tap(homebrew-<tap>)→push は本人GO後。DMG公証済みを明示。
- 掲載(closed-source可の一般ディレクトリを機械的に全部): macmenubar.com / MacUpdate / Indie App Catalog / awesome-mac(PR) / AlternativeTo。OSS限定は除外。
- フォーム入力は Chrome DevTools MCP で代行可、ログインは本人。CAPTCHAで詰まれば本人に渡す。

## Phase 2 コピー一式(日英・誇張禁止・言い切り)
- 1行キャッチ / X投稿(動画前提・フック先行) / Show HN(タイトル誇張語なし＋技術の中身を素直に＋最初のコメントで裏側開示) / Product Hunt(タグライン＋説明＋初コメ) / Reddit(自慢でなく「使う人いれば」)

## Phase 3 動画の弾(faceless=アプリ画面のみ)
- X用15秒: 無音→操作→コア体験の瞬間を最初の数秒で。idleドリフト禁止・寄り切ったら静止。
- YouTube Shorts/TikTok台本: hook3秒＋本体35-40秒＋クローズ。retention70%狙い。タイトル/説明/hashtag最適化。サムネ案。
- 監査チェック: hook3秒以内/タイトルにキーワード/説明に導線/縦9:16字幕焼き/長尺orチャンネル誘導

## Phase 4 配信
| 作業 | 実行 | 手段 |
| X投稿 | スキル | cd ~/app/twitter_api_safe_relay && node x.mjs post "<本文>"(疎通=whoami, reply=--reply <id>, queryId壊れたら refresh) |
| 掲載フォーム | スキル | Chrome DevTools。ログインは本人。CAPTCHA→本人 |
| Homebrew push | スキル | git push(本人GO後) |
| Show HN/PH/Reddit投稿 | 本人 | 文・画像はスキル用意、認証＋本人レスは人間 |
| TikTok/YouTube投稿 | 本人 | 台本・メタはスキル用意 |
X投稿は実行前に本文を本人に見せて確認。フォーム送信・push も同様に確認。

## Phase 5 継続(最小)
新作出たら@Ev0Devで言うだけ。アップデート時は差分の短い動画を1本。個別アプリの継続宣伝はしない。

## エラーパス
- アプリ未発見→探索範囲広げ、ダメなら本人に聞く
- produce-plan.md 陳腐化(アプリ更新後)→鮮度を本人に確認
- x.mjs失敗→refresh試行、ダメなら本人
- Chrome未ログイン/CAPTCHA→本人に渡す
- 動画素材なし→Phase3の動画生成はスキップし台本だけ用意、本人に撮影依頼

## 絶対ルール
upvote依頼/誇張語(best/first等)/booster/OSS限定への申請/曜日最適化/なりすまし禁止。外部公開(X投稿/フォーム送信/push)は必ず本人確認。「作成成功」を自己申告せず、検証(別コマンドのls/cat or 本人の ! cat)で確定する。

## 完了報告
1.生成資産の一覧(パス) 2.スキルが実行したこと 3.本人に残る正味作業(所要時間) 4.詰まった点。生成物は Claude Value/宣伝/<アプリ>/ に保存。
