# 1日スケジュールプランナー Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** AM/PMの2つのドーナツ円グラフで1日の予定を可視化する単一HTMLファイルのスケジュールプランナーを構築する。

**Architecture:** 単一HTMLファイル（`schedule-planner.html`）にCSS・JS・SVGをすべて収める。SVGでドーナツを描画し、活動データはJSオブジェクト配列で管理、localStorageに永続化する。innerHTML は使わずすべてDOM操作で構築してXSSを防ぐ。

**Tech Stack:** HTML5, CSS3, Vanilla JS, SVG, localStorage

---

## ファイル構成

| ファイル | 役割 |
|---------|------|
| `schedule-planner.html` | 全コード（HTML/CSS/JS）を収める唯一のファイル |

---

## 定数・設計メモ

```
AMドーナツ: 0:00〜12:00（上=0:00、時計回り）
PMドーナツ: 12:00〜24:00（上=12:00、時計回り）
1時間 = 30度（360/12）
3時間ラベル: AM → 0:00, 3:00, 6:00, 9:00 / PM → 12:00, 15:00, 18:00, 21:00
ティックマーク: 1時間おき（1:00, 2:00 など）

SVG viewBox: "0 0 300 300"、中心: (150, 150)
外側半径(R): 120、内側半径(r): 75、ドーナツ幅: 45
ラベル半径(LABEL_R): 142

活動カラーパレット（10色、順番に割り当て）:
["#818cf8","#38bdf8","#34d399","#fbbf24","#f87171",
 "#a78bfa","#22d3ee","#4ade80","#fb923c","#e879f9"]
```

---

### Task 1: HTMLスケルトン + CSS基盤

**Files:**
- Create: `schedule-planner.html`

- [ ] **Step 1: HTMLスケルトンを作成する**

```html
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>1日スケジュールプランナー</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', Meiryo, system-ui, sans-serif;
  background: #0d1117;
  color: #e6e8ed;
  min-height: 100vh;
}

.header {
  background: #0d1117;
  border-bottom: 1px solid #21262d;
  padding: 16px 28px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  text-align: center;
}
.header h1 {
  font-size: 1.3rem;
  letter-spacing: 0.08em;
  background: linear-gradient(90deg, #818cf8, #38bdf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.header p { font-size: 0.82rem; color: #6b7280; }

.app {
  display: flex;
  gap: 20px;
  padding: 20px;
  max-width: 1060px;
  margin: 0 auto;
}

.charts-area {
  display: flex;
  gap: 20px;
  flex: 1;
  justify-content: center;
  align-items: flex-start;
}

.chart-card {
  background: #161b22;
  border: 1px solid #21262d;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.chart-card h2 {
  font-size: 0.9rem;
  color: #8b949e;
  letter-spacing: 0.05em;
}

.sidebar {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-card {
  background: #161b22;
  border: 1px solid #21262d;
  border-radius: 12px;
  padding: 16px;
}
.form-card h3 {
  font-size: 0.85rem;
  color: #8b949e;
  margin-bottom: 12px;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}
.form-group label { font-size: 0.78rem; color: #6b7280; }
.form-group input {
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 6px;
  padding: 8px 10px;
  color: #e6e8ed;
  font-size: 0.85rem;
  width: 100%;
}
.form-group input:focus {
  outline: none;
  border-color: #818cf8;
}

.btn-add {
  width: 100%;
  padding: 8px;
  background: linear-gradient(90deg, #818cf8, #38bdf8);
  border: none;
  border-radius: 6px;
  color: #fff;
  font-size: 0.85rem;
  cursor: pointer;
  font-weight: 600;
}
.btn-add:hover { opacity: 0.85; }

.activity-list { display: flex; flex-direction: column; gap: 6px; }
.activity-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: #0d1117;
  border-radius: 6px;
  font-size: 0.82rem;
}
.activity-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.activity-name { flex: 1; }
.activity-time { font-size: 0.75rem; color: #6b7280; }
.btn-del {
  background: none;
  border: none;
  color: #6b7280;
  cursor: pointer;
  font-size: 0.9rem;
  padding: 0 2px;
  line-height: 1;
}
.btn-del:hover { color: #f87171; }

@media (max-width: 700px) {
  .app { flex-direction: column; }
  .charts-area { flex-direction: column; align-items: center; }
  .sidebar { width: 100%; }
}
</style>
</head>
<body>
<header class="header">
  <h1>1日スケジュールプランナー</h1>
  <p>1日の予定をドーナツグラフで可視化</p>
</header>

<div class="app">
  <div class="charts-area">
    <div class="chart-card">
      <h2>AM（0:00 〜 12:00）</h2>
      <svg id="svg-am" viewBox="0 0 300 300" width="280" height="280"></svg>
    </div>
    <div class="chart-card">
      <h2>PM（12:00 〜 24:00）</h2>
      <svg id="svg-pm" viewBox="0 0 300 300" width="280" height="280"></svg>
    </div>
  </div>

  <div class="sidebar">
    <div class="form-card">
      <h3>活動を追加</h3>
      <div class="form-group">
        <label>活動名</label>
        <input type="text" id="inp-name" placeholder="例: 朝食">
      </div>
      <div class="form-group">
        <label>開始時刻</label>
        <input type="time" id="inp-start" value="09:00">
      </div>
      <div class="form-group">
        <label>終了時刻</label>
        <input type="time" id="inp-end" value="10:00">
      </div>
      <button class="btn-add" id="btn-add">＋ 追加</button>
    </div>

    <div class="form-card">
      <h3>活動リスト</h3>
      <div class="activity-list" id="activity-list"></div>
    </div>
  </div>
</div>

<script>
// TODO: JS（Task 2以降で追加）
</script>
</body>
</html>
```

