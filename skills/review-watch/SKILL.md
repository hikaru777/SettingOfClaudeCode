---
name: review-watch
description: ユーザーが Xcode 等で自分の手で書いている Swift コードの差分をセッション中ずっと監視し、アーキテクチャ/SwiftUI 流儀に反する書き方を見つけたら 1 件ずつ指摘する。ユーザーはいつでも質問してヒントを得られる。「コードを監視して」「書いてる間レビューし続けて」「差分を見張って指摘して」等で起動。1 回の呼び出し = 1 ティック（差分を 1 回点検）。継続監視は /loop に乗せて回す。
---

# review-watch — 差分監視レビュー

ユーザーが**自分の手で（Xcode 等で外部から）**書いている Swift を見張り、悪い書き方を 1 件ずつ指摘する。本人は学習中なので**答えのコードは書かない**——指摘＋直す方向＋理由だけ渡す（[[feedback_learning_mode_no_code]]）。トーンは簡潔・平易・断定、キザ禁止（[[feedback_concise_plain_no_kiza]]）。

**1 回の呼び出し = 1 ティック**（差分を 1 回点検して新しい指摘を出す）。継続は外側の `/loop` が回す。本文の手順は 1 ティック分。

## 動作モデル（これ以外で実装しない）
- 監視は**この対話セッションの中**で回す。`PostToolUse` フックは Claude 自身の編集しか拾えず、ユーザーの外部編集を拾えないので使わない。
- **`claude -p` やバックグラウンド常駐プロセスを絶対に起動しない**。従量課金（programmatic）になり「LLM はサブスク経由・API課金禁止」に反する。差分検出は同梱スクリプトの Bash スナップショット比較のみ。
- **git を一切変更しない**（init/add/commit しない）。スナップショットは作業ディレクトリへのコピーで取る。

## 起動のさせ方（ユーザーに案内する）
- 継続監視: **`/loop /review-watch`**（自己ペースで巡回。ペーシングは ScheduleWakeup 一本＝下記）。
- 間隔固定: `/loop 5m /review-watch`（この場合 ScheduleWakeup は呼ばない＝二重発火防止）。
- 今すぐ 1 回だけ: `/review-watch`。
- 対象変更: `/review-watch <path>`（省略時 `~/app/Sudoku`）。
- 基準を取り直す: `/review-watch <path> reset`。

## コストの正直な話（ユーザーに最初に伝える）
- 「変更なしティックで黙る」のは**出力と推論**を抑えるだけ。**各ティックは入力(この長いシステム前提)を毎回読み直す**ので、無音でも入力コストはかかる。
- これはサブスク枠（利用ウィンドウ）を消費する。**ガン詰めで書いている時だけ回し、休憩中は『監視やめて』で止める**のが正しい使い方。
- 既定間隔は ~150s（キャッシュが温かい範囲）。長時間ダラ見なら `/loop 10m /review-watch` 等に伸ばす提案をする。

## 状態の置き場（セッション跨ぎでも壊れない）
- `TARGET` = 引数のパス。無ければ `~/app/Sudoku`。
- `BASE` は**スクリプトに聞く**（自分でハッシュ計算しない＝表記揺れで孤児化しない）:
  `BASE=$(bash ~/.claude/skills/review-watch/watch-diff.sh "$TARGET" --where)`
- `BASE/state` … `running` / `stopped`（スクリプトは触らない。スキルが管理）
- `BASE/ledger.md` … 既出指摘の台帳（`file | ルール | 要旨` を1行ずつ）。重複指摘を防ぐ。reset/staleness でも消えない。

