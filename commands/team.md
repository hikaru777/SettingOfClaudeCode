# /team — Fan-out / Fan-in エージェントチームを起動する

## 目的

複数エージェントがファイル衝突を起こさず、可能な限り**同時に**実装を進め、最後に単独の integrator が統合して compile-ready な状態に持っていく。

このスキルは「順番に実装するチーム」ではなく、「**契約を先に固定し、全 worker が同時に atomic diff を作り、最後に統合するチーム**」である。

## 引数

- 任意のテキスト: 実行したいタスクの説明（省略時は聞く）

---

## 基本思想

### 1. 直列開発を禁止する

悪い進行:
```md
Domain 完了
↓
Persistence 開始
↓
UI 開始
↓
Preview 修正
↓
統合
```

これは複数エージェントを使っていても、実質的には1〜3人で直列に作業しているだけである。

正しい進行:
```md
API Contract / Skeleton 確定
↓
Domain / Persistence / UI / Mock / Preview / Wiring / Tests が同時開始
↓
各 worker が atomic diff を完了
↓
reviewer が領域別に検証
↓
integrator が1人で統合
```

### 2. blockedBy ではなく canStart / mergeAfter で考える

`blockedBy` は原則として使わない。代わりに以下を使う:

- **canStart**: `true | false` — 今すぐ作業を開始してよいか
- **mergeAfter**: `[task-id]` — 作業は始めてよいが、統合順序として後に回すべき task
- **dependsOnContract**: `[type / protocol / method / file]` — 実装完了ではなく、**契約として存在していれば**依存可能な型・関数・protocol

例:
```md
Task ID: UI-03
目的: TactEditorView に operation list を表示する
canStart: true
mergeAfter:
  - DOMAIN-01
  - MOCK-01
dependsOnContract:
  - TactOperation
  - TactRepositoryProtocol.fetchOperations
方針:
- Domain の実装完了は待たない
- API Contract を正として UI を実装する
- 実 repository が未完成なら mock repository を使う
```

### 3. Start Blocker / Merge Blocker / Runtime Blocker を分ける

**Start Blocker** — 作業開始を止める本当のブロッカー。以下のみ:
- API Contract が未確定
- 対象ファイルが存在しない
- public type / protocol / method signature が未確定
- spec 判断が必要
- ファイル所有者が未確定
- 同じファイルが複数 worker に割り当てられている

**Merge Blocker** — 作業は始めてよいが、統合順序を制御するもの:
- Persistence は Domain 実装完了前に作ってよい
- UI は Repository 実装完了前に mock に対して作ってよい
- Preview は本番 repository 完了前に mock data で作ってよい

**Runtime Blocker** — compile は通るが、実動作確認が後になるもの:
- 実データ接続は未確認
- Preview / mock では動くが本番 repository では未検証
- xcodebuild での最終確認が必要

Runtime Blocker は WARN として最終 report に残す。

---

## モデル規律（例外なし）

★★★ **このスキルで立てるエージェントは planner / worker / reviewer / integrator を含めて全員 Sonnet 5** ★★★

- spawn 時に **必ず `model: "sonnet"` を明示**する。親からの継承任せにしない
- 部署長がさらに Workflow を回す場合も、全 `agent()` に `opts.model: 'sonnet'` を貼る
- 「reviewer は判断が要るから opus」もやらない。判断基準は planner-architect が固定した契約と受け入れ条件であって、モデルの地力で埋めるものではない
- Opus はディレクター（メインのセッション）だけ

## チーム構成

### 推奨: 10エージェント構成（中〜大規模変更）

1. **planner-architect** — 実装しない。契約・分割・所有権・タスク表を作る
2. **domain-worker** — Domain model / protocol / pure function
3. **operation-worker** — operation / reducer / helper
4. **persistence-schema-worker** — SwiftData @Model / schema
5. **persistence-mapper-worker** — Domain ↔ Persistence mapper
6. **repository-worker** — repository implementation
7. **app-ui-worker** — View / ViewModel / Feature UI
8. **mock-preview-worker** — InMemory / Mock / Preview stub
9. **reviewer** — compile-readiness / spec / ownership 違反検出
10. **integrator** — 最後に1人で統合する

