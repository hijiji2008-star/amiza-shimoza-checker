# caffeine tracker: Sliding-window time graph (design)

## Goal
- 折れ線グラフを「**中央＝現在時刻**」にし、時間経過とともに **表示範囲（窓）がスライド**していく体験にする。
- 既存のカフェイン残量計算（`caffeineAt(tHours)`）はそのまま利用する。

## Non-goals
- カフェイン計算式・半減期（`HALF_LIFE`）の変更
- UI全体のリデザイン
- Canvas化などの大規模な描画方式変更

## Current state (relevant)
- `caffeine_tracker/index.html`
  - `updateGraph()` が 0:00〜24:00 を固定で 30分刻み（48点）にサンプルし、SVGのパスを更新
  - 1分ごとに `updateGraph()` を呼ぶ（`setInterval(..., 60_000)`）
  - Xラベルは固定テキスト（0/6/12/18/24）

## Proposed behavior
### Sliding window
- 表示レンジは **合計 12時間**（左右に **±6時間**）をデフォルトとする
  - 中央（グラフの真ん中のX位置）が **現在時刻 `now`** を表す
  - 左端が `now - 6h`、右端が `now + 6h`
- 時間経過（1分ごとの再描画）により、窓がなめらかにスライドしていく

### Center time display / now marker
- グラフ中央に **現在時刻（`HH:MM`）** を表示する
- 中央に「いま」を示す **縦の基準線**を追加する（薄い色）

### X-axis labels
- 固定の 0/6/12/18/24 表示はやめ、窓に合わせて以下の5点を表示する
  - `now - 6h`, `now - 3h`, `now`, `now + 3h`, `now + 6h`
- ラベル表示は 24h をまたぐため、内部計算（連続時間）と表示（時計）を分離する
  - 表示用は 0〜24 に丸め、`HH:MM` 表記にする

### Sampling & rendering
- 表示窓内で `N` 点サンプリングして折れ線を作る
  - 初期は現状と同等の密度（48点）を踏襲し、`N=48` をデフォルト
  - `tHours` は `start = nowH - 6` から `end = nowH + 6` の範囲で線形に生成
  - 各点は `caffeineAt(tHours)` を呼ぶ（`tHours` が 0〜24 を外れる場合は「前日/翌日」として計算する）

#### Day wrap handling (continuous time)
- `caffeineAt()` の入力 `tHours` は「0〜24に制限しない」連続時間として扱う
  - 例: 23:00 の1時間後は 24.0（翌日0:00）として扱える
- `caffeineAt()` 内の各摂取イベント時刻 `ti` は当日内（0〜24）だが、
  - `tHours` が 0未満 / 24超の領域では、摂取イベントも ±24 で複製して寄与を計算する必要がある
  - 要件: 窓の幅が ±6h なので、**前日分（-24）と翌日分（+24）** の複製があれば十分

## UI changes (minimal)
- `#graphWrap` 内に
  - 中央の縦線要素（SVGの `line` か、絶対配置の `div`）
  - 中央時刻テキスト（絶対配置 `div`）
  - 既存 `x-labels` を動的生成に変更（または `id` を付けてJSで差し替え）

## Update loop
- 現状どおり 1分更新（`setInterval(..., 60_000)`）を継続
- `updateGraph()` は「ログ追加/削除時」＋「定期更新時」どちらでも同じ描画結果になる

## Acceptance criteria
- 画面中央の時刻表示が常に「現在時刻」になっている
- 中央に固定された“いま”基準線があり、折れ線は時間経過で左に流れるように見える
- 24時跨ぎ（23時台〜0時台）でもグラフが不自然に途切れない
- 既存のログ追加/削除が壊れていない

## Open parameters (can be tuned without redesign)
- 窓の幅: ±6h（合計12h）をデフォルト。±4h/±8h への変更は容易
- サンプル点数: 48点（現状踏襲）。滑らかさ優先なら増やせる

