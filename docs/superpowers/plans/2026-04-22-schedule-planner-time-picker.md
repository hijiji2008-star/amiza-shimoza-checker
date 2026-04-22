# スケジュールプランナー グラフタップ式時刻入力 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `schedule-planner.html` のドーナツグラフをクリック/タップして開始・終了時刻を30分スナップで設定できるようにする。

**Architecture:** 単一HTMLファイル内のVanilla JS。AM/PMそれぞれのSVGに独立した `tapStateAM` / `tapStatePM` を持ち、`mousemove`/`touchmove` でホバーインジケーターを描画、`click`/`touchend` で2タップ式の時刻確定を行う。確定した時刻はサイドバーの既存フォームに自動入力する。

**Tech Stack:** Vanilla JS, SVG DOM API, HTML5 touch events（ビルドツールなし・単一HTMLファイル）

---

## ファイル構成

| ファイル | 変更内容 |
|---------|---------|
| `schedule-planner.html` | グローバル状態追加、ユーティリティ追加、描画関数追加、イベントリスナー追加、CSS追加 |

---

### Task 1: tapState変数とSVG座標ユーティリティを追加

**Files:**
- Modify: `schedule-planner.html`

- [ ] **Step 1: tapState と hoverMin のグローバル変数を追加**

`let activities = [];` の直後に追加する：

```javascript
let tapStateAM = null; // null | { startMin: number }
let tapStatePM = null;
let hoverMinAM = null;
let hoverMinPM = null;
```

- [ ] **Step 2: SVG座標取得関数 getSVGCoords を追加**

`function timeStrToMin(t)` の直前に追加する：

```javascript
function getSVGCoords(svg, event) {
  const rect = svg.getBoundingClientRect();
  const scaleX = 300 / rect.width;
  const scaleY = 300 / rect.height;
  const src = event.touches ? event.touches[0] : event;
  return {
    x: (src.clientX - rect.left) * scaleX,
    y: (src.clientY - rect.top) * scaleY,
  };
}
```

- [ ] **Step 3: リング判定・角度→時刻変換関数 xyToMin を追加**

`getSVGCoords` の直後に追加する：

```javascript
function xyToMin(x, y, periodStart) {
  const dx = x - CX, dy = y - CY;
  const dist = Math.sqrt(dx * dx + dy * dy);
  if (dist < INNER_R - 10 || dist > R + 10) return null;
  let deg = Math.atan2(dy, dx) * 180 / Math.PI + 90;
  if (deg < 0) deg += 360;
  const raw = periodStart + (deg / 360) * 720;
  const snapped = Math.round(raw / 30) * 30;
  return Math.min(Math.max(snapped, periodStart), periodStart + 720);
}
```

- [ ] **Step 4: ブラウザで動作確認**

`schedule-planner.html` をブラウザで開き、コンソール（F12）にエラーが出ないことを確認する。既存の活動追加・表示が壊れていないことを確認する。

- [ ] **Step 5: コミット**

```bash
git add schedule-planner.html
git commit -m "feat: tapState変数とSVG座標ユーティリティを追加"
```

---

### Task 2: drawTapIndicator 描画関数を追加

**Files:**
- Modify: `schedule-planner.html`

- [ ] **Step 1: drawTapIndicator を追加**

`function drawSeg(svg, a, actStart, actEnd, periodStart, periodEnd)` の直前に追加する：