### 安定重視: 6 worker + 2 reviewer + planner + integrator（衝突リスク高）

1. planner-architect
2. domain-worker
3. persistence-worker
4. app-ui-worker
5. mock-preview-worker
6. wiring-worker
7. reviewer-domain-persistence
8. reviewer-app-ui
9. integration-reviewer
10. integrator

### 既存「3組9エージェント」構成（領域分割で並行性確保）

3 つの領域別サブチームに分けた既存パターンも引き続き利用可能。**ただし必ず planner-architect と integrator を追加する**（合計 11 名）。

組の領域分割（iOS マルチモジュールの例）:
- **組1「Domain」**: 純関数 / model / op / Codable 後方互換 / 算出ヘルパ
- **組2「Persistence」**: SwiftData @Model / Schema / Mapper / Repository 実装
- **組3「App + UI」**: Coordinator / Route / AppRootView / Features 画面 / Sheet 配線

各組は3名（impl-A / impl-B / reviewer）。
**planner-architect + integrator は全体共通で 1 名ずつ追加**する。

### 小規模変更（数ファイル程度）

1. planner
2. worker-1
3. worker-2
4. reviewer
5. integrator

ただし、小規模でも以下は必須:
- File Ownership
- canStart
- mergeAfter
- 編集禁止ファイル
- 横断ファイル所有者

### 調査のみ（「調べて」「分析して」「比較して」）

- researcher-1 / researcher-2: 並行調査
- summarizer: 結果まとめ

### 構成判断の目安

以下のいずれかを満たせば 10エージェント構成、満たさなければ小規模構成:
- 変更ファイルが **6 ファイル以上**
- **Domain / Persistence / UI のうち 2 領域以上に跨る**
- protocol / model / persistence / UI 配線のように **依存順がある**

迷ったら小規模構成（過剰な並行は調整コストが利得を上回る）。

---

## 実行手順

### Phase 0: Task Compile

実装前に planner-architect は必ず Task Compile を行う。

**目的**: ユーザーの雑な依頼を、複数 worker が即実行できる atomic diff に分解する。

**atomic diff の条件**:
- 1 task = 1目的
- 原則 1〜2ファイルだけ編集
- 1 worker が担当
- 他 worker と同じファイルを触らない
- 設計判断を含まない
- 担当外ファイルを触らずに完了できる
- 完了条件が明確
- canStart / mergeAfter / dependsOnContract が明記されている

atomic diff に分解できない場合、**いきなり実装してはいけない**。先に API Contract / Skeleton / File Ownership を確定する。

### Phase 0.5: Session Start Sanity Check

実装系タスクの場合、planner-architect は worker spawn 前に session 環境の sanity check を行う。

**必須確認**:
- `xcodebuild -list` で scheme 名を確認
- 既知の scheme 名がある場合は CLAUDE.md / プロジェクト固有 CLAUDE.md の Build Commands と照合
- `Tact` のような推測 scheme 名を使わない
- Swift package 構成の場合は package path を確認
- project.yml / XcodeGen 構成の場合は generate 必要条件を確認
- baseline build を実行するかどうかを team-lead が判断する

**注意**:
- worker / reviewer は xcodebuild を走らせない
- `swift build` など軽量検証は integrator が担当してよい
- xcodebuild が必要な場合は team-lead またはユーザー判断で最終確認として実行する
- sanity check の結果は初回ブロードキャスト（Phase 3）で全 worker に共有する

### Phase 1: Work Contract 作成

planner-architect は TeamCreate 後、実装開始前に **Work Contract** を作成する。

Work Contract には必ず以下を含める:

