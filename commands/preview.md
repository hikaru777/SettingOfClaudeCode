# /preview — SwiftUI Preview 自動生成

ファイル名を渡すだけで、その画面用のテストデータを揃えた `#Preview` ブロックを末尾に追加する。

## 引数

- `$ARGUMENTS`: 対象ファイル名（拡張子は省略可）。例:
  - `FreeThreadContent.swift`
  - `FreeThreadContent`
  - 絶対パス・相対パスでも可

## 基本方針

- **対象ファイル末尾に `#Preview { ... }` を追加する**（既存があれば上書きせず別名で追加）
- Preview に必要なテストデータは **同ファイル内に `private` で定義**する。別ファイルは作らない
- iOS テンプレート（Assembly/Screen/Content/ViewModel/ViewState）に従ったプロジェクトを前提
- ホットリロード（InjectionIII）と Xcode Canvas の両方で動くこと
- ★ **「動作が完璧に確認できる Preview」を作る** — 静的スナップショットではなく、ボタンタップ・遷移・モーフィング・状態切替が Preview Canvas で実際に動くこと
- インタラクションを持つ View（callback / @Binding / @Observable / トグル状態 を持つ）は **必ず Interactive Harness 方式** で作る

## 手順

### Step 1: ファイル特定

引数からファイルを特定する。

```bash
# 拡張子なしで来た場合は補完
# パス指定なら直接、ファイル名だけならカレントから find
find . -type f -name "<filename>.swift" -not -path "*/.build/*" -not -path "*/DerivedData/*" 2>/dev/null
```

ヒットが複数ある場合は候補を提示してユーザーに選ばせる。1 件なら確定。

### Step 2: 種別判定

ファイル内容を読み、以下のどれかを判定する：

| 種別           | 判定基準                                               | Preview の作り方                            |
| -------------- | ------------------------------------------------------ | ------------------------------------------- |
| **Content**    | `struct *Content: View` で `viewState` / `onViewEvent` | ViewState のテストデータ + `{ _ in }` ハンドラ |
| **Screen**     | `struct *Screen: View` で `@Bindable var viewModel`    | Preview 用 mock ViewModel を組み立てる         |
| **Component**  | `struct *: View` で単独パーツ                          | 必要なプロパティに最小限のテストデータ          |
| **Assembly**   | `enum *Assembly` で `static func screen(...)`          | `screen(context: PreviewContext(), onEvent: { _ in })` で呼ぶ |
| **その他 View**| 上記に当てはまらない `View`                            | プロパティを読み取って手動でテストデータ生成    |

### Step 3: 依存型の収集

Preview に必要な型を集める。**型定義ファイルを直接読みに行く**こと。grep で見つからなければ全プロジェクトから探す。

集める対象：
- ViewState の定義（`*ViewState.swift`）
- ViewEvent の定義（`*ViewEvent.swift`）  
- 引数で受け取るモデル（`*Model.swift` / `*.swift` の struct/enum）
- enum の case 一覧（テストデータで使う value を選ぶため）
- 画像・URL・ID 系は実在しなくてよい（プレースホルダで OK）

### Step 4: テストデータ生成

各依存型について、以下の規則で **意味のあるテストデータ** を組み立てる：

- **String**: 画面の文脈に合った日本語サンプル（"こんにちは、シンジ君" など空文字や "test" は禁止）
- **Int / Double**: 0 ではなく現実的な値（いいね 42、距離 1.2km 等）
- **Date**: `Date()` か `.now.addingTimeInterval(-3600)` で相対時刻
- **URL**: `URL(string: "https://picsum.photos/200")!` などダミー画像 URL
- **Bool**: false ではなく true 側の見た目も確認できるよう状況に応じて
- **配列**: 空配列ではなく **3-5 件** 入れる（リスト UI の確認のため）
- **Optional**: `.some` 側のデータを優先（nil 表示も別 Preview で別途確認）
- **enum**: 一番代表的な case を選ぶ。loading/error は別 Preview で