- [ ] **Step 2: ブラウザで開いてレイアウトを確認する**

`schedule-planner.html` をブラウザで開き、以下を確認:
- ダークモダンなレイアウトが表示されている
- AM/PMの2カラム（SVGは空）
- 右サイドにフォームとリストエリアがある
- スマホ幅（400px）でも縦積みになっている

---

### Task 2: 空のドーナツ基盤を描画する

**Files:**
- Modify: `schedule-planner.html` — `<script>` タグ内

- [ ] **Step 1: 定数と描画ヘルパーを実装する**

`<script>` タグを以下で置き換える:

```js
const CX = 150, CY = 150, R = 120, INNER_R = 75, LABEL_R = 142;
const COLORS = [
  "#818cf8","#38bdf8","#34d399","#fbbf24","#f87171",
  "#a78bfa","#22d3ee","#4ade80","#fb923c","#e879f9"
];

function timeToAngle(totalMinutes, periodStart) {
  const minutes = totalMinutes - periodStart;
  return (minutes / 720) * 360 - 90; // -90で12時位置スタート
}

function polarToXY(angleDeg, radius) {
  const rad = (angleDeg * Math.PI) / 180;
  return { x: CX + radius * Math.cos(rad), y: CY + radius * Math.sin(rad) };
}

function svgEl(tag, attrs) {
  const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  return el;
}

function drawBase(svgId, periodStart) {
  const svg = document.getElementById(svgId);
  svg.textContent = ""; // 安全なクリア（innerHTML不使用）

  // 背景リング
  svg.appendChild(svgEl("circle", {
    cx: CX, cy: CY, r: (R + INNER_R) / 2,
    fill: "none", stroke: "#21262d",
    "stroke-width": R - INNER_R,
  }));
}

drawBase("svg-am", 0);
drawBase("svg-pm", 720);
```

- [ ] **Step 2: ブラウザで確認する**

グレーの空ドーナツが2つ表示されていることを確認する。

---

### Task 3: 時間ラベルとティックマークを描画する

**Files:**
- Modify: `schedule-planner.html` — `drawBase()` 関数を差し替え

- [ ] **Step 1: ティックマークと時間ラベルの描画を追加する**

`drawBase` 関数全体を以下で置き換える:

```js
function drawBase(svgId, periodStart) {
  const svg = document.getElementById(svgId);
  svg.textContent = "";

  // 背景リング
  svg.appendChild(svgEl("circle", {
    cx: CX, cy: CY, r: (R + INNER_R) / 2,
    fill: "none", stroke: "#21262d",
    "stroke-width": R - INNER_R,
  }));

  // 1時間おき: 3時間ごとにラベル、それ以外は点
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
}
```

- [ ] **Step 2: ブラウザで確認する**

