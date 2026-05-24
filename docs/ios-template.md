iOS アプリ アーキテクチャテンプレート

1. プロジェクト構造（workspace + XcodeGen）

root/
├── MyApp.xcworkspace/                # ルート workspace
├── MyApp/                            # アプリサブディレクトリ
│   ├── MyApp.xcodeproj/              # ★ XcodeGen で生成（git管理しない）
│   ├── project.yml                   # ★ XcodeGen 設定ファイル（git管理する）
│   ├── MyApp/                        # アプリソース
│   ├── MyAppTests/
│   └── MyAppUITests/
├── Packages/                         # ★ SPMパッケージはルート直下の Packages/ に配置
│   ├── Core/
│   ├── Data/
│   ├── Domain/
│   ├── DesignSystem/
│   └── Features/
└── docs/

★★★ パッケージは root/Packages/ にまとめること ★★★
★★★ xcodeproj は XcodeGen で生成する（手動編集禁止） ★★★
★★★ xcodeproj は .gitignore に追加する ★★★

workspace ファイル（MyApp.xcworkspace/contents.xcworkspacedata）:
<?xml version="1.0" encoding="UTF-8"?>
<Workspace version = "1.0">
   <FileRef location = "group:MyApp/MyApp.xcodeproj"></FileRef>
   <FileRef location = "group:docs"></FileRef>
</Workspace>

★ workspace には xcodeproj と docs のみ参照（Packages は参照しない）
★ パッケージは project.yml の packages + group: "" でプロジェクトナビゲーターに表示
★ Package.resolved は workspace レベルの xcshareddata/swiftpm/ に配置

---
2. Core パッケージ（基盤）

AppContext（依存注入）

// MyApp/Core/Sources/AppContext/AppContext.swift

public protocol AppContext:
    LoggerProvider &
    NetworkServiceProvider &
    UserServiceProvider &
    AnalyticsProvider {}

public protocol LoggerProvider {
    var logger: Logger { get }
}

public protocol NetworkServiceProvider {
    var networkService: NetworkService { get }
}

public protocol UserServiceProvider {
    var userService: UserService { get }
}

public protocol AnalyticsProvider {
    var analytics: Analytics { get }
}

// App/AppContext+Live.swift

final class LiveAppContext: AppContext {
    let logger: Logger = ConsoleLogger()
    let networkService: NetworkService = URLSessionNetworkService()
    let userService: UserService = FirebaseUserService()
    let analytics: Analytics = FirebaseAnalytics()
}

---
3. UIKit 資産を取り込む場合（参考）

★ 新規画面は原則 SwiftUI（セクション 4 参照）。UIKit は既存資産の再利用時のみ。
★ PencilKit / ARKit / Camera など UIKit でしか表現できない部品は UIViewRepresentable / UIViewControllerRepresentable で SwiftUI に取り込む（これは全パターン共通の例外として常に許容）。

ディレクトリ構造

MyApp/Features/Sources/Profile/
├── ProfileAssembly.swift              # 公開：組み立て
├── ProfileViewController.swift        # 内部：画面制御
├── ProfileInteractor.swift            # 内部：ビジネスロジック
├── ProfileViewModel.swift             # 内部：表示用モデル
├── ProfileViewModelBuilder.swift      # 内部：State→ViewModel変換
└── Components/                        # 内部：UIコンポーネント
    ├── ProfileHeaderView.swift
    └── ProfileCell.swift

Assembly（UIKit 版）

// ProfileAssembly.swift

import SwiftUI
import Core

public enum ProfileAssembly {
    @MainActor
    public static func screen(
        context: some AppContext,
        onEvent: @escaping (ProfileEvent) -> Void
    ) -> some View {
        // UIKit VC を UIViewControllerRepresentable で包んで返す
        ProfileRepresentable(context: context, onEvent: onEvent)
    }
}

Interactor / ViewController / ViewModel / ViewModelBuilder は ios-template.md の旧セクション3（git 履歴参照）に準ずる。

---
4. SwiftUI 実装テンプレート（メインパターン）

ディレクトリ構造

MyApp/Features/Sources/Settings/
├── SettingsAssembly.swift             # 公開：組み立て（some View を返す）
├── SettingsScreen.swift               # 内部：Screenエントリポイント
├── SettingsContent.swift              # 内部：メインUI
├── SettingsViewModel.swift            # 内部：ビジネスロジック
├── SettingsViewState.swift            # 内部：画面状態
├── SettingsViewEvent.swift            # 内部：ユーザーアクション
├── SettingsEvent.swift                # 公開：外部通知
└── Components/                        # 内部：UIコンポーネント
    ├── SettingsRow.swift
    └── SettingsSection.swift

Assembly（SwiftUI 版）

// SettingsAssembly.swift