★ **空・nil・0 で済ませるな。** Preview の役目は「動く見た目を確認すること」。

### Step 5: Preview ブロック生成

ファイル末尾に以下のテンプレートで追加する。

#### Content の場合

```swift
#Preview("Default") {
    <Feature>Content(
        viewState: <Feature>ViewState(
            // 意味のあるテストデータ
        ),
        onViewEvent: { _ in }
    )
}

#Preview("Loading") {
    <Feature>Content(
        viewState: <Feature>ViewState(isLoading: true),
        onViewEvent: { _ in }
    )
}

#Preview("Empty") {
    <Feature>Content(
        viewState: <Feature>ViewState(items: []),
        onViewEvent: { _ in }
    )
}
```

複数バリエーション（Default / Loading / Empty / Error）を **適用できるものだけ** 出す。Loading 状態が ViewState に存在しないなら出さない。

#### Screen / Assembly の場合

Preview 用の mock context / mock ViewModel を**同ファイル末尾に private で定義**する：

```swift
#if DEBUG
@MainActor
private final class PreviewContext: <Feature>ViewModel.Context {
    var logger: Logger = ConsoleLogger()
    var userService: UserService = MockUserService()
    // ... 必要な provider のみ
}

private final class MockUserService: UserService {
    // メソッドは空実装または preview に妥当な値を返す
}
#endif

#Preview("Default") {
    <Feature>Screen(
        viewModel: <Feature>ViewModel(
            context: PreviewContext(),
            onEvent: { _ in }
        )
    )
}
```

mock service が既に DesignSystem や Core にあるなら再利用する。なければ最小実装をその場で書く。

#### Component の場合（インタラクションなし — 純粋な見た目だけの場合）

```swift
#Preview {
    VStack(spacing: 16) {
        <Component>(/* 通常状態 */)
        <Component>(/* 別バリエーション */)
    }
    .padding()
}
```

#### Component / View の場合（インタラクションあり — **Interactive Harness 方式**）

★ callback / @Binding / トグル状態 / モーフィング / 遷移 を持つ View は **必ずこの方式**。静的スナップショット（callback を `{}` で済ませる）は禁止。

```swift
#if DEBUG
/// 各ボタン・トグル・遷移を実際に押して動作確認するためのインタラクティブ Harness。
/// 静的 Preview だと morphing / search expand / state 切替の挙動が見えないため。
private struct <View>PreviewHarness: View {
    // 対象 View が外部から受ける全状態を @State でローカル保持
    @State private var flagA: Bool = true
    @State private var keyword: String = ""
    @State private var subtitle: String? = "初期値"
    @State private var observableState = SomeObservableState()
    @State private var lastEvent: String = "—"

    var body: some View {
        VStack(spacing: 0) {
            <View>(
                // すべての引数を @State / Binding / 環境注入で繋ぐ
                flagA: flagA,
                searchKeyword: $keyword,
                subtitle: subtitle,
                onTapA: {
                    lastEvent = "A tap"
                    withAnimation(.spring(response: 0.45, dampingFraction: 0.7)) {
                        flagA.toggle()
                    }
                },
                onTapB: {
                    lastEvent = "B tap → 別状態へ"
                    withAnimation { subtitle = "B 状態" }
                }
            )
            .environment(observableState)

            controlPanel
                .padding(16)

            Spacer(minLength: 0)
        }
        .background(/* 実機の背景色に近いもの */)
    }

    /// 全フラグを直接操作できるパネル。Toggle / Picker / Slider / 最終イベント表示 を必ず置く。
    private var controlPanel: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("コントロール").font(.headline)

            Toggle("flagA", isOn: $flagA.animation(.spring(response: 0.45, dampingFraction: 0.7)))

            Picker("subtitle", selection: $subtitle) {
                Text("なし").tag(String?.none)
                Text("A").tag(String?.some("A"))
                Text("B").tag(String?.some("B"))
            }
            .pickerStyle(.menu)

            // @Observable な値があれば Slider で直接動かせるようにする
            VStack(alignment: .leading, spacing: 4) {
                Text("observableValue: \(String(format: "%.2f", observableState.value))")
                    .font(.caption.monospaced())
                Slider(
                    value: Binding(
                        get: { observableState.value },
                        set: { observableState.value = $0 }
                    ),
                    in: 0 ... 1
                )
            }

            VStack(alignment: .leading, spacing: 2) {
                Text("最後のイベント").font(.caption2).foregroundStyle(.secondary)
                Text(lastEvent).font(.caption.monospaced())
            }
        }
        .padding(14)
        .background(Color.white.opacity(0.7))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}
#endif

#Preview("Interactive") {
    <View>PreviewHarness()
}
```

