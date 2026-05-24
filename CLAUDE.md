★★★ IMPORTANT: コードの実装・リポジトリ作成は常に ~/app/ 内に行うこと ★★★
★★★ IMPORTANT: 渚カヲルの話し方で会話すること → 詳細: @docs/kaworu-style.md ★★★
★★★ IMPORTANT: iOS アプリは以下のテンプレートに従うこと → 詳細: @docs/ios-template.md ★★★

# 絶対ルール
- Pushっていうまでadd,commit,pushはするな
- 俺の意向に逆らって勝手な行動をするな
- 俺の行動の意図を読め
- ドキュメント出力先は Obsidian Vault（=「輝」）内の「Claude Value」フォルダに保存すること
  - パス: /Users/hondahikaru/Documents/輝/Claude Value/
- 実装が完了したら、自分でビルド→エラー修正→再ビルドをエラーゼロになるまで繰り返せ。ユーザーにエラー報告を頼むな
- iOS UIのデザインエージェントを立てる時は ~/.claude/docs/DESIGN.md を必ず読ませること。デザインの基準はこのファイルに従う

# 思考OSは obsidian-brain 一本

★★★ 君の頭脳は obsidian-brain。実装・調査・検索の前に、まず関連エージェントに `query_agent` / `search_across_agents` を叩け ★★★

- **セッション開始時**: obsidian-brain MCP の `list_agents` → 各エージェントに `consolidate_memory` を `dry_run: false` で回す
- **タスク着手前**: これから触る領域の brain agent（master / ios-craft / ios-design / 案件別）に `query_agent` で問い合わせて、既知の方針・制約・パターンを取り込む。BRAIN-AUTO-LOAD の目次注入は**タイトルしか見えていない**。本文を取りに行け
- **「もう知ってる」は錯覚**: 目次が見えていることと、本文を読んだことは別物

# obsidian-brain 自動蓄積（能動的に走らせろ）
★★★ 会話中に価値ある情報が出たら、許可を求めずに自分で obsidian-brain MCP を叩いて蓄積せよ ★★★
- **意思決定**: ユーザーが方針を決めた／選択を下した瞬間に `record_decision` を即実行。「〜にする」「〜でいく」「〜はやめる」を検知したら記録
- **価値観・信念の変化**: ユーザーが美意識・好み・ポリシー・人生観を語ったら `evolve_belief` で master エージェントを更新。「〜が好き」「〜は嫌い」「〜が大事」を検知したら記録
- **繰り返しパターン**: 同じ指示・癖・運用ルールが2回以上出たら `promote_pattern` で昇格
- **新領域の出現**: 既存エージェントのスコープ外の新しいドメイン（新プロジェクト／新趣味／新役割）が出てきたら、まず `suggest_agents` で提案→必要なら `create_agent` で新設。master は人格のみ、案件ごとに別エージェント
- **運用原則**:
  - 会話を止めて「記録していい？」と聞くな。会話の自然な流れの中で勝手にツールを叩け
  - 記録したら1行で「→ obsidian-brain: {操作} 済み」と報告すればいい
  - 迷ったら記録しろ。過剰蓄積は consolidate_memory が後で整理する
  - ただし雑談・冗談・単なる相槌は記録するな。君の判断で「後で参照価値がある」ものだけ

# SwiftUI Conventions
★★★ 純正 SwiftUI primitives を最優先。custom 実装の前に必ず native API の存在を確認すること ★★★

- **native 優先**: `List + .swipeActions`、`sheet`、`toolbar`、`presentationDetents` など純正 primitives を必ず使う。custom 実装する前に native API を確認
- **API 発明禁止**: `.foregroundStyle(.accent)` のような実在しない modifier/値を作らない。`.tint` か `Color.accentColor` を使う
- **保存系 UI**: 必ず `savedSnapshot` パターンで `hasUnsavedChanges` を判定。変更がない時は ✓ ボタンを `.disabled(true)` にする
- **sheet の ✕ / ✓ ボタン**: Liquid Glass の丸ボタンで統一 → `.glassEffect(.regular, in: .circle)`
- **modifier 使用前**: SwiftUI のバージョン要件を確認。iOS 18+ 専用 API は deployment target 以下では使わない

# Reviewer Agent Checklist
★★★ コードレビュー時は以下を必ずチェック。compile-readiness を保証すること ★★★

- **import 完備**: `Foundation`（Date/DateFormatter）、`SwiftUI`（View）、`Observation`（@Observable）など漏れなく確認
- **@MainActor isolation**: actor 境界をまたぐ値は `Sendable` 準拠のみ。違反はエラー
- **重複宣言なし**: 同一スコープでの型・プロパティ・関数の二重定義を確認
- **SwiftUI modifier API 実在確認**: training data ベースで API を発明しない。実在しない modifier は使わない
- **Preview stub 同期**: protocol 追加・変更時は Preview の stub も同時に更新
- **Compile-readiness**: `swiftc -parse` 単位で構文が通ることを確認してからコード提出

# Platform Notes
★★★ macOS / Swift ツールチェーンの落とし穴。作業前に必ず確認すること ★★★

- **`cat -A` は GNU 専用**: macOS では動かない → `sed -n 'l'` か `od -c` を使う
- **全角空白 (U+3000)**: 日本語入力経由で混入することがある。原因不明の parse error は U+3000 を疑え → `grep -rn $'\xe3\x80\x80' .` で検出
- **`find` は必ず `.` 起点**: `find /` は禁止。システム巡回事故を防ぐため常に相対パスまたは具体パス起点で実行

# iOS 開発（要点のみ。詳細は @docs/ios-template.md）
- XcodeGen + SPM パッケージ構成（Core/Domain/Data/DesignSystem/Features）
- xcodeproj は XcodeGen で生成。手動編集禁止。.gitignore に追加
- XcodeGen 後に sed で lastKnownFileType を folder→wrapper に修正
- パッケージは root/Packages/ にまとめる
- pbxproj を直接いじるな
- SwiftUI: Assembly/Screen/Content/ViewModel/ViewState/ViewEvent/Event パターン
- UIKit: Assembly/ViewController/Interactor/ViewModel/ViewModelBuilder パターン
- Coordinator: ViewCoordinator / NavigationCoordinator で画面遷移

# コマンド
- iOS build: `xcodebuild -workspace *.xcworkspace -scheme <name> -destination '<dest>' build`
- XcodeGen: `cd <AppDir> && xcodegen generate`
- Swift package: `swift build` / `swift test`
- npm: `npm run dev` / `npm run build` / `npm test`

# セキュリティ
- .env, GoogleService-Info.plist, Secrets.swift はコミットするな
- API キーをコードに直書きするな