import SwiftUI
import Core

public enum SettingsAssembly {
    @MainActor
    public static func screen(
        context: some SettingsViewModel.Context,
        onEvent: @escaping (SettingsEvent) -> Void
    ) -> some View {
        let viewModel = SettingsViewModel(context: context, onEvent: onEvent)
        return SettingsScreen(viewModel: viewModel)
    }
}

★ Assembly の戻り値は `some View`（UIViewController / UIHostingController を返さない）
★ NavigationStack / sheet / fullScreenCover はすべて Coordinator 側で管理する

Screen

// SettingsScreen.swift

import SwiftUI

struct SettingsScreen: View {
    @Bindable var viewModel: SettingsViewModel

    var body: some View {
        SettingsContent(
            viewState: viewModel.viewState,
            onViewEvent: viewModel.send
        )
        .onAppear { viewModel.send(.onAppear) }
        .navigationTitle("Settings")
    }
}

Content

// SettingsContent.swift

import SwiftUI

struct SettingsContent: View {
    let viewState: SettingsViewState
    let onViewEvent: (SettingsViewEvent) -> Void

    var body: some View {
        List {
            Section("Account") {
                SettingsRow(title: "Profile", icon: "person.circle") {
                    onViewEvent(.onTapProfile)
                }
                SettingsRow(title: "Notifications", icon: "bell") {
                    onViewEvent(.onTapNotifications)
                }
            }
            Section("App") {
                Toggle("Dark Mode", isOn: Binding(
                    get: { viewState.isDarkMode },
                    set: { onViewEvent(.onToggleDarkMode($0)) }
                ))
            }
            Section {
                Button("Sign Out", role: .destructive) {
                    onViewEvent(.onTapSignOut)
                }
            }
        }
        .overlay {
            if viewState.isLoading { ProgressView() }
        }
    }
}

ViewModel

// SettingsViewModel.swift

import Foundation
import Observation
import Core

@Observable
@MainActor
final class SettingsViewModel {
    typealias Context = UserServiceProvider & LoggerProvider & AnalyticsProvider

    private let context: any Context
    let onEvent: (SettingsEvent) -> Void
    private(set) var viewState: SettingsViewState

    init(
        context: any Context,
        onEvent: @escaping (SettingsEvent) -> Void,
        viewState: SettingsViewState = SettingsViewState()
    ) {
        self.context = context
        self.onEvent = onEvent
        self.viewState = viewState
    }

    func send(_ event: SettingsViewEvent) {
        switch event {
        case .onAppear:        handleOnAppear()
        case .onTapProfile:    onEvent(.navigateToProfile)
        case .onTapNotifications: onEvent(.navigateToNotifications)
        case .onToggleDarkMode(let v): handleToggleDarkMode(v)
        case .onTapSignOut:    handleSignOut()
        }
    }

    private func handleOnAppear() {
        context.analytics.track("settings_viewed")
        viewState.isLoading = true
        Task { viewState.isLoading = false }
    }

    private func handleToggleDarkMode(_ isEnabled: Bool) {
        viewState.isDarkMode = isEnabled
    }

    private func handleSignOut() {
        Task {
            viewState.isLoading = true
            try? await context.userService.signOut()
            viewState.isLoading = false
            onEvent(.didSignOut)
        }
    }
}

ViewState / ViewEvent / Event

// SettingsViewState.swift
struct SettingsViewState: Equatable {
    var isLoading: Bool = false
    var isDarkMode: Bool = false
    var notificationsEnabled: Bool = true
}

// SettingsViewEvent.swift
enum SettingsViewEvent {
    case onAppear
    case onTapProfile
    case onTapNotifications
    case onToggleDarkMode(Bool)
    case onTapSignOut
}

// SettingsEvent.swift
public enum SettingsEvent {
    case navigateToProfile
    case navigateToNotifications
    case didSignOut
}

---
5. Coordinator 実装テンプレート（NavigationStack ベース）

★ Coordinator は `@Observable @MainActor final class` + `NavigationPath` + `Route: Hashable enum` の3点セット
★ UIKit Coordinator 基底クラス（ViewCoordinator / NavigationCoordinator）は使わない
★ NavigationStack + navigationDestination で画面遷移、sheet / fullScreenCover でモーダル

ディレクトリ構造

App/
├── AppCoordinator.swift               # Auth state で AuthRoot / MainRoot を切替
├── Routes/
│   ├── MainRoute.swift                # メインフロー Route enum
│   └── AuthRoute.swift                # 認証フロー Route enum
├── Coordinators/
│   ├── MainNavigationCoordinator.swift
│   └── AuthenticationCoordinator.swift
└── Views/
    ├── MainRootView.swift
    └── AuthenticationRootView.swift

Route enum