**Harness が満たすべき要件**:
1. 対象 View の **全 callback** を State 操作に繋ぐ（タップで実際にフラグが動く）
2. 対象 View の **全 Binding** をローカル `@State` で持つ
3. **コントロールパネル** で各フラグを直接操作できる（Toggle / Picker / Slider / TextField）
4. **「最後のイベント」表示** で押したボタンが何だったか視認できる
5. アニメーション付きの状態変化は `withAnimation` で囲む（実機と同じ spring / smooth カーブを使う）
6. `@Observable` な共有状態は `.environment` で注入し、Slider 等で動かせるようにする

### Step 6: 検証

Preview ブロックを書いたら以下を確認する：

1. ファイルに `import SwiftUI` が入っているか（無ければ追加）
2. テストデータの型が一致しているか（コンパイルエラーになる箇所がないか）
3. private な mock / Harness を `#if DEBUG` で囲んだか
4. 既存の `#Preview` を**削除していない**か
5. インタラクションを持つ View が静的スナップショット（callback を `{}` で済ませる形）になっていないか

★ **xcodebuild は走らせない**（`feedback_no_agent_xcodebuild`）。コンパイル確認は Xcode Canvas / ユーザーの再ビルドに任せる。エージェント側は静的に型整合をチェックするだけにする。

### Step 7: 報告

以下を 1 メッセージで報告する：

- 対象ファイルの絶対パス
- 追加した Preview の名前一覧（例: "Default", "Loading", "Empty"）
- 同ファイルに追加した private mock 型があれば一覧
- ビルドが通ったかどうか

## 禁止事項

- **別ファイルを作るな。** Preview もテストデータも対象ファイル末尾に追加する
- **既存の `#Preview` を消すな。** 同名なら "Default 2" のように別名で並べる
- **空文字 / 0 / 空配列で済ませるな。** Preview の意義を失う
- **Mock を Production コードに混ぜるな。** 必ず `#if DEBUG ... #endif` で囲む
- **手当たり次第に複数 Preview を作るな。** ViewState に存在する状態のみ Preview 化する
- **callback を `{}` だけで済ませるな。** インタラクション持ちの View は Interactive Harness で State に繋ぎ、ボタンタップで実際にフラグが動くようにする
- **xcodebuild を走らせるな。** `feedback_no_agent_xcodebuild` 厳守。コンパイル確認は Xcode Canvas に任せる

## トラブルシューティング

- **依存型が見つからない**: `grep -r "struct <Type>" --include="*.swift"` で全プロジェクト走査
- **Context protocol が複雑すぎる**: 必要最小限の provider だけ満たす Context を作る。`UserServiceProvider & LoggerProvider` のように
- **ViewModel の init で副作用がある**: Preview 用に `viewState` を直接渡せる init があるか確認。なければ Content だけ Preview する
- **Singleton（`*.shared`）が絡む**: そこを通る初期化は Preview でハングする。必ず明示的に値を渡す形に書き換える
- **InjectionIII と競合**: `@ObserveInjection` 等は Preview には不要。CLAUDE.md の通り App.swift で一括処理されているので個別 View には付けない