## 1 ティックの手順
1. **TARGET 決定** → `BASE=$(... --where)` を取得。
2. **停止チェック**: `BASE/state` が `stopped` なら**何もせず終了**（このターンでユーザーが明示的に再開を頼んだ場合を除く）。
3. **差分取得**: `bash ~/.claude/skills/review-watch/watch-diff.sh "$TARGET"` を実行し、出力マーカーで分岐:
   - `__TARGET_NOT_FOUND__` → パスが違う。ユーザーに知らせて止める（無音で流すな）。
   - `__BASELINE_ESTABLISHED__` → 初回/再取得。`BASE/state` に `running`、`BASE/ledger.md` を無ければ空作成。1行で「監視開始。`<TARGET>` の .swift N 個を見張る。詰まったら『ヒント 〇〇』、止めるなら『監視やめて』」＋上の**コストの一言**を告げて終了。
   - `__TICK_OK__` のみ（diff 無し）→ **変更なし。何も言わず終了**（推論も使わない）。ただし無音が続くと「監視が死んだ」と区別できないので、**約10ティックに1回だけ**「監視継続中（変更なし）」と1行 heartbeat を出してよい。
   - diff があり末尾に `__TICK_OK__` → 次へ。
   - **どのマーカーも無い** → スクリプト異常。無音で流さず「監視スクリプトが応答しない」と報告。
4. **点検**: 下の【レビュー基準】で diff を見る。指摘は `BASE/ledger.md` と突き合わせ、既出（同じ file × 同じルール）はスキップ。
5. **指摘**: 新規の指摘は**この diff の分を全部出す**（書式は下記）。throttle して次ティックに繰り越すな——スクリプトは毎ティックでスナップショットをローテートするので、出し損ねた指摘は次に拾えず消える。出した指摘は `BASE/ledger.md` に追記。
6. 終了。`/loop` 自己ペース中（間隔指定なし）なら、最後に `ScheduleWakeup`（delaySeconds ≈ 150、prompt = `/review-watch <TARGET>`）で次を1つだけ予約。`/loop` に固定間隔があるなら予約しない（二重発火防止）。`state` が `stopped` なら予約しない。

## 判定の精度ルール（誤検知を出さないため・重要）
diff の追加行**だけ**で断定できるルールと、**変更ファイル全体を読まないと判定できない**ルールがある。混同するな。

- **行ローカルで判定可**（diff だけで指摘してよい）: 実在しない modifier の発明 / `TextEditor` 使用 / 詩的な可視ラベル / `ToolbarItem` 内の装飾(背景・glassEffect・padding・Spacer) / `@Bindable` で VM 所有 / `MainActor.run` 冗長 など、その行だけで完結するもの。
- **ファイル全体が要る**（追加行だけで断定するな）: public/internal 境界 / UI 状態網羅(empty/loading/error) / `savedSnapshot` dirty 判定 / 同一 placement の ToolbarItem 重複 / Features→Data 依存 / Codable 後方互換 / import 完備 / 重複宣言。
  → これらに**関係する変更**を見たら、**その変更ファイルを Read してから**判定する。**「○○が無い」を diff だけを根拠に指摘するな**（先頭の import や別の場所は diff に映らない）。読んでも確信が持てなければ「要確認」と明示し、断定しない。

## 割り込み（インタラクティブ・ヒント）
巡回の合間にユーザーが質問してきたら、それへの回答が最優先。
- 「ヒント 〇〇」「ここどう書く？」等 → **答えのコードは書かない**。考える方向・選択肢・トレードオフ・該当する純正 API や原則を渡す。説明用の**ごく短いスニペット**は可だが、本人のファイルを書き換えたり完成形を渡したりしない。
- 回答後も監視は継続。

## 停止 / 再開
- 「監視やめて」「stop」「もういい」等 → `BASE/state` に `stopped` を書き、1行「監視止めた」。次ティック冒頭で自然に止まる。`ScheduleWakeup` は呼ばない。
- 「再開」→ `BASE/state` に `running` を書いて 1 ティック実行（停止中<15分の編集は再開時にまとめて diff に出る＝想定どおり）。

## 指摘の書式（1 件 = 短く）
```
⚠️ <file>:<line> — <何が問題か（1行）>
  なぜ: <違反しているルール/原則（1行）>
  方向: <どう直すか。コードでなく方針。純正 API 名・移すべき層など>
```
平易・簡潔・断定。褒めない。問題が無いティックは黙る。確信が低い時は「要確認」と明示。

## レビュー基準（本田輝の確立ルール。diff をこれに照らす）

