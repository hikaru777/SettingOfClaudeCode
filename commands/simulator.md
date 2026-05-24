# /simulator — iOS シミュレーター管理

シミュレーターの一覧表示・起動・シャットダウン・デバイス選択を行う。

## サブコマンド

引数に応じて処理を分岐する：

### 引数なし または `list`
利用可能なシミュレーターを整形して表示する：
```bash
xcrun simctl list devices available
```
iOS バージョンごとにグループ化して、Booted/Shutdown 状態もわかりやすく表示する。

---

### `boot <デバイス名またはUDID>`
指定のシミュレーターを起動して Simulator.app を開く：
```bash
# デバイス名から UDID を検索
xcrun simctl list devices available | grep "<デバイス名>"

xcrun simctl boot <UDID>
open -a Simulator
```

---

### `shutdown <デバイス名またはUDID>`
指定のシミュレーターをシャットダウンする：
```bash
xcrun simctl shutdown <UDID>
```

### `shutdown all`
全シミュレーターをシャットダウンする：
```bash
xcrun simctl shutdown all
```

---

### `open`
Simulator.app を開く：
```bash
open -a Simulator
```

---

### `select`
Booted のシミュレーター一覧を表示して、どれを `/run` のデフォルトにするか選ばせる。
ユーザーが選んだデバイスを `/run` コマンドで使うよう伝える。

---

### `erase <デバイス名またはUDID>`
シミュレーターのデータを消去（工場出荷状態に戻す）：
```bash
xcrun simctl erase <UDID>
```

---

## デバイス名から UDID を取得する方法

```bash
xcrun simctl list devices available | grep "<デバイス名>" | grep -oE '[0-9A-F-]{36}'
```

デバイス名が一意でなければ、マッチしたものを全部表示してユーザーに選ばせる。
