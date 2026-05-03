# caffeine tracker Sliding-window Graph Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `caffeine_tracker/index.html` の折れ線グラフを「中央＝現在時刻」のスライド窓（±6h）に変更し、1分ごとに窓が移動していく見た目にする。

**Architecture:** 既存の `caffeineAt(tHours)`（当日0〜24の時刻）を温存しつつ、表示窓のために `tHours` を連続時間として扱えるラッパー `caffeineAtContinuous(tHours)` を追加してサンプリングする。UIは最小変更で、中央の現在時刻ラベルと“いま”縦線、動的Xラベルを追加する。

**Tech Stack:** Single-file HTML（Vanilla JS + SVG）

---

## File structure / touch points
- Modify: `caffeine_tracker/index.html`
- Create: (none)

---

### Task 1: Add minimal UI hooks (x-label container id, center label)

**Files:**
- Modify: `caffeine_tracker/index.html`

- [ ] **Step 1: Update markup for x-labels to be dynamic**

変更前（固定ラベル）:

```html
<div class="x-labels">
  <span class="x-label">0:00</span>
  <span class="x-label">6:00</span>
  <span class="x-label">12:00</span>
  <span class="x-label">18:00</span>
  <span class="x-label">24:00</span>
</div>
```

変更後（`id` を付けてJSで再生成）:

```html
<div class="x-labels" id="xLabels"></div>
```

- [ ] **Step 2: Add center time overlay element inside `#graphWrap`**

`</svg>` の直後あたり（`x-labels` より上）に追加:

```html
<div id="centerTimeLabel">--:--</div>
```

- [ ] **Step 3: Add CSS for `#centerTimeLabel`**

既存CSSの末尾付近に追加（見た目は最小）:

```css
#centerTimeLabel{
  position:absolute;
  left:50%;
  top:50%;
  transform:translate(-50%,-50%);
  font-size:12px;
  letter-spacing:1px;
  color:#e6edf3;
  background: rgba(13,17,23,0.55);
  border:1px solid rgba(48,54,61,0.7);
  padding:6px 10px;
  border-radius:999px;
  pointer-events:none;
  backdrop-filter: blur(6px);
}
```

- [ ] **Step 4: Commit**

```bash
git add caffeine_tracker/index.html
git commit -m "$(cat <<'EOF'
feat: caffeine-tracker — prepare sliding-window graph UI hooks

EOF
)"
```

---

### Task 2: Implement continuous-time caffeine evaluation (`±24h` duplicates)

**Files:**
- Modify: `caffeine_tracker/index.html`

- [ ] **Step 1: Add helpers for formatting and modulo**

`HALF_LIFE` 近辺（関数群の近く）に追加:

```js
function mod(n, m) {
  return ((n % m) + m) % m;
}

function hoursToHHMM(tHours) {
  const h = Math.floor(mod(tHours, 24));
  const m = Math.floor(mod(tHours, 24) * 60) % 60;
  return String(h).padStart(2, '0') + ':' + String(m).padStart(2, '0');
}
```

- [ ] **Step 2: Add `caffeineAtContinuous(tHours)`**

`caffeineAt(tHours)` の直後に追加:

```js
function caffeineAtContinuous(tHours) {
  // tHours を連続時間（…,-1,0..24,25,…）として扱い、当日イベントを ±24h 複製して寄与を足す
  // 表示窓が ±6h なので、±24 の複製で十分
  return entries.reduce((sum, e) => {
    const ti0 = timeToHours(e.time);
    const tis = [ti0 - 24, ti0, ti0 + 24];
    for (const ti of tis) {
      if (tHours < ti) continue;
      sum += e.mg * Math.pow(2, -(tHours - ti) / HALF_LIFE);
    }
    return sum;
  }, 0);
}
```

- [ ] **Step 3: Quick verification in browser console**

ページを開いて、コンソールで以下を確認:

```js
// entriesが空でも0近辺の値が返る
caffeineAtContinuous(-1)
caffeineAtContinuous(25)
```

期待: `0`（もしくは限りなく0に近い値）でエラーにならない。

- [ ] **Step 4: Commit**

```bash
git add caffeine_tracker/index.html
git commit -m "$(cat <<'EOF'
feat: caffeine-tracker — add continuous-time caffeine evaluation

EOF
)"
```

---

### Task 3: Render sliding-window line/fill paths (±6h around now)

**Files:**
- Modify: `caffeine_tracker/index.html`

- [ ] **Step 1: Introduce window constants**

`updateGraph()` の直前あたりに追加:

```js
const WINDOW_HALF_HOURS = 6;   // ±6h
const WINDOW_SAMPLES    = 48;  // line density (0.25h step over 12h)
```

- [ ] **Step 2: Replace `computePoints()` to be window-based**

既存:

```js
function computePoints() {
  const pts = [];
  for (let i = 0; i <= 48; i++) pts.push(caffeineAt(i * 0.5));
  return pts;
}
```

新規（`nowH` と窓を受け取る）:

```js
function computeWindowPoints(nowH) {
  const start = nowH - WINDOW_HALF_HOURS;
  const end   = nowH + WINDOW_HALF_HOURS;
  const pts = [];
  for (let i = 0; i <= WINDOW_SAMPLES; i++) {
    const t = start + (i / WINDOW_SAMPLES) * (end - start);
    pts.push(caffeineAtContinuous(t));
  }
  return pts;
}
```

