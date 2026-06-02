# /verify-swift

Swift / SwiftUI 実装後の機械的検証を行う。

## 目的

reviewer が見逃しやすい初歩的な Swift / SwiftUI / build 環境ミスを検出する。

`/team` と組み合わせる位置:

```
/team "機能を実装して"
  ↓
planner が Work Contract を作る
  ↓
worker が一斉に実装
  ↓
reviewer が見る
  ↓
integrator が統合
  ↓
/verify-swift で機械確認  ← ここ
  ↓
最終報告
```

`/team` は「作業を進めるチーム」、`/verify-swift` は「Swift 的に初歩ミスがないか見る検査コマンド」。役割分担を混ぜない。

## 実行方針

- **実装はしない**。検証と報告だけ行う。
- 修正が必要な場合は、勝手に直さず **FAIL / WARN として報告**する。
- xcodebuild は重いため、**明示指示がない限り実行しない**（worker / reviewer は xcodebuild 走らせない原則を踏襲）。
- swift build が可能な package があれば軽量検証として実行する。

## 確認項目

### 1. Build Environment

- `xcodebuild -list` を実行し、scheme 名を確認する
- プロジェクトの CLAUDE.md（または `~/app/<project>/CLAUDE.md`）に既知 scheme 名があれば照合する
- 推測 scheme 名（`Tact`、`MyApp` 等の短縮形）を使わない
- `project.yml` / XcodeGen / `Package.swift` の有無を確認する

### 2. Lightweight Build

可能なら以下を実行する:

- Swift Package 構成なら `swift build --package-path <path>` を package 単位で実行
- XcodeGen 構成で `xcodegen generate` の必要性を確認（.swift 追加/削除/リネーム後は必要）
- xcodebuild は重いため、明示指示がない限り実行しない

### 3. Foundation Import Check

以下の型を使う Swift file で `import Foundation` があるか確認する:

- `Date`
- `URL`
- `UUID`
- `Calendar`
- `Locale`
- `TimeZone`
- `DateFormatter`
- `ISO8601DateFormatter`
- `Data`
- `JSONEncoder` / `JSONDecoder`

不足があれば **FAIL**。

検出コマンド例:
```sh
grep -rln --include="*.swift" -E "Date|URL|UUID|Calendar|Locale|TimeZone|DateFormatter" <path> | \
  xargs grep -L "^import Foundation"
```

### 4. SwiftUI Symbol Check

以下を確認する:

- `.foregroundStyle(.accent)` のような存在しない / 怪しい modifier usage がないか
- native SwiftUI API で足りる箇所に custom implementation を作っていないか
- `List` / `.swipeActions` / `.sheet` / `.toolbar` / `NavigationStack` / `PhotosPicker` / `confirmationDialog` / `alert` / `Menu` で足りる要件を custom 実装していないか
- ToolbarItem 内に背景色 / glassEffect / padding / frame / Spacer が付いていないか（HStack でテキスト/アイコンのみが正）

検出コマンド例:
```sh
grep -rn --include="*.swift" -E "\.foregroundStyle\(\.accent\b" <path>
grep -rn --include="*.swift" -E "ToolbarItem.*\{" -A 20 <path> | grep -E "glassEffect|background|padding"
```

### 5. Swift Concurrency Check

以下を確認する:

- @MainActor isolation violation の可能性
- @MainActor クラス内で `await MainActor.run { }` の冗長使用がないか（直接代入で OK）
- Sendable が必要な型の不足
- @Sendable closure 内 captured var mutation
- #Predicate 内の参照型 capture

### 6. Duplicate Declaration Check

以下を確認する:

- duplicate variable declaration
- duplicate property declaration
- duplicate method declaration
- 同一 scope に同名 state がないか

検出コマンド例:
```sh
grep -rn --include="*.swift" -E "^\s*(var|let|func)\s+\w+" <path> | \
  awk -F: '{print $1, $3}' | sort | uniq -c | awk '$1 > 1'
```

### 7. UX State Check

confirm / save / apply / done 系 UI では以下を確認する:

- **unchanged state で disabled** になっているか
- dirty state を `savedSnapshot` / `initialState` と比較しているか
- empty / loading / error / selection state が必要な UI で抜けていないか

selection UI では以下を確認する:

- none selected
- partial selected
- all selected
- empty list

検出は構造的に行う（Button + confirm/save/apply 系のラベル → .disabled の有無）。完全自動は難しいので、対象 view を列挙して **目視確認推奨** として WARN に上げる。

### 8. Codable 後方互換 Check

- 新規追加 field が `decodeIfPresent + デフォルト値` パターンになっているか
- 既存 snapshot を decode した時に throw しない構造か

## 出力形式

```md
# Verify Swift Result

## Summary
PASS / FAIL / WARN

## Build Environment
- scheme: <検出した scheme 名 / 期待値との一致>
- package: <検出した package paths>
- xcodegen: <generate 必要性>
- baseline: <swift build 結果 / 実行可否>

## FAIL
| File | Issue | Required Fix |
|---|---|---|

## WARN
| File | Risk | Suggested Check |
|---|---|---|

## Notes
<補足 / 検出できなかった項目 / 目視確認推奨箇所>
```

## 判定区分

- **PASS**: 全 8 項目クリア。FAIL / WARN ゼロ
- **FAIL**: import 漏れ / duplicate declaration / 存在しない API / disabled 漏れなど明確な問題あり
- **WARN**: 自動検出では確定できないが目視確認推奨（UX state / native preference の妥当性等）

## 引数

- 任意のテキスト: 検証対象のパス（省略時は cwd）

## 使用例

```
/verify-swift /Users/hondahikaru/app/Tact/Packages/Features
/verify-swift   ← cwd の全 Swift file
```

## Hook 化への道筋

このコマンドが安定し漏れがなくなったら、PostToolUse hook で軽量サブセットを自動実行する選択肢がある。ただし xcodebuild は重いので、最初は手動 `/verify-swift` 運用が安全。