```md
## Work Contract

### 全体目的
<今回の変更で実現すること>

### 非目的
<今回はやらないこと>

### 変更領域
- Domain:
- Persistence:
- App/UI:
- Mock/Preview:
- Wiring:
- Tests:

### API Contract
- 追加/変更される型:
- 追加/変更される protocol:
- 追加/変更される method signature:
- public / internal 境界:
- Codable 後方互換方針:
- Swift concurrency 境界:

### Skeleton
下流 worker が依存してよい最低限の型・protocol・method を定義する。
中身は仮実装でもよい。ただし signature は固定する。

### File Ownership
| File/Directory | Owner | Editable | Notes |
|---|---|---|---|

### Edit Denylist
各 worker が絶対に触ってはいけないファイル。

### Cross-cutting Files
横断ファイルと単独所有者。例:
- AppRootView.swift: wiring-worker
- AppCoordinator.swift: wiring-worker
- RepositoryProtocol.swift: domain-worker
- Tact.swift: domain-worker

### Task Graph
各 task について:
- taskId
- owner
- purpose
- editableFiles
- readonlyFiles
- forbiddenFiles
- canStart
- mergeAfter
- dependsOnContract
- outputMode
- completionCriteria
- risk

### Integration Order
integrator が最後に取り込む順序。

### Final Verification
- swift build
- xcodegen generate
- mock / preview conformer
- strict concurrency
- Codable backward compatibility
```

**Work Contract が未作成の状態で worker を動かしてはいけない**。

### Phase 2: API Contract / Skeleton 確定

実装本体より先に **API Contract / Skeleton** を確定する。

**Skeleton の目的**: 下流 worker が他 task の完了を待たずに実装できるようにすること。

Skeleton には以下を含める:
- 型名
- protocol 名
- method signature
- enum case
- public initializer
- error type
- Sendable / MainActor 方針
- Codable 後方互換方針
- mock / preview が準拠すべき interface

**重要**: Skeleton の中身は仮でよい。ただし signature は原則固定。

#### Skeleton Owner

API Contract / Skeleton の**最終所有者は planner-architect** とする。

- domain-worker は Skeleton の**実装案**を作ってよい
- ただし以下の**最終決定は planner-architect が行う**:
  - public type / protocol / method signature
  - actor boundary（@MainActor / nonisolated / Sendable 境界）
  - Codable 方針（後方互換戦略 / decodeIfPresent デフォルト）
  - public / internal 境界
- worker は planner-architect が確定した Skeleton を**正**として作業する
- worker が signature 変更を必要と判断した場合、**直接変更せず Contract Change Request を送る**（後述 Phase 4.5 参照）

### Phase 3: 全 worker 同時開始（初回ブロードキャスト必須テンプレ）

API Contract / Skeleton / File Ownership が確定したら、team-lead は全 worker に**初回ブロードキャスト**を発信する。

```
- 全体目的: <1〜2行>
- チーム構成: planner-architect / worker-X (×N) / reviewer / integrator
- API Contract (要約): <型 / protocol / signature>
- Skeleton 場所: <ファイルパス>
- 各 worker の editable / readonly / forbidden ファイル
- 横断ファイルの単独所有者
- canStart 状態と mergeAfter
- 連絡ルール: Patch Request / spec 迷いは team-lead に / FAIL は reviewer から team-lead
- 完了条件: 後述「完了条件」節を参照
- 待機禁止ルール: 上流実装の完了は待たない。mock / stub / TODO placeholder で進む
```

worker への共通指示:
- 他 task の完了を**待たない**
- API Contract を**正**として、自分の担当 atomic diff を完了する
- 上流実装が未完了の場合は **mock / stub / TODO placeholder** を使う
- 担当外ファイルは絶対に編集しない
- 判断が必要な場合だけ team-lead に報告する
- 待機は禁止

### Phase 4: Patch Request

worker が担当外ファイルの変更を必要とした場合、**直接編集してはいけない**。必ず Patch Request を送る。

Patch Request 形式:
```md
## Patch Request

From: <worker name>
To: <owner worker or team-lead>

Reason: <なぜ担当外ファイル変更が必要か>

Target File: <対象ファイル>

Requested Change:
<追加したい import / method / route / wiring / mock 対応など>

Usage Example:
<呼び出し側の使用例>

Blocking:
<この変更がないと何が止まるか>

Urgency: low / medium / high
```