- AMドーナツ外周に `0:00`, `3:00`, `6:00`, `9:00` が表示されている
- PMドーナツ外周に `12:00`, `15:00`, `18:00`, `21:00` が表示されている
- 時間ラベルの間に小さい点が表示されている

---

### Task 4: 活動データ管理

**Files:**
- Modify: `schedule-planner.html` — JS追記

- [ ] **Step 1: 活動データ管理の実装を追加する**

定数定義の直後（`drawBase` より前）に追加:

```js
let activities = [];

function timeStrToMin(t) {
  const [h, m] = t.split(":").map(Number);
  return h * 60 + m;
}

function minToTimeStr(min) {
  return `${String(Math.floor(min / 60)).padStart(2, "0")}:${String(min % 60).padStart(2, "0")}`;
}

function addActivity() {
  const nameEl = document.getElementById("inp-name");
  const startEl = document.getElementById("inp-start");
  const endEl = document.getElementById("inp-end");

  const name = nameEl.value.trim();
  if (!name) { alert("活動名を入力してください"); return; }
  if (!startEl.value || !endEl.value) { alert("時刻を入力してください"); return; }

  const startMin = timeStrToMin(startEl.value);
  const endMin = timeStrToMin(endEl.value);
  if (endMin <= startMin) { alert("終了時刻は開始時刻より後にしてください"); return; }

  activities.push({ id: Date.now(), name, startMin, endMin, color: "" });
  reassignColors();
  saveToStorage();
  renderAll();
  nameEl.value = "";
}

function deleteActivity(id) {
  activities = activities.filter(a => a.id !== id);
  reassignColors();
  saveToStorage();
  renderAll();
}

function reassignColors() {
  activities.forEach((a, i) => { a.color = COLORS[i % COLORS.length]; });
}

function saveToStorage() {
  localStorage.setItem("schedule-planner-v1", JSON.stringify(activities));
}

function loadFromStorage() {
  const saved = localStorage.getItem("schedule-planner-v1");
  if (saved) activities = JSON.parse(saved);
}
```

- [ ] **Step 2: `renderAll`・`renderList` スタブを追加する**

```js
function renderAll() {
  renderCharts();
  renderList();
}

function renderCharts() {
  drawBase("svg-am", 0);
  drawBase("svg-pm", 720);
  // セグメント描画はTask 5で実装
}

function renderList() {
  const list = document.getElementById("activity-list");
  list.textContent = "";

  if (activities.length === 0) {
    const p = document.createElement("p");
    p.style.cssText = "font-size:0.8rem;color:#6b7280";
    p.textContent = "まだ活動がありません";
    list.appendChild(p);
    return;
  }

  activities.forEach(a => {
    const item = document.createElement("div");
    item.className = "activity-item";

    const dot = document.createElement("span");
    dot.className = "activity-dot";
    dot.style.background = a.color;

    const nameSpan = document.createElement("span");
    nameSpan.className = "activity-name";
    nameSpan.textContent = a.name; // textContent でXSS防止

    const timeSpan = document.createElement("span");
    timeSpan.className = "activity-time";
    timeSpan.textContent = `${minToTimeStr(a.startMin)}〜${minToTimeStr(a.endMin)}`;

    const delBtn = document.createElement("button");
    delBtn.className = "btn-del";
    delBtn.textContent = "✕";
    delBtn.addEventListener("click", () => deleteActivity(a.id));

    item.append(dot, nameSpan, timeSpan, delBtn);
    list.appendChild(item);
  });
}
```

- [ ] **Step 3: 初期化とイベントリスナーをファイル末尾に追加する**

```js
document.getElementById("btn-add").addEventListener("click", addActivity);
loadFromStorage();
renderAll();
```

- [ ] **Step 4: ブラウザで確認する**

- 活動を追加するとリストに表示される
- ✕ で削除できる
- ページリロード後も活動が残っている

---

### Task 5: ドーナツセグメント描画

**Files:**
- Modify: `schedule-planner.html` — `renderCharts()` を実装

- [ ] **Step 1: セグメント描画関数を実装する**

`renderCharts` 関数を以下で置き換える:

