---
name: produce-plan
description: 指定アプリ「固有」の宣伝戦略プランを立てる。`/produce-plan <アプリ名 or リポジトリパス>` で起動。アプリの型(macOSメニューバー/iOS/Web/CLI等)・武器・配布形態・ソース公開可否を判定し、効くチャネルだけを選定、コピー軸と動画コンセプトとローンチ順序まで設計してプランドキュメントをObsidian Valueに保存する。実行スキル /produce はこのプランを読んで動く。produce(汎用実行)の前段として固有戦略を固めるのが役割。
---

# /produce-plan

アプリ固有の宣伝戦略を立てるスキル。`/produce`（汎用の資産生成＆配信）の前段。

- `/produce-plan <アプリ>` … 戦略プランを作って Obsidian Value に保存
- その後 `/produce <アプリ>` … 保存されたプランを読んで資産生成＆配信を実行

iOS/Web/CLIなど毛色が違うアプリは必ず先に `/produce-plan` を通す。

## Phase A — 把握＆型判定
README(全言語)・project.yml/Package.swift/Info.plist・ランディングを読む。不明は仮定で埋めカード1枚で宣言→本人が差分訂正(質問攻めにしない)。
- 配布形態 = macOS DMG直配布 / Mac App Store / iOS App Store / Web / CLI・OSS ── チャネルを最も決める
- ソース = 公開 / 非公開(OSS限定チャネルの可否)
- 価格 / コア体験「○○を△△に変える」/ ターゲット / 対応OS(新OS専用は初速影響) / 既存素材(動画有無)
- 「だから何=手元に何が残るか」を1行で言えるか確認

## Phase B — 型→チャネルマッピング(核)
該当しないチャネルは「×やらない」と明記。
### macOSメニューバー/ユーティリティ(DMG直配布)
◎macmenubar.com(無料・Submitフォーム high) ◎Homebrew Cask(brew install --cask, LyricsX実例 high) ○AlternativeTo/awesome-mac/MacUpdate/Indie App Catalog ○Show HN(無料登録不要で有利 high) ○Product Hunt △Reddit r/macapps(90/10前提) ×OSS限定(closed-source不可 high)
### iOS/iPadOS(App Store)
◎ASO(タイトル/サブタイトル/キーワード/スクショ1枚目) ◎App Storeプレビュー動画 ○Product Hunt ○Reddit r/iosapps,r/apple ○TestFlight公開 △X動画 ×macmenubar/Homebrew/Show HN
### Web/SaaS
◎Show HN(ブラウザで即試せる) ◎Product Hunt ○専門サブReddit ○SEO(検索流入=最大のストック) △X動画
### CLI/開発者ツール/OSS
◎Show HN＋GitHub README(stars) ◎Homebrew/npm/awesome-* ◎OSS限定もOK ○dev.to/r/programming系

## Phase C — 武器の特定
見れば/触れば一発で伝わる強みを1つに絞る。視覚/操作の快/ニッチ刺さり/摩擦ゼロ。武器でPhase Bの優先度を再ソート。

## Phase D — 固有リサーチ(必要時のみ)
競合のローンチ事後分析/専門コミュニティ探索/ASO・SEOキーワード。手段=WebSearch・WebFetch、規模が要れば deep-research。得た主張は確証度を添える(反証は「やらない」へ)。

## Phase E — ローンチ設計(結論)
1. チャネル優先順位表(◎即/○花火/△仕込み/×やらない、確証度つき)
2. ローンチ順序(曜日でなく順序。例: 掲載→動画→Show HN/PH→Reddit)。曜日最適化は反証済みなので入れない
3. コピー軸(日英・master口調・誇張禁止・言い切り)
4. 動画コンセプト(武器を15秒でどう見せきるか。idleドリフト禁止・寄り切ったら静止)
5. 本人の正味作業見積り(動画キャプチャ/ログイン/本人レス)
6. このアプリ固有の注意点
※【重要】初期フォロワーゼロなら「X動画起点」は不発。初動はアルゴリズム拡散型(YouTube Shorts/TikTok/Reddit/HN)で発見を取る分岐を必ず入れる。

## 出力
`/Users/hondahikaru/Documents/輝/Claude Value/宣伝/<アプリ名>/produce-plan.md` に保存。Phase A〜Eを見出しに。既存があれば差分更新。保存後、要点を会話に短く出し本人の差分訂正を受ける。

## 共通の土台(produce と共有・繰り返さない)
HN規約(upvote依頼/誇張語/booster禁止)・Reddit 90/10・動画15秒・OSS限定除外・曜日最適化否定・@Ev0Dev資産化・外部公開は本人確認 ── `/produce` の絶対ルールに従う。