対象ファイルの owner だけが実際に編集できる。

### Phase 4.5: Contract Change Request

Patch Request は**担当外ファイル変更**用。**API Contract / Skeleton 自体の変更**は別物として扱う。

worker が API Contract / Skeleton の変更を必要とした場合、**直接変更してはいけない**。必ず team-lead に **Contract Change Request** を送る。

Contract Change Request 形式:
```md
## Contract Change Request

From: <worker name>

Affected Contract:
<type / protocol / method / enum / actor boundary>

Reason:
<なぜ契約変更が必要か>

Requested Change:
<変更したい signature / field / case / requirement>

Affected Tasks:
<影響しそうな task>

Compatibility:
- downstream 影響:
- Codable 影響:
- mock / preview 影響:
- persistence 影響:

Urgency: low / medium / high
```

**処理フロー**:
1. team-lead は Contract Change Request を受領
2. planner-architect と相談（Skeleton Owner なので最終判断者）
3. **承認 / 却下 / 代替案提示** の 3 択
4. **承認された場合のみ** API Contract を更新し、影響 worker に **broadcast**
5. 影響 worker は新 contract に追従

**重要**:
- Patch Request と Contract Change Request を混同しない
- Patch Request = ファイル変更依頼（横断ファイル wiring 等）
- Contract Change Request = 契約変更依頼（全 worker に影響）
- 並行実装中に worker が独断で protocol を変更すると **fan-out が破綻する**

### Phase 5: Reviewer 検証

reviewer は worker の成果を以下の観点で検証する。

**必須チェック**:
- 担当外ファイルを編集していないか
- File Ownership 違反がないか
- import が足りているか
- access control が正しいか
- public API と利用側が一致しているか
- protocol conformer が全更新されているか
- mock / InMemory / Preview stub が同期しているか
- **Swift 6 Strict Concurrency**（@MainActor 境界・Sendable 準拠・@Sendable closure 内 captured var mutation・#Predicate の local 束縛で参照型キャプチャ回避）
- **Codable 後方互換**（新 field は `decodeIfPresent + デフォルト`、旧 snapshot の JSONDecoder throw 不在）
- 既存シンボル参照が退行していないか（grep 検証）
- spec から外れていないか

**判定区分**:
- **PASS**: compile-readiness 上問題なし、統合候補
- **FAIL**: 明確な compile error / spec 違反 / ownership 違反 / 既存退行。修正必須
- **BLOCKED**: 検証に必要な contract / file / task が不足。team-lead 判断が必要（自分で「informational」にして逃げない）
- **WARN**: 動く可能性は高いが、最終統合や runtime 確認で見るべきリスクあり。PASS 扱いだが最終 report に明記

**FAIL の報告形式**:
```md
## FAIL
Task: <task id>
File: <file path>
Issue: <何が問題か>
Reason: <なぜ compile/spec/ownership 的にNGか>
Required Fix: <どう直すべきか>
Owner: <修正すべき worker>
```

reviewer は **general-purpose 型**で spawn、起動時に ACK を team-lead に返す（**沈黙運用禁止**）。
**独断 informational 化・残課題化禁止**。spec 違反は明示的に表面化し team-lead 判断を仰ぐ。

#### Reviewer Mechanical Gate

reviewer は ACK / PASS / LGTM を返す前に、**必ず以下を明示的に確認する**。目視レビュー禁止、機械的 gate にする。

**Swift compile basics**:
- Date / URL / UUID / Calendar / Locale / TimeZone など Foundation 型を使う file に `import Foundation` があるか
- duplicate variable / duplicate property / duplicate method declaration がないか
- referenced symbol / modifier / initializer が実在するか
- non-existent SwiftUI API（`.foregroundStyle(.accent)` 等）を使っていないか
- access control が cross-module 利用に足りているか

**Swift concurrency**:
- @MainActor isolation violation がないか
- Sendable が必要な型に付いているか
- @Sendable closure 内 captured var mutation がないか
- #Predicate で参照型を直接 capture していないか

