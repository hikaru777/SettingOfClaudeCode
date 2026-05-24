# /idea-scout — ビジネスアイデア・スカウト・エージェント

WebSearchで多角的にリサーチし、実際の「痛み」を起点にビジネスアイデアを発掘する自律エージェント。

## トリガー

ユーザーが以下のいずれかを求めるとき：
- 新しいビジネス/SaaS/アプリのアイデアを探したい
- 特定ドメインでビジネス機会を調査したい
- 「何か作りたいけどアイデアがない」
- 競合調査や市場リサーチ
- 既存アイデアの代替案探し

## 引数

- 引数なし: 幅広く探索
- ドメイン指定（例: `EC`, `不動産`, `クリエイター`, `飲食`）: 集中リサーチ
- `--ai-proof`: AI耐性チェック有効化
- `--refresh-profile`: GitHubからプロフィール再分析

プロジェクトディレクトリ: `~/App/IdeaScout/`
プロダクト保存先: `~/Documents/輝/Products/`

## 手順

### 1. コンテキストを収集する

以下を並列で読み込む：
- `~/App/IdeaScout/config/profile.md` — ビルダーの技術プロフィール
- `~/App/IdeaScout/config/filters.md` — 品質フィルター定義
- `~/Documents/輝/Products/*/README.md` — 既存プロダクト一覧（各READMEの1行目から名前と概要を抽出し、除外リストを自動構築）

`--refresh-profile` 指定時は `gh repo list --json name,primaryLanguage,description --limit 50` でGitHubリポを取得し、profile.md を更新。

### 2. サブエージェントを起動する

Agent tool を使ってリサーチエージェントを起動する：

- `subagent_type`: `general-purpose`
- `model`: `opus`
- `prompt`: Step 1 で収集した全コンテキスト（profile, filters, 除外リスト）と、以下の実行指示を渡す：

---

**実行指示（サブエージェントへのプロンプト）:**

あなたはビジネスアイデア・スカウト・エージェントです。WebSearchを駆使して多角的にリサーチし、実際の「痛み」を起点にビジネスアイデアを発掘してください。

**Phase 1: 多角リサーチ（WebSearchを並列実行）**

以下の探索ベクトルでWebSearchを実行。各ベクトルで2〜3クエリを投げること。{ドメイン指定があればそのドメインに絞る}

- **V1 痛みの発見**: "[domain] frustrated with OR wish there was site:reddit.com 2025 2026" / "[domain] 面倒 困っている ツールがない"
- **V2 既存ツールの不満**: "[domain] SaaS too expensive OR too complex" / "[domain] ツール 使いにくい 代替"
- **V3 成功パターン**: "indie hacker $10k MRR 2026 [domain]" / "micro SaaS profitable [domain] solo"
- **V4 日本DXギャップ**: "日本 [domain] DX 遅れ 手作業" / "[domain] Japan digital transformation gap"
- **V5 テクノロジー**: "MCP server [domain] 2026" / "[domain] what's newly possible with AI"
- **V6 グローバル**: "[domain] SaaS Japan global expansion"
- **V7 AI耐性**（--ai-proof有効時のみ）: "data moat micro SaaS what AI cannot replace" / "SaaS defensibility against AI agents"

**Phase 2: 統合分析**

リサーチ結果から交差点を探す：痛み × ビルダーのスキル × 到達可能な顧客 × 未充足の市場。除外リストとの重複は排除。

**Phase 3: アイデア生成（5〜8個、質が低いなら3個でOK）**

各アイデアに以下を含める：
- **一言**: 30字以内
- **痛みの証拠**: 実際のURL（なければ「証拠未発見」）
- **解決策**: 1ヶ月以内にMVP作れる範囲
- **競合と不満**: テーブル（サービス名/URL/価格/不満）
- **堀（Moat）**: データ蓄積/ネットワーク効果/API統合/ブランド/コミュニティ/なし
- **最初の10人**: 具体的チャネル+アクション
- **PLG設計**: 自然に広まる仕組み
- **収益モデル**: 価格帯と根拠
- **技術スタック**: profile.mdとの親和性
- **グローバル展開**: 可能/要ローカライズ/日本限定
- **リスク**: 最大の弱点
- **AI耐性**（--ai-proof有効時）: なぜAIに1プロンプトで代替されないか

**Phase 4: 品質フィルター**

基本チェック：MVP1ヶ月以内？/ 顧客が必要性認識済み？/ ネット経由で10人獲得？/ 月額課金自然？/ 技術差別化あり？/ リスク致命的でない？
--ai-proof時追加：AI代替不可？/ 価値源泉がデータ/接続/継続性/信頼？
→ 1つでもNOなら削除。△は出力しない。

**Phase 5: 最終出力**

1. リサーチ重要ファクトのサマリー
2. 各アイデアの構造化提案
3. 総合評価テーブル（名前/◎or⭕️/堀/グローバル可否）
4. Sources

リサーチ結果を `~/App/IdeaScout/data/research/YYYY-MM-DD_vectors.json` に保存すること。嘘のデータ禁止。質が低いなら3個で良い。各Phase完了時に進捗を報告。

---

### 3. 結果を伝える

エージェントの回答をユーザーにそのまま伝える。

### 4. プロダクトフォルダ化（ユーザー承認後）

ユーザーが「プロダクト化して」「フォルダ作って」等と言った場合、指定アイデアごとに `~/Documents/輝/Products/{slug}/` を作成し、README.md + mvp-scope.md を生成する。

**README.md テンプレート:**
```
# {名前} — {一言}
> {痛みの要約}
## コンセプト / ## なぜ今か / ## 主要機能 / ## 技術スタック / ## ターゲット
## 収益モデル（テーブル） / ## 競合（テーブル） / ## リスク（テーブル）
```

**mvp-scope.md テンプレート:**
```
# {名前} MVP Scope
## ゴール / ## 最小機能セット / ## 技術設計 / ## マイルストーン(Week 1-4) / ## 成功指標
```

### 5. 会話の継続

ユーザーの追加指示に応じて同じエージェントを resume で再開：
- 「もっと深掘り」→ 特定アイデアの追加リサーチ
- 「別のドメインで」→ 新ドメインで再探索
- 「競合もっと調べて」→ 競合深掘り
- 「全部微妙」→ 探索ベクトルを変えて再リサーチ
