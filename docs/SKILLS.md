# スキル索引（正本・2026-08-15）

★★★ これが唯一の正本。CLAUDE.md の発火表は「会話で即叩くもの」の抜粋であり、
**委譲プロンプトを書く時はこの索引を引くこと**。表を他所に複製しない（必ずずれる） ★★★

使い方は2つ。

1. **ディレクターが会話中に自分で叩く** … 状況が下表に当たったら Skill ツールで起動する
2. **ディレクターが部署長・worker に渡すプロンプトに書き込む** … 「〜する時は `xxx` を使え」と明記して渡す。
   渡さなければ相手はスキルの存在を知らない（エージェント定義にスキル一覧は入っていない）

---

## 段取り・進行（どの領域でも最初に効く）

| 状況 | 使うもの |
|---|---|
| 構想がまだ固まっていない。「作りたい」「どう思う」「相談」 | `spec-lock` |
| 半分決まっていて、残りは物を見ないと決められない | `flow` |
| 仕様が固まっている。「実装して」「進めて」「終わらせて」 | `ship` |
| 後でやるタスクを渡された／溜まったものを消化する | `inbox` / `next` / `inbox-list` |
| 変更を記録する（push はしない） | `commit` |
| 定期的に繰り返し実行したい | `loop`（ハーネス組み込み） |
| 思考を広げる・整理する | `/think` / `product-advisor` |

## iOS / Swift

| 状況 | 使うもの |
|---|---|
| View を書いた直後、状態を網羅した Preview が要る | `preview-expand` / `/preview` / `/preview-loop` |
| ビルドする・シミュレーターで動かす | `/build` / `/run` / `/simulator` |
| Swift の検証 | `/verify-swift` |
| 型・定義を正確に読む | swift-lsp（プラグイン。ツールとして常駐） |
| Preview 描画 / Swift REPL / Apple ドキュメント検索 | Xcode MCP（`xcode`。**Xcode 起動中のみ**動く） |
| デザインを詰める | `~/.claude/docs/DESIGN.md` を読ませる |
| App Store Connect 関連 | `asc-app-create-ui` / `asc-iap-attach` / `asc-privacy-nutrition-labels` / `asc-team-key-create` |
| 自分の手で書いた Swift を見張ってほしい | `review-watch` |

★ エージェントに `xcodebuild` を走らせない（Preview が遅延する）。最終ビルドは人か team-lead。

## Web / フロントエンド

| 状況 | 使うもの |
|---|---|
| **UI を新規に書く・作り直す** | `frontend-design`（プラグイン。AI っぽい既視感を避ける） |
| ブラウザで実際の描画を確認する・操作する（**手元の dev サーバー / localhost**） | chrome-devtools（MCP。2,072回/30日 稼働中の主力） |
| **WebSearch が届かない公開サイトを直接見に行く / JS レンダリングが要るページを読む / 本番サイトを監視する** | `kitesurf`（MCP。Cloudflare 上のクラウドブラウザ。**localhost には届かない**ので手元の dev サーバー検証には使えない） |
| Next.js / Vercel 全般 | `vercel:nextjs` ほか vercel プラグインの約29スキル |
| ライブラリの最新 API を書く | `context7`（MCP。学習データが古い前提で必ず引く） |
| LCP・パフォーマンス改善 | `chrome-devtools-mcp:debug-optimize-lcp` |
| アクセシビリティ監査 | `chrome-devtools-mcp:a11y-debugging` |

★ dev 稼働中に `next build` を走らせない（共有 `.next` が壊れて全ルート 500）。型検証は `npx tsc --noEmit`。

## 検証・レビュー

| 状況 | 使うもの |
|---|---|
| コードレビュー | `/code-review`（組み込み。`ultra` で多エージェント） |
| 重複・簡素化のみ見たい | `/simplify`（組み込み） |
| セキュリティ観点 | `/security-review`（組み込み）。編集時の警告は security-guidance が自動で走る |
| 画面収録・動画の中身を読む | `video` |

## 公開・宣伝

| 状況 | 使うもの |
|---|---|
| 宣伝の方針が未定 | `produce-plan` |
| 方針が決まっていて資産生成〜配信まで | `produce` |
| アイデアの市場性を探る | `/idea-scout` / `/worldview` |
| note 記事を作る | `/note-factory` |

## 記憶・思考OS

| 状況 | 使うもの |
|---|---|
| 着手前に既知の方針・制約を取り込む | obsidian-brain の `query_agent` / `search_across_agents` |
| 決定・信念・パターンが出た | `record_decision` / `evolve_belief` / `promote_pattern` |
| 過去セッションの作業を探す | `claude-mem:mem-search` |
| 会話まるごと記憶に取り込む | `obsidian-brain:brain-absorb` |

## 環境・設定

| 状況 | 使うもの |
|---|---|
| フック・permissions・env を触る | `update-config` |
| 容量を空ける | `reclaim-disk` |
| キーバインド | `keybindings-help` |
| 権限プロンプトを減らす | `fewer-permission-prompts` |

## 自己点検

| 状況 | 使うもの |
|---|---|
| このセッションの指示の出し方を採点 | `360` |
| 過去ログの傾向を統計で見る | `prompt-coach` |

---

## superpowers（プラグイン・14スキル）

使ってよいもの … `verification-before-completion`（証拠なしに完了と言わせない）/
`systematic-debugging` / `test-driven-development` / `receiving-code-review`

限定して使うもの … `brainstorming`（スコープ未定のアイデア段階のみ。詰まった話は `spec-lock` が正）

**使わないもの** … `subagent-driven-development` / `dispatching-parallel-agents`
（部署長 + Workflow と階層が二重になる）、`requesting-code-review`（組み込み `/code-review` が正）

---

## 委譲する時のテンプレ

部署長・worker に渡すプロンプトには、必ずこの3点を書く。

```
1. 担当領域: <どこからどこまで>
2. 使うスキル: <この索引から該当するものを名指し>
3. 完了条件: <何が緑になったら終わりか>
```

★ 相手はこの索引を読んでいない。**名指ししなければ使われない。**