**SwiftUI UX basics**:
- confirm / save / apply 系 button は unchanged state で disabled になっているか
- destructive action は disabled / confirmation / undo のいずれかが検討されているか
- selection UI は none / partial / all selected の状態を持つか
- empty / loading / error state が必要な view で抜けていないか
- native SwiftUI API で足りる要件に custom 実装を使っていないか

**Gate ルール**: 上記を確認せずに PASS してはいけない。確認できない場合は PASS ではなく **WARN または BLOCKED** にする。reviewer が「目視で大丈夫そう」で通すと、過去の friction（reviewer の脇が甘い問題）が再発する。

### Phase 6: Integrator 統合

integrator は**最後に1人だけ**が行う。複数人で統合作業をしてはいけない。

**integrator の責務**:
1. 各 worker の成果を確認
2. mergeAfter に従って統合順序を決める
3. import / access control / public API のズレを修正
4. Patch Request を反映する
5. 横断ファイルの wiring をまとめる
6. mock / preview / InMemory の conformer 漏れを修正
7. xcodegen generate が必要なら実行
8. swift build が可能なら実行
9. 最終 report を作成

**integrator の禁止事項**:
- 大きな設計変更
- spec の勝手な変更
- 担当 worker の実装意図の大幅変更
- 新機能追加
- 横断的リファクタリング
- WARN の握りつぶし

integrator が設計変更を必要と判断した場合は、team-lead に報告し、**再 Task Compile を要求する**。

---

## Task 定義フォーマット

全 task は必ず以下の形式にする。

```md
## Task: <task-id>

### Owner
<worker name>

### Purpose
<この task の目的>

### Editable Files
- <file path>

### Readonly Files
- <file path>

### Forbidden Files
- <file path>

### canStart
true / false

### mergeAfter
- <task-id>

### dependsOnContract
- <type / protocol / method / file>

### outputMode
direct-edit / patch-request / report-only / isolated-patch

### Implementation Rules
- 他 task の完了を待たない
- API Contract を正とする
- 担当外ファイルは触らない
- 上流未完成なら mock / stub / TODO placeholder を使う
- spec 判断を勝手にしない

### Completion Criteria
- <完了条件>

### Report Format
完了時は以下を報告:
- touched files
- added/changed symbols
- assumptions
- patch requests
- risks
```

---

## Worker Prompt Template

各 worker には以下の形式で指示する。

```
あなたは <worker name> です。
あなたの担当は Task <task-id> の atomic diff だけです。

目的:
<task purpose>

編集可能:
<editable files>

読み取り専用:
<readonly files>

編集禁止:
<forbidden files>

依存してよい契約:
<dependsOnContract>

canStart:
<true/false>

mergeAfter:
<mergeAfter>

outputMode:
<direct-edit / patch-request / report-only / isolated-patch>

重要ルール:
- 他 task の完了を待たない
- API Contract を正として実装する（planner-architect が確定した Skeleton が正）
- 担当外ファイルを絶対に編集しない
- 横断ファイルを直接編集しない
- 必要な担当外変更は Patch Request にする
- API Contract / Skeleton の変更が必要なら Contract Change Request を送る（直接変更禁止）
- 設計判断を勝手にしない
- ついでのリファクタリングをしない
- 目的外の改善をしない

上流実装が未完成の場合:
- mock / stub / TODO placeholder を使って進める
- 待機しない
- 不足 contract は team-lead に報告する

isolated-patch モードの場合:
- main working tree に直接書かない
- patch summary / touched files / apply order / expected conflicts / integrator follow-up を報告

完了時の報告:
- touched files
- added/changed symbols
- assumptions
- patch requests
- contract change requests
- risks
```

---

## Reviewer Prompt Template