```javascript
function drawTapIndicator(svg, tapState, hoverMin, periodStart) {
  if (hoverMin === null) return;
  const hoverAngle = timeToAngle(hoverMin, periodStart);

  if (tapState) {
    const startAngle = timeToAngle(tapState.startMin, periodStart);

    // ゴースト弧: hoverMin > startMin のときだけ描画
    if (hoverMin > tapState.startMin) {
      const span = (hoverAngle - startAngle + 360) % 360;
      const large = span > 180 ? 1 : 0;
      const oS = polarToXY(startAngle, R);
      const oE = polarToXY(hoverAngle, R);
      const iS = polarToXY(startAngle, INNER_R);
      const iE = polarToXY(hoverAngle, INNER_R);
      svg.appendChild(svgEl("path", {
        d: `M ${oS.x} ${oS.y} A ${R} ${R} 0 ${large} 1 ${oE.x} ${oE.y}` +
           ` L ${iE.x} ${iE.y} A ${INNER_R} ${INNER_R} 0 ${large} 0 ${iS.x} ${iS.y} Z`,
        fill: "#818cf8", opacity: "0.3",
      }));
    }

    // START点（青）
    const sp = polarToXY(startAngle, (R + INNER_R) / 2);
    svg.appendChild(svgEl("circle", {
      cx: sp.x, cy: sp.y, r: "7", fill: "#38bdf8",
      stroke: "#0d1117", "stroke-width": "2",
    }));
    const st = svgEl("text", {
      x: sp.x, y: sp.y, "text-anchor": "middle", "dominant-baseline": "middle",
      fill: "#0d1117", "font-size": "7", "font-family": "system-ui", "pointer-events": "none",
    });
    st.textContent = "S";
    svg.appendChild(st);
  }

  // ホバードット（tapStateなし=白、あり=緑）
  const hp = polarToXY(hoverAngle, (R + INNER_R) / 2);
  svg.appendChild(svgEl("circle", {
    cx: hp.x, cy: hp.y, r: "6",
    fill: tapState ? "#34d399" : "#fff", opacity: "0.85",
    stroke: "#0d1117", "stroke-width": "1.5",
  }));
}
```

- [ ] **Step 2: コミット**

```bash
git add schedule-planner.html
git commit -m "feat: drawTapIndicator描画関数を追加"
```

---

### Task 3: drawBase() と renderCharts() を更新

**Files:**
- Modify: `schedule-planner.html`

- [ ] **Step 1: drawBase() のシグネチャと中央ヒントを更新**

既存の `function drawBase(svgId, periodStart)` を以下に置き換える：

```javascript
function drawBase(svgId, periodStart, tapState) {
  const svg = document.getElementById(svgId);
  svg.textContent = "";

  svg.appendChild(svgEl("circle", {
    cx: CX, cy: CY, r: (R + INNER_R) / 2,
    fill: "none", stroke: "#21262d",
    "stroke-width": R - INNER_R,
  }));

  for (let h = 0; h < 12; h++) {
    const angleDeg = (h / 12) * 360 - 90;

    if (h % 3 === 0) {
      const pos = polarToXY(angleDeg, LABEL_R);
      const hourVal = (Math.floor(periodStart / 60) + h) % 24;
      const text = svgEl("text", {
        x: pos.x, y: pos.y,
        "text-anchor": "middle", "dominant-baseline": "middle",
        fill: "#6b7280", "font-size": "10",
        "font-family": "system-ui, sans-serif",
      });
      text.textContent = `${hourVal}:00`;
      svg.appendChild(text);
    } else {
      const pos = polarToXY(angleDeg, R + 6);
      svg.appendChild(svgEl("circle", { cx: pos.x, cy: pos.y, r: "2", fill: "#30363d" }));
    }
  }

  const hasSeg = activities.some(a => {
    if (a.endMin < a.startMin) return true;
    return periodStart === 0 ? a.startMin < 720 : a.endMin > 720;
  });

  if (tapState) {
    const hint = svgEl("text", {
      x: CX, y: CY,
      "text-anchor": "middle", "dominant-baseline": "middle",
      fill: "#818cf8", "font-size": "10",
      "font-family": "system-ui, sans-serif",
    });
    hint.textContent = `${minToTimeStr(tapState.startMin)} → ?`;
    svg.appendChild(hint);
  } else if (!hasSeg) {
    const hint = svgEl("text", {
      x: CX, y: CY,
      "text-anchor": "middle", "dominant-baseline": "middle",
      fill: "#30363d", "font-size": "10",
      "font-family": "system-ui, sans-serif",
    });
    hint.textContent = "リングをタップ";
    svg.appendChild(hint);
  }
}
```