// MainRoute.swift

enum MainRoute: Hashable {
    case profile
    case search
    case chat(senderUID: String, receiverUID: String)
    case userProfile(ProfileModel)
    case followList(uid: String, listType: FollowListType, userName: String)
    case postDetail(PostModel, selectedFriends: [ProfileModel])
    case placeViewer
}

// AuthRoute.swift

enum AuthRoute: Hashable {
    case profileSetup
}

Coordinator

// MainNavigationCoordinator.swift

import SwiftUI
import Observation
import Core

@Observable
@MainActor
final class MainNavigationCoordinator {
    var path: NavigationPath = NavigationPath()

    // sheet / fullScreenCover 用 state
    var presentedPlacePosting: ARPlacementPayload? = nil
    var isPresentingPlacePicker: Bool = false

    private let appContext: AppContext

    init(appContext: AppContext) {
        self.appContext = appContext
    }

    // MARK: - Navigation

    func push(_ route: MainRoute) {
        path.append(route)
    }

    func pop() {
        guard !path.isEmpty else { return }
        path.removeLast()
    }

    func popToRoot() {
        path.removeLast(path.count)
    }

    // MARK: - Event Handlers

    func handleSearchRoleTabEvent(_ event: SearchRoleTabEvent) {
        switch event {
        case .navigateToProfile:      push(.profile)
        case .navigateToSearch:       push(.search)
        case .navigateToARViewer:     push(.placeViewer)
        case .navigateToYosegakiCreation: isPresentingPlacePicker = true
        case .navigateToPlacePosting(let payload): presentedPlacePosting = payload
        case .navigateToParticipatedSheet(let items):
            guard let (post, _, friends) = items.first else { return }
            push(.postDetail(post, selectedFriends: friends))
        }
    }

    // ... 各 Feature Event ハンドラを同様に実装
}

Root View

// MainRootView.swift

import SwiftUI

struct MainRootView: View {
    @State private var coordinator: MainNavigationCoordinator

    init(appContext: AppContext) {
        _coordinator = State(initialValue: MainNavigationCoordinator(appContext: appContext))
    }

    var body: some View {
        NavigationStack(path: $coordinator.path) {
            SearchRoleTabAssembly.screen(
                context: coordinator.appContext,
                onEvent: { coordinator.handleSearchRoleTabEvent($0) }
            )
            .navigationDestination(for: MainRoute.self) { route in
                switch route {
                case .profile:
                    ProfileAssembly.screen(context: coordinator.appContext) { event in
                        coordinator.handleProfileEvent(event)
                    }
                case .search:
                    SearchAssembly.screen(context: coordinator.appContext) { event in
                        coordinator.handleSearchEvent(event)
                    }
                case .chat(let s, let r):
                    ChatAssembly.screen(context: coordinator.appContext, senderUID: s, receiverUID: r) { _ in }
                case .userProfile(let user):
                    ProfileAssembly.userProfileScreen(context: coordinator.appContext, user: user) { event in
                        coordinator.handleUserProfileEvent(event)
                    }
                case .postDetail(let post, let friends):
                    PrivatePostAssembly.postDetailScreen(
                        post: post, selectedFriends: friends, context: coordinator.appContext
                    ) { event in coordinator.handlePostDetailEvent(event) }
                case .placeViewer:
                    PlaceViewerAssembly.screen(context: coordinator.appContext) { event in
                        switch event {
                        case .didTapDismiss: coordinator.pop()
                        }
                    }
                case .followList(let uid, let listType, let userName):
                    ProfileAssembly.followListScreen(
                        context: coordinator.appContext, targetUID: uid,
                        listType: listType, userName: userName
                    ) { event in coordinator.handleFollowListEvent(event) }
                }
            }
        }
        .fullScreenCover(item: $coordinator.presentedPlacePosting) { payload in
            PlacePostingAssembly.screen(payload: payload, context: coordinator.appContext) { _ in
                coordinator.presentedPlacePosting = nil
            }
        }
        .sheet(isPresented: $coordinator.isPresentingPlacePicker) {
            PrivatePostAssembly.placePickerScreen { event in
                switch event {
                case .didCancel, .didConfirm: coordinator.isPresentingPlacePicker = false
                }
            }
        }
    }
}

AppCoordinator（Auth state ルーター）

// AppCoordinator.swift

import SwiftUI
import Core

struct AppCoordinator: View {
    @StateObject private var authStateManager = AuthStateManager.shared

    var body: some View {
        switch authStateManager.authState {
        case .loading:
            SplashView()
        case .signedOut, .needsProfile:
            AuthenticationRootView(appContext: LiveAppContext.shared)
        case .signedIn:
            MainRootView(appContext: LiveAppContext.shared)
        }
    }
}

---
6. Package.swift 設定例