### マルチモジュール / アーキテクチャ
- **依存は下向き一方向**。`Core`/`Domain`/`DesignSystem` は依存ゼロ（最下層）。`Data`→Domain(+Core)。`Features`→Core/Domain/DesignSystem。
- **Features は Data に直接依存禁止**。通信は Domain/Core 側に Repository プロトコル → AppContext に Provider → Data で実装 → LiveAppContext で具象注入 → Features は `context.xxx` 経由。（Feature→Data 直依存は SwiftUI Preview の JIT クラッシュも誘発）
- **public/internal 境界**: 外から使うものだけ `public`。`Assembly` と `Event` だけ公開、`Screen`/`Content`/`ViewModel`/`ViewState`/`ViewEvent` は internal。【要ファイル全体】
- `public` な `Assembly.screen` が internal な `Context` を引数に晒すとアクセス制御エラー → public protocol を直に constraint に。
- **Features 同士の相互 import 禁止** → 共有したい型は Domain に降ろす。
- 命名規約: `{Feature}Assembly/Screen/Content/ViewModel/ViewState/ViewEvent/Event`、`{Feature}NavigationCoordinator`、`{Scope}Route`、`{Feature}RootView`。
- NavigationStack / sheet / fullScreenCover は Coordinator 側で管理。Assembly の戻り値は `some View`。

### SwiftUI 実装
- **native primitive 最優先**。`List + .swipeActions` / `.sheet` / `.toolbar` / `NavigationStack` / `presentationDetents` / `PhotosPicker`。自前実装の前に純正確認。**自前 picker 禁止**。
- **実在しない modifier/値を発明しない**（例: `.foregroundStyle(.accent)` は無い → `.tint` か `Color.accentColor`）。
- **UI 状態網羅**: empty / loading / error / unchanged / partial / all。happy path だけで出すな。【要ファイル全体】
- **保存系 UI**: `savedSnapshot` で `hasUnsavedChanges`、変更なしなら確定(✓)を `.disabled(true)`。**✓ は確定専用、dismiss に使うな**（キーボード閉じは `keyboard.chevron.compact.down`）。【要ファイル全体】
- **selection UI**: none / partial / all の3状態。対象ゼロ時は action disabled。
- **destructive**: disabled / confirmation / undo のいずれか。
- **toolbar**: 画面(Content)内部に付与。`ToolbarItem` の中身は HStack の Text/Image **だけ**（背景色/glassEffect/padding/frame/Spacer 禁止）。同一 placement に複数なら `ToolbarItemGroup` に統合（後勝ちで先頭が消える）。【複数判定は要ファイル全体】
- **ViewModel 所有**: `@Observable` な VM は `@State`/`@StateObject`。`@Bindable` は bindings 専用で所有しない。
- **iOS 26 では `TextEditor` を使うな**（日本語 IME を壊す）→ `TextField(text:, axis: .vertical)` + `lineLimit(1...)`。
- **可視ラベルに詩的/中二語を使うな**（「生命感」等）→ 機能を表す素直な名詞。内部名は可、画面文字列だけ平易に。

### Swift コンパイル / 並行性
- import 完備（`Foundation`=Date/URL/UUID/Calendar、`SwiftUI`=View、`Observation`=@Observable）。【要ファイル全体】
- 同一スコープの型/プロパティ/メソッドの重複宣言なし。【要ファイル全体】
- `@MainActor` isolation: actor 境界をまたぐ値は `Sendable` のみ。`@Sendable` closure 内の captured var mutation 禁止（参照型ボックスへ）。`#Predicate` は参照型を直接 capture しない（local 束縛で逃がす）。`@MainActor` クラス内の `MainActor.run` は冗長。
- Codable 後方互換: 新 field は `decodeIfPresent` + デフォルト。【要ファイル全体】

### UI 第一フェーズの規律（UI だけ作る段階なら）
- 通信関数なし / Data 層空 / ViewEvent は UI 更新用のみ / ViewModel は viewState を直書き換え。

## 既定値まとめ
- 対象: 引数 > `~/app/Sudoku`
- 巡回間隔: 約150秒（キャッシュが温かい範囲。ダラ見なら伸ばす）
- 1 ティックの指摘: その diff の新規分を**全部**（throttle しない）
- トーン: 簡潔・平易・断定・キザ禁止・学習モード（答えコードを書かない）