```
あなたは <reviewer name> です。
実装は禁止です。

担当領域の compile-readiness / spec / ownership を検証してください。

見るもの:
- worker の差分
- Work Contract
- API Contract
- File Ownership
- Task 定義

必須チェック:
- 担当外ファイル編集がないか
- File Ownership 違反がないか
- import / access control / public API が正しいか
- protocol conformer 漏れがないか
- mock / InMemory / Preview stub が同期しているか
- Swift 6 Strict Concurrency 的に危険がないか
- Codable 後方互換が守られているか
- 既存経路の退行がないか
- spec に反していないか

判定:
PASS / FAIL / BLOCKED / WARN

FAIL / BLOCKED を informational として握りつぶしてはいけない。
```

---

## Integrator Prompt Template

```
あなたは integrator です。
あなたは最後に1人で統合する担当です。
大きな設計変更は禁止です。

入力:
- Work Contract
- API Contract
- Task Graph
- 各 worker の成果（direct-edit 反映済 / isolated-patch 形式）
- 各 reviewer の判定
- Patch Request
- 承認済 Contract Change Request

やること:
1. FAIL / BLOCKED が残っていないか確認
2. mergeAfter に従って統合順序を決める
3. 各 worker の atomic diff を取り込む（isolated-patch は順序に従って apply）
4. apply 時の conflict を検出・解消（worker の expected conflicts 報告を参照）
5. import / access control / public API のズレを直す
6. mock / InMemory / Preview stub の conformer 漏れを直す
7. 横断ファイルの wiring を行う（worker からの Patch Request 反映）
8. xcodegen generate が必要なら実行
9. swift build が可能なら実行
10. WARN を最終 report に残す

禁止:
- 新機能追加
- spec の勝手な変更
- 大規模リファクタリング
- worker の担当外実装を勝手に作り直す
- WARN の握りつぶし

最終 report:
- 完了した task
- 統合順序
- 修正した integration issue
- build / generate 結果
- 残 WARN
- ユーザーが確認すべきこと
```

---

## 待機禁止ルール

worker は原則として待機してはいけない。

**待機してよいのは以下だけ**:
- API Contract が存在しない
- 自分の editable file が存在しない
- File Ownership が衝突している
- spec 判断が必要
- canStart が false

それ以外は、mock / stub / TODO placeholder / Patch Request を使って進める。

**以下は禁止**:
- 「Domain が終わるまで待ちます」
- 「Persistence が終わるまで UI は進めません」
- 「Repository 実装がないので Preview は後でやります」
- 「他 worker の完了後に着手します」

**代わりに以下のように動く**:
- 「API Contract を正として実装しました」
- 「Repository 実体は未完成なので MockRepository に対して UI を完成させました」
- 「必要な AppRootView の変更は Patch Request として wiring-worker に送りました」
- 「mergeAfter に DOMAIN-01 を指定しています」

---

## 横断ファイルルール

横断ファイルは必ず**単独所有**にする。

例:
- AppRootView.swift: wiring-worker
- AppCoordinator.swift: wiring-worker
- DependencyContainer.swift: wiring-worker
- RepositoryProtocol.swift: domain-worker
- Tact.swift: domain-worker
- Package.swift: integrator
- project.yml: integrator

他 worker は横断ファイルを**直接編集してはいけない**。必要な変更は Patch Request にする。

---

## 出力モード

worker の outputMode は以下のどれかにする:

### direct-edit
担当ファイルを直接編集してよい。
条件:
- ファイル所有者が自分
- 他 worker と編集範囲が重ならない

### patch-request
担当外ファイルに対する変更提案のみ行う。
条件:
- 横断ファイル
- 他 worker 所有ファイル
- project.yml / Package.swift など統合影響が大きいファイル

### report-only
調査・レビューのみ。ファイル編集禁止。

### isolated-patch
worker は main working tree に**直接統合せず**、自分の atomic diff を **patch として出力**する。
integrator が最後に mergeAfter に従って取り込む。

**使用条件**:
- 変更規模が大きい
- 複数 worker が近い領域を触る
- conflict risk が高い
- integrator が最後に統合する前提
- 同一 working tree への同時書き込みを避けたい

**運用ポイント**:
- direct-edit と isolated-patch は混在可能（worker ごとに mode を変える）
- conflict risk が中程度なら direct-edit + Patch Request、高ければ isolated-patch を選ぶ

#### isolated-patch 出力形式