```js
function drawSegments(svg, periodStart, periodEnd) {
  activities.forEach(a => {
    const segStart = Math.max(a.startMin, periodStart);
    const segEnd = Math.min(a.endMin, periodEnd);
    if (segEnd <= segStart) return;

    const startAngle = timeToAngle(segStart, periodStart);
    const endAngle = timeToAngle(segEnd, periodStart);
    const large = endAngle - startAngle > 180 ? 1 : 0;

    const outerStart = polarToXY(startAngle, R);
    const outerEnd = polarToXY(endAngle, R);
    const innerStart = polarToXY(startAngle, INNER_R);
    const innerEnd = polarToXY(endAngle, INNER_R);

    svg.appendChild(svgEl("path", {
      d: `M ${outerStart.x} ${outerStart.y}
          A ${R} ${R} 0 ${large} 1 ${outerEnd.x} ${outerEnd.y}
          L ${innerEnd.x} ${innerEnd.y}
          A ${INNER_R} ${INNER_R} 0 ${large} 0 ${innerStart.x} ${innerStart.y}
          Z`,
      fill: a.color, opacity: "0.9",
    }));
  });
}

function renderCharts() {
  drawBase("svg-am", 0);
  drawBase("svg-pm", 720);
  drawSegments(document.getElementById("svg-am"), 0, 720);
  drawSegments(document.getElementById("svg-pm"), 720, 1440);
}
```

- [ ] **Step 2: ブラウザで確認する**

- 活動を追加するとドーナツにカラーのセグメントが表示される
- AM活動はAMドーナツ、PM活動はPMドーナツに描画される
- 0:00〜12:00をまたぐ活動は両方に描画される

---

### Task 6: セグメント内テキスト表示（小さい場合は非表示）

**Files:**
- Modify: `schedule-planner.html` — `drawSegments()` にテキスト描画を追加

- [ ] **Step 1: テキスト描画ロジックを `drawSegments` 内に追加する**

`svg.appendChild(svgEl("path", {...}));` の直後に追加:

```js
    const arcDeg = endAngle - startAngle;
    if (arcDeg >= 15) { // 約30分未満は非表示
      const midAngle = (startAngle + endAngle) / 2;
      const midPos = polarToXY(midAngle, (R + INNER_R) / 2);
      const label = a.name.length > 6 ? a.name.slice(0, 5) + "…" : a.name;
      const t = svgEl("text", {
        x: midPos.x, y: midPos.y,
        "text-anchor": "middle", "dominant-baseline": "middle",
        fill: "#fff", "font-size": arcDeg >= 30 ? "10" : "8",
        "font-family": "system-ui, sans-serif",
        "pointer-events": "none",
      });
      t.textContent = label; // textContent でXSS防止
      svg.appendChild(t);
    }
```

- [ ] **Step 2: ブラウザで確認する**

- 長い活動（1時間以上）はセグメント内に名前が表示される
- 短い活動（30分未満）はテキストが表示されない
- 6文字超は省略される

---

### Task 7: 空状態の中心テキストと最終確認

**Files:**
- Modify: `schedule-planner.html` — `drawBase()` 末尾に追加

- [ ] **Step 1: 空状態の中心テキストを追加する**

`drawBase` 関数の末尾（`for` ループの後）に追加:

```js
  const hasSeg = activities.some(a =>
    periodStart === 0 ? a.startMin < 720 : a.endMin > 720
  );
  if (!hasSeg) {
    const hint = svgEl("text", {
      x: CX, y: CY,
      "text-anchor": "middle", "dominant-baseline": "middle",
      fill: "#30363d", "font-size": "11",
      "font-family": "system-ui, sans-serif",
    });
    hint.textContent = "活動を追加してね";
    svg.appendChild(hint);
  }
```

- [ ] **Step 2: ブラウザで最終確認する**

以下をすべて確認:
- 初期状態でドーナツ中心に「活動を追加してね」が表示される
- 活動追加・削除でドーナツがリアルタイム更新される
- リロード後も活動が復元される
- スマホ幅（400px）でレイアウトが崩れていない
- AMをまたぐ活動が両ドーナツに正しく描画される

- [ ] **Step 3: コミットする**

```bash
git add schedule-planner.html docs/superpowers/plans/2026-04-20-schedule-planner.md
git commit -m "feat: 1日スケジュールプランナー初回実装"
```