- [ ] **Step 2: renderCharts() を更新してインジケーターを組み込む**

既存の `function renderCharts()` を以下に置き換える：

```javascript
function renderCharts() {
  drawBase("svg-am", 0, tapStateAM);
  drawBase("svg-pm", 720, tapStatePM);
  drawSegments(document.getElementById("svg-am"), 0, 720);
  drawSegments(document.getElementById("svg-pm"), 720, 1440);
  drawTapIndicator(document.getElementById("svg-am"), tapStateAM, hoverMinAM, 0);
  drawTapIndicator(document.getElementById("svg-pm"), tapStatePM, hoverMinPM, 720);
}
```

- [ ] **Step 3: ブラウザで動作確認**

ブラウザをリロードし、AM/PMグラフが正常に表示されることを確認する。中央に「リングをタップ」と表示されることを確認する（活動が0件のとき）。コンソールエラーなし。

- [ ] **Step 4: コミット**

```bash
git add schedule-planner.html
git commit -m "feat: drawBaseとrenderChartsをtapState対応に更新"
```

---

### Task 4: hover イベントリスナーを追加

**Files:**
- Modify: `schedule-planner.html`

- [ ] **Step 1: setupHover 関数とその呼び出しを追加**

`document.getElementById("btn-add").addEventListener("click", addActivity);` の直前に追加する：

```javascript
function setupHover(svgId, periodStart, setHoverMin) {
  const svg = document.getElementById(svgId);

  svg.addEventListener("mousemove", e => {
    const { x, y } = getSVGCoords(svg, e);
    setHoverMin(xyToMin(x, y, periodStart));
    renderCharts();
  });

  svg.addEventListener("mouseleave", () => {
    setHoverMin(null);
    renderCharts();
  });

  svg.addEventListener("touchmove", e => {
    e.preventDefault();
    const { x, y } = getSVGCoords(svg, e);
    setHoverMin(xyToMin(x, y, periodStart));
    renderCharts();
  }, { passive: false });
}

setupHover("svg-am", 0,   v => { hoverMinAM = v; });
setupHover("svg-pm", 720, v => { hoverMinPM = v; });
```

- [ ] **Step 2: ブラウザで動作確認**

AMグラフのリング上にマウスを乗せると白いドットが表示され、30分刻みでスナップしながら動くことを確認する。リング外に出るとドットが消えることを確認する。

- [ ] **Step 3: コミット**

```bash
git add schedule-planner.html
git commit -m "feat: グラフホバーインジケーターを実装"
```

---

### Task 5: tap/click イベントリスナーを追加

**Files:**
- Modify: `schedule-planner.html`

- [ ] **Step 1: handleTap と setupTap を追加**

`setupHover("svg-pm", ...)` の呼び出しの直後に追加する：

```javascript
function handleTap(min, periodStart) {
  const isAM = periodStart === 0;
  const tapState = isAM ? tapStateAM : tapStatePM;

  if (min === null) {
    // リング外タップ → リセット
    if (isAM) { tapStateAM = null; hoverMinAM = null; }
    else       { tapStatePM = null; hoverMinPM = null; }
    return;
  }

  if (tapState === null) {
    // 1回目タップ: START確定
    if (isAM) tapStateAM = { startMin: min };
    else      tapStatePM = { startMin: min };
  } else {
    const startMin = tapState.startMin;
    if (min <= startMin) {
      // END <= START → リセット
      if (isAM) tapStateAM = null;
      else      tapStatePM = null;
    } else {
      // 2回目タップ: END確定 → フォームに自動入力
      document.getElementById("inp-start").value = minToTimeStr(startMin);
      document.getElementById("inp-end").value   = minToTimeStr(min);
      document.getElementById("inp-name").focus();
      if (isAM) { tapStateAM = null; hoverMinAM = null; }
      else       { tapStatePM = null; hoverMinPM = null; }
    }
  }
}

function setupTap(svgId, periodStart) {
  const svg = document.getElementById(svgId);
  const isAM = periodStart === 0;

  svg.addEventListener("click", e => {
    const { x, y } = getSVGCoords(svg, e);
    handleTap(xyToMin(x, y, periodStart), periodStart);
    renderCharts();
  });

  svg.addEventListener("touchend", e => {
    e.preventDefault();
    const touch = e.changedTouches[0];
    const rect = svg.getBoundingClientRect();
    const x = (touch.clientX - rect.left) * (300 / rect.width);
    const y = (touch.clientY - rect.top)  * (300 / rect.height);
    if (isAM) hoverMinAM = null; else hoverMinPM = null;
    handleTap(xyToMin(x, y, periodStart), periodStart);
    renderCharts();
  }, { passive: false });
}

setupTap("svg-am", 0);
setupTap("svg-pm", 720);
```