isolated-patch の出力形式は以下の優先順位に従う:

1. **unified diff**
2. **git diff 形式**
3. **ファイル単位の before / after**
4. **完全版ファイルコピー**

原則として **unified diff を最優先**する。

ただし、以下の場合のみ完全版ファイルコピーを許可する:
- 新規ファイル作成
- ファイル全体の置き換え
- diff より全文の方が安全に適用できる場合
- integrator が明示的に全文コピーを要求した場合

isolated-patch の報告には**必ず以下を含める**:
- **Patch Format**
- **Apply Target**
- **Apply Order**
- **Expected Conflicts**
- **Required Integrator Follow-up**

---

## 通信ルール

- worker は **ファイル1つ編集完了ごとに reviewer** に SendMessage で通知
- reviewer は中間状態を FAIL として team-lead に上げない（**フライング禁止**）。明白な compile error 直結（dangling 参照・型不一致・import 漏れ）は当該 worker に直接 SendMessage で指摘する程度に留める
- **統合検証は team-lead の明示トリガー後**に各 reviewer が並行で実行
- worker 間のスタック・spec 解釈の迷い・衝突検出は team-lead に SendMessage で報告
- 担当外ファイル変更が必要なら **Patch Request** として owner または team-lead に送る
- team-lead（自分）は **実装しない**、調整・意思決定・組間調停・spec 判断・統合検証トリガーに徹する

---

## iOS 固有の運用

- **worker / reviewer は xcodebuild を走らせない**（Preview 遅延防止、Xcode の index 構築と競合）。
- xcodebuild が必要な場合は、team-lead またはユーザー判断で最終確認として実行する。
- integrator は原則 `swift build` や package 単位の軽量検証までを担当する。
- xcodebuild を実行した場合は、最終 report の Build / Generate に結果を明記する。
- **ファイル追加/削除/リネーム後は必ず `xcodegen generate` 実行**（XcodeGen + SPM 構成の場合）。pbxproj の lastKnownFileType が folder のままだと SPM 経路で壊れるので `sed` で wrapper に置換
- 単一スキーマ + lightweight migration が基本。VersionedSchema 二重定義はチェックサム重複でクラッシュ

---

## Native SwiftUI First Rule

SwiftUI UI 実装では、原則として **native SwiftUI API を最優先**する。

**優先 API**:
- `List`
- `.swipeActions`
- `.sheet`
- `.toolbar`
- `NavigationStack`
- `PhotosPicker`
- `confirmationDialog`
- `alert`
- `Menu`
- `ButtonStyle`
- `ToggleStyle`

**禁止**:
- native API で満たせる操作を custom row / custom gesture / custom sheet として再実装すること
- custom 実装が必要な場合に、team-lead へ理由を出さずに勝手に実装すること

**custom 実装が必要な場合の必須報告**:
- native API で不足する理由
- custom 実装の範囲
- accessibility / gesture / animation / maintainability のリスク

team-lead は custom 実装提案を受けたら「やりたい挙動が純正で出せないか」「他に native combination で実現可能か」の 2 軸で判断する。安易な custom 実装承認は禁止。

---

## コンフリクト検出時の復旧手順

1. 該当 worker は **編集を即停止**（ファイル破壊の連鎖を防ぐ）
2. 変更済み差分の要約を team-lead に SendMessage で送る（追加した API・触ったファイル一覧）
3. team-lead が File Ownership を再決定
4. 非 owner は差分を **Patch Request に変換**（直接編集しない）
5. owner が必要分だけ取り込む
6. reviewer が再検証

---

## spec 整合性の運用

- worker が spec に従えない構造的制約に当たった時は **早期に team-lead に表面化**する（独断で代替実装に逃げない）
- reviewer は spec と実装の差異を見たら独断 informational 化せず team-lead に判断を仰ぐ
- team-lead は spec 違反 / 設計改善 / 構造的制約 / 実装コストの4軸で判断:
  - **構造的制約**（Features→App 物理的不可能 等）→ 正当な除外として PASS 可
  - **実装コスト問題**（書けば書ける）→ spec 優先
  - **設計改善**（spec の意図を更に強化）→ 承認可、最終 report で明示
  - **spec 違反**（意図と齟齬）→ 再実装要求