- [ ] **Step 3: Update `updateGraph()` to use window points**

`updateGraph()` の先頭付近で `nowH` を先に作る:

```js
  const now  = new Date();
  const nowH = now.getHours() + now.getMinutes() / 60;
  const pts  = computeWindowPoints(nowH);
```

同時に、既存の `toX` が `48` 固定になっているので `WINDOW_SAMPLES` に置き換える:

```js
  const toX = i   => PAD_L + (i / WINDOW_SAMPLES) * gW;
```

Badge更新の `caffeineAt(nowH)` は **window表示とは独立**なので、`caffeineAtContinuous(nowH)` に置換:

```js
  document.getElementById('badgeCurrent').textContent  = Math.round(caffeineAtContinuous(nowH)) + 'mg';
  document.getElementById('badgeMidnight').textContent = Math.round(caffeineAtContinuous(24))   + 'mg';
```

（`24` は当日0:00の意味で現状仕様維持）

- [ ] **Step 4: Commit**

```bash
git add caffeine_tracker/index.html
git commit -m "$(cat <<'EOF'
feat: caffeine-tracker — render sliding window graph around now

EOF
)"
```

---

### Task 4: Add “now” vertical marker + center time text update

**Files:**
- Modify: `caffeine_tracker/index.html`

- [ ] **Step 1: Add an SVG line element for the center marker**

`<path id="graphLine"...>` の後に追加:

```html
<line id="nowLine" x1="250" y1="10" x2="250" y2="152"
      stroke="#e6edf3" stroke-opacity="0.22" stroke-width="1"/>
```

※ `viewBox="0 0 500 170"` 前提で中央 \(x=250\)。`y1/y2` はパディングに合わせて後で調整する。

- [ ] **Step 2: In `updateGraph()`, set `nowLine` Y to match plot area**

`PAD_T`, `PAD_B` を使って:

```js
  const nowLine = document.getElementById('nowLine');
  if (nowLine) {
    const x = PAD_L + gW / 2;
    nowLine.setAttribute('x1', x);
    nowLine.setAttribute('x2', x);
    nowLine.setAttribute('y1', PAD_T);
    nowLine.setAttribute('y2', PAD_T + gH);
  }
```

- [ ] **Step 3: Update `#centerTimeLabel` text each render**

`updateGraph()` 末尾近くで:

```js
  const centerLabel = document.getElementById('centerTimeLabel');
  if (centerLabel) centerLabel.textContent = hoursToHHMM(nowH);
```

- [ ] **Step 4: Commit**

```bash
git add caffeine_tracker/index.html
git commit -m "$(cat <<'EOF'
feat: caffeine-tracker — add now marker and center time label

EOF
)"
```

---

### Task 5: Dynamic X-axis labels for window (now±6/±3/now)

**Files:**
- Modify: `caffeine_tracker/index.html`

- [ ] **Step 1: Add helper to render x labels (safe DOM ops, no innerHTML)**

`updateGraph()` の上あたりに追加:

```js
function renderWindowXLabels(nowH) {
  const el = document.getElementById('xLabels');
  if (!el) return;

  const ticks = [
    nowH - WINDOW_HALF_HOURS,
    nowH - WINDOW_HALF_HOURS / 2,
    nowH,
    nowH + WINDOW_HALF_HOURS / 2,
    nowH + WINDOW_HALF_HOURS
  ];

  while (el.firstChild) el.removeChild(el.firstChild);

  ticks.forEach(t => {
    const span = document.createElement('span');
    span.className = 'x-label';
    span.textContent = hoursToHHMM(t);
    el.appendChild(span);
  });
}
```

- [ ] **Step 2: Call `renderWindowXLabels(nowH)` from `updateGraph()`**

`updateGraph()` の最後の方で:

```js
  renderWindowXLabels(nowH);
```

- [ ] **Step 3: Manual test**

ブラウザで表示し、中央ラベルが現在時刻、左右が±3h/±6hになっていることを確認。
また、23時台〜0時台に跨いでもラベルが `23:xx → 00:xx` のように自然に循環することを確認。

- [ ] **Step 4: Commit**

```bash
git add caffeine_tracker/index.html
git commit -m "$(cat <<'EOF'
feat: caffeine-tracker — dynamic x labels for sliding window

EOF
)"
```

---

### Task 6: Final verification sweep

**Files:**
- Modify: `caffeine_tracker/index.html` (if fixes needed)

- [ ] **Step 1: Smoke test core flows**
  - `+ 追加` でログを追加 → 折れ線が変化する
  - `✕` で削除 → 折れ線が戻る
  - 1分待つ（またはPC時刻を進める） → グラフがスライドして見える

- [ ] **Step 2: Edge cases**
  - `23:50` などの摂取を入れて、0時跨ぎの窓で折れ線が不自然に途切れない
  - entriesが空でもエラーが出ない（グラフが0付近で描画される）

- [ ] **Step 3: Commit (if any small fixes)**

```bash
git add caffeine_tracker/index.html
git commit -m "$(cat <<'EOF'
fix: caffeine-tracker — sliding window graph polish

EOF
)"
```