- [ ] **Step 2: ブラウザで動作確認（デスクトップ）**

1. AMグラフのリングを1回クリックする → 青い「S」ドットが表示され、中央に「HH:MM → ?」が出ることを確認する
2. リング上をマウスで動かすと、ゴースト弧が伸び縮みすることを確認する
3. 2回目クリックで時刻フォームに自動入力され、活動名フィールドにフォーカスが移ることを確認する
4. リング外をクリックするとSTARTがリセットされることを確認する

- [ ] **Step 3: END ≤ START のエッジケース確認**

1. リングの12時位置（0:00）をクリックしてSTARTをセットする
2. 同じ位置をもう一度クリックする → tapStateがリセットされ「S」ドットが消えることを確認する

- [ ] **Step 4: コミット**

```bash
git add schedule-planner.html
git commit -m "feat: 2タップ式時刻確定とサイドバー自動入力を実装"
```

---

### Task 6: ESCキーリセットとCSSカーソルを追加

**Files:**
- Modify: `schedule-planner.html`

- [ ] **Step 1: ESCキーイベントリスナーを追加**

`setupTap("svg-pm", 720);` の直後に追加する：

```javascript
document.addEventListener("keydown", e => {
  if (e.key !== "Escape") return;
  tapStateAM = null; tapStatePM = null;
  hoverMinAM = null; hoverMinPM = null;
  renderCharts();
});
```

- [ ] **Step 2: SVGにcrosshairカーソルを追加**

`</style>` の直前のCSSブロックに追加する：

```css
#svg-am, #svg-pm { cursor: crosshair; }
```

- [ ] **Step 3: ブラウザで動作確認**

1. STARTを1クリックして確定する
2. ESCキーを押す → 「S」ドットが消え tapState がリセットされることを確認する
3. グラフ上でカーソルが十字（crosshair）になっていることを確認する

- [ ] **Step 4: コミット**

```bash
git add schedule-planner.html
git commit -m "feat: ESCキーリセットとcrosshairカーソルを追加"
```

---

### Task 7: エンドツーエンド動作確認

- [ ] **Step 1: フルフロー確認（デスクトップ）**

1. `schedule-planner.html` をブラウザで開く
2. AMグラフのリングをクリック（例: 9:00付近）→ 青いS点が9:00に表示されることを確認
3. リング上をマウスで動かし、ゴースト弧が追従することを確認
4. 11:00付近をクリック → `inp-start=09:00`, `inp-end=11:00` が自動入力されることを確認
5. 活動名を入力して「追加」ボタンを押す → グラフにセグメントが表示されることを確認
6. PMグラフも同様に動作することを確認
7. ページをリロードして活動がローカルストレージから復元されることを確認

- [ ] **Step 2: 既存機能の非破壊確認**

1. サイドバーフォームの時刻input（`inp-start`, `inp-end`）に直接入力して追加できることを確認
2. 活動リストの削除ボタンが動作することを確認
3. 日またぎ活動（例: 22:00〜06:00）を手動入力で追加し、AM/PM両グラフに表示されることを確認

- [ ] **Step 3: コミット（変更があれば）**

```bash
git add schedule-planner.html
git commit -m "fix: エンドツーエンド確認後の修正"
```