---

## 完了条件

以下をすべて満たした場合のみ完了とする:

- Work Contract が作成済み
- API Contract / Skeleton が確定済み（**Skeleton Owner = planner-architect**）
- 全 task に canStart / mergeAfter / dependsOnContract / outputMode がある
- File Ownership が衝突していない
- 全 worker が担当 atomic diff を完了
- **Patch Request が処理済み**（横断ファイル変更）
- **Contract Change Request が処理済み**（契約変更：承認 or 却下 or 代替案で決着）
- **isolated-patch 出力は integrator が apply 済み**
- reviewer の **FAIL がゼロ**
- reviewer の **BLOCKED がゼロ**
- WARN が最終 report に明記されている
- integrator が統合済み
- xcodegen generate が必要な場合は実行済み
- swift build が可能な場合はエラーゼロ
- 最終 report に未確認事項が明記されている

---

## 最終 report フォーマット

```md
# Team Result

## Summary
<何を完了したか>

## Execution Model
fan-out / fan-in

## Work Contract
<要約>

## Completed Tasks
| Task | Owner | Status | Files |
|---|---|---|---|

## Integration Order
<mergeAfter に基づく統合順序>

## Contract Changes
<承認された Contract Change Request の要約 / 影響範囲>

## isolated-patch Applied
<isolated-patch 出力を取り込んだ task と apply 順>

## Reviewer Results
| Reviewer | Result | Notes |
|---|---|---|

## Fixed Integration Issues
<統合時に直した import / access / conformer / mock など>

## Build / Generate
- xcodegen generate:
- swift build:
- xcodebuild:

## WARN / Remaining Risks
<残リスク>

## User Confirmation Needed
<ユーザーが最後に見るべきこと>
```

---

## 注意事項

- 10エージェント構成は最大値。それ以上は収穫逓減（コンフリクト管理コストが並行性メリットを上回る）
- 小規模構成は最大5名（team-lead 含む）
- team-lead は実装しない。調整・意思決定・組間調停・spec 判断・統合検証トリガーのみ
- integrator は1人に限定。複数人で統合作業しない
- メンバーがスタックしたら新メンバーで再開させる
- spec 違反は worker/reviewer から早期表面化させる（独断逃げ禁止）
- idle 通知は正常状態。idle teammate に新タスクが必要なら SendMessage で起こす
- チーム解散は最終ビルド通過確認後（SendMessage で `{type: "shutdown_request"}`）

---

## 自己レビュー（呼び出し時必須）

`/team` が呼ばれた瞬間、team-lead は以下を**実行前に**自己レビューする:

1. Work Contract が生成可能か（不可なら Phase 0 Task Compile に戻る）
2. Task Graph に canStart / mergeAfter / dependsOnContract / outputMode が全て埋まっているか
3. Worker Prompt が atomic diff 単位で書けるか
4. **Skeleton Owner が planner-architect として明示されているか**
5. 横断ファイルの単独所有者が決まっているか
6. integrator が 1 人だけ指名されているか
7. 待機禁止ルールが各 worker prompt に含まれているか
8. **Patch Request と Contract Change Request の使い分けが worker に伝わっているか**
9. **conflict risk の高い task は outputMode=isolated-patch になっているか**
10. reviewer 判定区分が PASS / FAIL / BLOCKED / WARN の 4 区分で運用されるか
11. **Reviewer Mechanical Gate が各 reviewer prompt に含まれているか**（compile basics / concurrency / UX basics）
12. **Phase 0.5 Session Start Sanity Check（xcodebuild -list）が実装系タスクで実行されているか**
13. **Native SwiftUI First Rule が UI task で worker prompt に含まれているか**
14. 完了条件に FAIL ゼロ / BLOCKED ゼロ / WARN 明記が入っているか

不足があれば、worker spawn 前にこのファイル自体を追記・修正してから進める。