// Packages/Features/Package.swift
// ★ パッケージ間の依存は ../Core のように Packages/ 内の相対パスで参照

// swift-tools-version: 6.0

import PackageDescription

let package = Package(
    name: "Features",
    platforms: [.iOS(.v18)],
    products: [
        .library(name: "Home", targets: ["Home"]),
        .library(name: "Profile", targets: ["Profile"]),
        .library(name: "Settings", targets: ["Settings"]),
    ],
    dependencies: [
        .package(path: "../Core"),
        .package(path: "../Domain"),
        .package(path: "../DesignSystem"),
    ],
    targets: [
        .target(name: "Home",     dependencies: ["Core", "Domain", "DesignSystem"]),
        .target(name: "Profile",  dependencies: ["Core", "Domain", "DesignSystem"]),
        .target(name: "Settings", dependencies: ["Core", "Domain", "DesignSystem"]),
    ]
)

---
7. 設計原則まとめ

モジュール依存ルール

App (Coordinators / RootViews)
    ↓ import
Features (Home, Profile, Settings...)  ← 相互参照禁止
    ↓ import
Core + Domain + DesignSystem

公開範囲

各機能モジュールが公開するもの：
- Assembly - 画面生成（`some View` を返す static func）
- Event - 外部通知
- 必要な型定義のみ

ファイル命名規則
┌──────────────────┬────────────────────────────────────┐
│      種類        │               命名                 │
├──────────────────┼────────────────────────────────────┤
│ Assembly         │ {Feature}Assembly.swift            │
│ Screen           │ {Feature}Screen.swift              │
│ Content          │ {Feature}Content.swift             │
│ ViewModel        │ {Feature}ViewModel.swift           │
│ ViewState        │ {Feature}ViewState.swift           │
│ ViewEvent        │ {Feature}ViewEvent.swift           │
│ Event            │ {Feature}Event.swift               │
│ Coordinator      │ {Feature}NavigationCoordinator.swift│
│ Route            │ {Feature}Route.swift               │
│ Root View        │ {Feature}RootView.swift            │
└──────────────────┴────────────────────────────────────┘

データフロー

[SwiftUI — メインパターン]
User Action → ViewEvent → ViewModel.send() → ViewState 変更
                                    ↓
                            @Observable 自動更新
                                    ↓
                              Content 再描画
                                    ↓
                   onEvent({Feature}Event) → Coordinator.handle()
                                    ↓
                    coordinator.push(Route) / present sheet

[UIKit 部品の取り込み（例外）]
UIViewRepresentable / UIViewControllerRepresentable → SwiftUI View
PencilKit / ARKit / Camera → この経路で SwiftUI に流し込む

---
機能追加手順:

1. 新機能モジュール追加 → Packages/Features/Sources/{Feature}/
2. Route case 追加 → App/Routes/{Scope}Route.swift
3. Coordinator に Event ハンドラ追加 → App/Coordinators/{Scope}NavigationCoordinator.swift
4. navigationDestination に case 追加 → App/Views/{Scope}RootView.swift
5. Package.swift 更新 → target と product を追加
6. project.yml 更新 → dependencies に追加
7. xcodegen generate で xcodeproj を再生成

---
8. XcodeGen によるプロジェクト管理

★★★ xcodeproj は XcodeGen で生成する。手動編集禁止 ★★★
★★★ pbxproj を直接いじるな ★★★

--- project.yml の書き方 ---

name: MyApp

options:
  deploymentTarget:
    iOS: "18.0"

packages:
  Domain:
    path: ../Packages/Domain
    group: ""
  Core:
    path: ../Packages/Core
    group: ""
  Data:
    path: ../Packages/Data
    group: ""
  DesignSystem:
    path: ../Packages/DesignSystem
    group: ""
  Features:
    path: ../Packages/Features
    group: ""

targets:
  MyApp:
    type: application
    platform: iOS
    sources:
      - MyApp
    settings:
      base:
        DEVELOPMENT_TEAM: <チームID>
    dependencies:
      - package: Domain
      - package: Core
      - package: Data
      - package: DesignSystem
      - package: Features
        product: Home
      - package: Features
        product: Settings

★ packages の path は ../Packages/{Name}（xcodeproj からの相対パス）
★ group: "" で各パッケージをプロジェクトナビゲーターのルートに直接配置

--- xcodeproj 生成手順 ---

Step 1: cd MyApp && xcodegen generate
Step 2: 全パッケージの lastKnownFileType を folder→wrapper に sed で修正

禁止事項
- pbxproj を手動編集するな
- Xcode GUI から File → Add Package Dependencies するな
- ユーザーが配置したファイル・フォルダを勝手に削除・移動するな
- パッケージ内に .build/ .swiftpm/ を残すな
