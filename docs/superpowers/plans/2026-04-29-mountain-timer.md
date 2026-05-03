# Mountain Timer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 登山×天気変化カウントダウンタイマーを単一HTMLファイルで実装する。

**Architecture:** 単一HTMLファイル（mountain_timer/index.html）にCSS・JSをすべてインライン。SVGシーンをJSで毎秒更新し、経過%に応じて空色・雨・虹・太陽・ハイカー位置を補間する。雨アニメは requestAnimationFrame で独立ループ、タイマーは setInterval で動作。

**Tech Stack:** HTML5 / CSS3 / Vanilla JS / SVG / Web Audio API

---

## 座標・定数リファレンス（全タスク共通）

```
SVG viewBox: 0 0 480 300
START  = { x: 30,  y: 265 }   // 左裾（出発点）
PEAK   = { x: 240, y: 30  }   // 頂上
END    = { x: 450, y: 265 }   // 右裾（ゴール）
```

天気補間キーフレーム（経過率 pct = 0.0〜1.0）:

| pct | 空上色 | 空下色 | 雨密度 | 虹opacity | 雲opacity |
|-----|--------|--------|--------|-----------|-----------|
| 0.0 | #1a2535 | #2d3f52 | 1.0 | 0.0 | 1.0 |
| 0.4 | #1e3a5a | #3d6080 | 0.2 | 0.0 | 0.5 |
| 0.5 | #1e6baa | #a8d8f0 | 0.0 | 1.0 | 0.0 |
| 0.6 | #1a5a90 | #7ec8e3 | 0.0 | 0.0 | 0.0 |
| 0.8 | #7c3000 | #f97316 | 0.0 | 0.0 | 0.0 |
| 1.0 | #0f1a35 | #1a0800 | 0.0 | 0.0 | 0.0 |

太陽キーフレーム:

| pct | cx | cy | opacity |
|-----|----|----|---------|
| 0.45 | 380 | 45 | 0.0 |
| 0.50 | 370 | 45 | 1.0 |
| 0.80 | 280 | 140 | 1.0 |
| 1.00 | 200 | 175 | 0.0 |

---

## Task 1: プロジェクト作成・HTMLスケルトン

**Files:**
- Create: `mountain_timer/index.html`

- [ ] **Step 1: ディレクトリ作成**

```bash
mkdir -p /Users/obatatsunari/projects/mountain_timer
```

- [ ] **Step 2: index.html を作成する**

以下の内容で `mountain_timer/index.html` を作成する。SVG内の要素は後続タスクで追加するため、ここでは空の `<g>` とプレースホルダーIDを持つ要素を置く。

```html
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mountain Timer</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #0d1117;
    color: white;
    font-family: 'Segoe UI', sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    gap: 16px;
    padding: 20px;
  }

  #scene {
    width: 520px;
    max-width: 100%;
    border-radius: 16px;
    overflow: hidden;
    display: block;
  }

  #timeDisplay {
    font-size: 52px;
    font-weight: 700;
    font-family: 'Courier New', monospace;
    background: linear-gradient(135deg, #f59e0b, #ef4444);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 4px;
  }

  #phaseLabel {
    font-size: 13px;
    color: #94a3b8;
    letter-spacing: 1px;
    min-height: 20px;
  }

  .presets {
    display: flex;
    gap: 8px;
  }
  .preset-btn {
    padding: 6px 16px;
    background: #1e2a3a;
    color: #94a3b8;
    border: 1px solid #2d3748;
    border-radius: 6px;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.15s;
  }
  .preset-btn:hover { background: #2d3748; color: white; }
  .preset-btn.active { background: #f59e0b; color: #0d1117; border-color: #f59e0b; font-weight: 700; }

  .controls {
    display: flex;
    gap: 10px;
    align-items: center;
  }
  select {
    background: #161b22;
    color: #94a3b8;
    border: 1px solid #2d3748;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 14px;
  }
  button {
    padding: 10px 24px;
    border: none;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }
  #startBtn {
    background: linear-gradient(135deg, #f59e0b, #ef4444);
    color: white;
  }
  #startBtn:hover { opacity: 0.85; }
  #resetBtn {
    background: #1e2a3a;
    color: #94a3b8;
    border: 1px solid #2d3748;
  }
  #resetBtn:hover { background: #2d3748; }

  .progress-wrap {
    width: 480px;
    max-width: 100%;
    height: 4px;
    background: #1e293b;
    border-radius: 2px;
    overflow: hidden;
  }
  #progressBar {
    height: 100%;
    width: 0%;
    background: #f59e0b;
    border-radius: 2px;
    transition: width 0.5s linear;
  }
</style>
</head>
<body>

<svg id="scene" viewBox="0 0 480 300" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
      <stop id="skyTop"    offset="0%"   stop-color="#1a2535"/>
      <stop id="skyBottom" offset="100%" stop-color="#2d3f52"/>
    </linearGradient>
    <linearGradient id="mtMainGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#6b4226"/>
      <stop offset="100%" stop-color="#2d1f12"/>
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="3" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>

  <!-- 空 -->
  <rect id="skyRect" width="480" height="300" fill="url(#skyGrad)"/>

  <!-- 太陽 -->
  <g id="sunGroup" opacity="0">
    <circle id="sunGlow" cx="380" cy="45" r="40" fill="#fde68a" opacity="0.3"/>
    <circle id="sunCore" cx="380" cy="45" r="18" fill="#fdd835"/>
  </g>

  <!-- 雨雲 -->
  <g id="rainClouds" opacity="1">
    <ellipse cx="75"  cy="35" rx="48" ry="18" fill="#374151"/>
    <ellipse cx="108" cy="26" rx="38" ry="16" fill="#4b5563"/>
    <ellipse cx="44"  cy="30" rx="30" ry="14" fill="#374151"/>
    <ellipse cx="210" cy="32" rx="52" ry="18" fill="#374151"/>
    <ellipse cx="248" cy="22" rx="40" ry="16" fill="#4b5563"/>
    <ellipse cx="340" cy="30" rx="46" ry="17" fill="#374151"/>
    <ellipse cx="375" cy="20" rx="34" ry="14" fill="#4b5563"/>
  </g>

  <!-- 虹 -->
  <g id="rainbowGroup" opacity="0">
    <path d="M 5,210 A 235,235 0 0 1 475,210" fill="none" stroke="#ef4444" stroke-width="5" opacity="0.5"/>
    <path d="M 14,210 A 226,226 0 0 1 466,210" fill="none" stroke="#f97316" stroke-width="5" opacity="0.5"/>
    <path d="M 23,210 A 217,217 0 0 1 457,210" fill="none" stroke="#eab308" stroke-width="5" opacity="0.5"/>
    <path d="M 32,210 A 208,208 0 0 1 448,210" fill="none" stroke="#22c55e" stroke-width="5" opacity="0.5"/>
    <path d="M 41,210 A 199,199 0 0 1 439,210" fill="none" stroke="#3b82f6" stroke-width="5" opacity="0.5"/>
    <path d="M 50,210 A 190,190 0 0 1 430,210" fill="none" stroke="#8b5cf6" stroke-width="5" opacity="0.5"/>
  </g>

  <!-- 雨粒レイヤー（JS生成） -->
  <g id="rainLayer"></g>

  <!-- 遠景の山 -->
  <polygon points="0,230 110,95 220,230"  fill="#1a2a3a" opacity="0.7"/>
  <polygon points="260,230 380,80 500,230" fill="#152030" opacity="0.7"/>

  <!-- メイン山 -->
  <polygon points="30,270 240,30 450,270" fill="url(#mtMainGrad)"/>
  <polygon points="30,270 240,30 240,270" fill="#000" opacity="0.1"/>

  <!-- 木々（左） -->
  <g fill="#1e4416">
    <polygon points="42,252 54,226 66,252"/>
    <polygon points="60,256 74,228 88,256"/>
    <polygon points="78,254 92,230 106,254"/>
  </g>
  <!-- 木々（右） -->
  <g fill="#1e4416">
    <polygon points="374,252 386,226 398,252"/>
    <polygon points="392,256 406,228 420,256"/>
    <polygon points="410,254 424,230 438,254"/>
  </g>

  <!-- 地面 -->
  <rect x="0" y="266" width="480" height="34" fill="#0f1f0a"/>
  <rect x="0" y="274" width="480" height="26" fill="#0a160a"/>

  <!-- 足跡 -->
  <polyline id="trail" points="" fill="none" stroke="#f59e0b"
            stroke-width="1.5" stroke-dasharray="4 5" opacity="0.6"/>

  <!-- 頂上フラグ -->
  <line x1="240" y1="30" x2="240" y2="10" stroke="#cbd5e1" stroke-width="1.8"/>
  <polygon points="240,10 257,18 240,26" fill="#ef4444"/>

  <!-- ハイカー -->
  <g id="hiker" transform="translate(30,265)">
    <ellipse id="hHatBrim" cx="0" cy="-30" rx="6"  ry="2.5" fill="#92400e"/>
    <rect    id="hHatTop"  x="-4" y="-36" width="8" height="7" rx="2" fill="#b45309"/>
    <circle  id="hHead"    cy="-25" r="5" fill="#fcd34d"/>
    <line id="hBody"  x1="0"  y1="-20" x2="0"  y2="-9"  stroke="#3b82f6" stroke-width="3"   stroke-linecap="round"/>
    <line id="hArmL"  x1="-2" y1="-17" x2="-7" y2="-11" stroke="#3b82f6" stroke-width="2"   stroke-linecap="round"/>
    <line id="hArmR"  x1="2"  y1="-17" x2="7"  y2="-11" stroke="#3b82f6" stroke-width="2"   stroke-linecap="round"/>
    <line id="hLegL"  x1="-2" y1="-9"  x2="-5" y2="0"   stroke="#1e3a5f" stroke-width="2"   stroke-linecap="round"/>
    <line id="hLegR"  x1="2"  y1="-9"  x2="5"  y2="0"   stroke="#1e3a5f" stroke-width="2"   stroke-linecap="round"/>
    <line id="hStick" x1="8"  y1="-15" x2="13" y2="2"   stroke="#94a3b8" stroke-width="1.5" stroke-linecap="round"/>
  </g>

  <!-- 進捗バー（SVG内下部） -->
  <rect x="48" y="288" width="384" height="4" rx="2" fill="#1e293b"/>
  <rect id="svgProgress" x="48" y="288" width="0" height="4" rx="2" fill="#f59e0b"/>
</svg>

<div id="timeDisplay">00:00</div>
<div id="phaseLabel"></div>

<div class="presets">
  <button class="preset-btn" data-min="5"  data-sec="0">5分</button>
  <button class="preset-btn" data-min="10" data-sec="0">10分</button>
  <button class="preset-btn" data-min="15" data-sec="0">15分</button>
  <button class="preset-btn" data-min="20" data-sec="0">20分</button>
</div>

<div class="controls">
  <select id="minSel"></select>
  <select id="secSel">
    <option value="0">00秒</option>
    <option value="15">15秒</option>
    <option value="30">30秒</option>
    <option value="45">45秒</option>
  </select>
  <button id="startBtn">▶ スタート</button>
  <button id="resetBtn">↺ リセット</button>
</div>

<script>
// ── 定数 ────────────────────────────────────────────────
const START = { x: 30,  y: 265 };
const PEAK  = { x: 240, y: 30  };
const END   = { x: 450, y: 265 };
const RAIN_MAX = 60;

// ── タイマー状態 ─────────────────────────────────────────
let totalSeconds = 300;
let remaining    = 300;
let interval     = null;
let walkFrame    = 0;
let trailPts     = [];
let rainDrops    = [];
let animFrameId  = null;

// ── DOM参照 ──────────────────────────────────────────────
const timeDisplay  = document.getElementById('timeDisplay');
const phaseLabel   = document.getElementById('phaseLabel');
const startBtn     = document.getElementById('startBtn');
const resetBtn     = document.getElementById('resetBtn');
const minSel       = document.getElementById('minSel');
const secSel       = document.getElementById('secSel');
const svgProgress  = document.getElementById('svgProgress');
const hikerEl      = document.getElementById('hiker');
const trailEl      = document.getElementById('trail');
const rainLayer    = document.getElementById('rainLayer');
const rainClouds   = document.getElementById('rainClouds');
const rainbowGroup = document.getElementById('rainbowGroup');
const sunGroup     = document.getElementById('sunGroup');
const sunGlowEl    = document.getElementById('sunGlow');
const sunCoreEl    = document.getElementById('sunCore');
const skyTopEl     = document.getElementById('skyTop');
const skyBottomEl  = document.getElementById('skyBottom');
const hArmL  = document.getElementById('hArmL');
const hArmR  = document.getElementById('hArmR');
const hLegL  = document.getElementById('hLegL');
const hLegR  = document.getElementById('hLegR');

// ── 分プルダウン生成 ─────────────────────────────────────
(function buildMinSel() {
  for (let i = 0; i <= 99; i++) {
    const opt = document.createElement('option');
    opt.value = i;
    opt.textContent = i + '分';
    if (i === 5) opt.selected = true;
    minSel.appendChild(opt);
  }
})();

// ── ユーティリティ ───────────────────────────────────────
function lerp(a, b, t) { return a + (b - a) * t; }

function hexToRgb(hex) {
  return [
    parseInt(hex.slice(1, 3), 16),
    parseInt(hex.slice(3, 5), 16),
    parseInt(hex.slice(5, 7), 16)
  ];
}

function lerpColor(a, b, t) {
  const [ar, ag, ab] = hexToRgb(a);
  const [br, bg, bb] = hexToRgb(b);
  const r = Math.round(lerp(ar, br, t));
  const g = Math.round(lerp(ag, bg, t));
  const bv = Math.round(lerp(ab, bb, t));
  return '#' + [r, g, bv].map(v => v.toString(16).padStart(2, '0')).join('');
}

// keyframes: [{at:0,val:...}, ...] — val は数値 or 16進色文字列
function kfLerp(kf, pct) {
  for (let i = 0; i < kf.length - 1; i++) {
    const k0 = kf[i], k1 = kf[i + 1];
    if (pct >= k0.at && pct <= k1.at) {
      const t = (k1.at === k0.at) ? 1 : (pct - k0.at) / (k1.at - k0.at);
      return (typeof k0.val === 'string')
        ? lerpColor(k0.val, k1.val, t)
        : lerp(k0.val, k1.val, t);
    }
  }
  return kf[kf.length - 1].val;
}

function formatTime(s) {
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return String(m).padStart(2, '0') + ':' + String(sec).padStart(2, '0');
}

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

// ── ハイカー位置 ─────────────────────────────────────────
function getHikerPos(pct) {
  if (pct <= 0.5) {
    const t = pct * 2;
    return { x: lerp(START.x, PEAK.x, t), y: lerp(START.y, PEAK.y, t) };
  }
  const t = (pct - 0.5) * 2;
  return { x: lerp(PEAK.x, END.x, t), y: lerp(PEAK.y, END.y, t) };
}

function updateHiker(pct) {
  const pos = getHikerPos(pct);
  hikerEl.setAttribute('transform', `translate(${pos.x},${pos.y})`);
  trailPts.push(pos.x + ',' + pos.y);
  trailEl.setAttribute('points', trailPts.join(' '));

  const atPeak = pct >= 0.48 && pct <= 0.52;
  if (atPeak) {
    // バンザイポーズ
    hArmL.setAttribute('x2', '-12'); hArmL.setAttribute('y2', '-26');
    hArmR.setAttribute('x2',  '12'); hArmR.setAttribute('y2', '-26');
    hLegL.setAttribute('x2', '-3');  hLegL.setAttribute('y2', '0');
    hLegR.setAttribute('x2',  '3');  hLegR.setAttribute('y2', '0');
  } else {
    walkFrame++;
    const s = Math.sin(walkFrame * 0.5) * 5;
    hArmL.setAttribute('x2', String(-7 + s * 0.5));  hArmL.setAttribute('y2', '-11');
    hArmR.setAttribute('x2', String( 7 - s * 0.5));  hArmR.setAttribute('y2', '-11');
    hLegL.setAttribute('x2', String(-5 + s * 0.4));  hLegL.setAttribute('y2', '0');
    hLegR.setAttribute('x2', String( 5 - s * 0.4));  hLegR.setAttribute('y2', '0');
  }
}

// ── 天気補間キーフレーム ─────────────────────────────────
const KF_SKY_TOP = [
  { at: 0.0, val: '#1a2535' },
  { at: 0.4, val: '#1e3a5a' },
  { at: 0.5, val: '#1e6baa' },
  { at: 0.6, val: '#1a5a90' },
  { at: 0.8, val: '#7c3000' },
  { at: 1.0, val: '#0f1a35' }
];
const KF_SKY_BTM = [
  { at: 0.0, val: '#2d3f52' },
  { at: 0.4, val: '#3d6080' },
  { at: 0.5, val: '#a8d8f0' },
  { at: 0.6, val: '#7ec8e3' },
  { at: 0.8, val: '#f97316' },
  { at: 1.0, val: '#1a0800' }
];
const KF_RAIN    = [
  { at: 0.0, val: 1.0 }, { at: 0.4, val: 0.2 }, { at: 0.5, val: 0.0 }, { at: 1.0, val: 0.0 }
];
const KF_CLOUD   = [
  { at: 0.0, val: 1.0 }, { at: 0.4, val: 0.5 }, { at: 0.5, val: 0.0 }, { at: 1.0, val: 0.0 }
];
const KF_RAINBOW = [
  { at: 0.0, val: 0.0 }, { at: 0.4, val: 0.0 }, { at: 0.5, val: 1.0 }, { at: 0.6, val: 0.0 }, { at: 1.0, val: 0.0 }
];
const KF_SUN_CX  = [
  { at: 0.45, val: 380 }, { at: 0.50, val: 370 }, { at: 0.80, val: 280 }, { at: 1.00, val: 200 }
];
const KF_SUN_CY  = [
  { at: 0.45, val: 45  }, { at: 0.50, val: 45  }, { at: 0.80, val: 140 }, { at: 1.00, val: 175 }
];
const KF_SUN_OPA = [
  { at: 0.45, val: 0.0 }, { at: 0.50, val: 1.0 }, { at: 0.90, val: 1.0 }, { at: 1.00, val: 0.0 }
];

function applyWeather(pct) {
  // 空
  skyTopEl.setAttribute('stop-color',    kfLerp(KF_SKY_TOP, pct));
  skyBottomEl.setAttribute('stop-color', kfLerp(KF_SKY_BTM, pct));
  // 雲
  rainClouds.setAttribute('opacity', kfLerp(KF_CLOUD, pct));
  // 虹
  rainbowGroup.setAttribute('opacity', kfLerp(KF_RAINBOW, pct));
  // 太陽
  const sunOpa = kfLerp(KF_SUN_OPA, clamp(pct, 0.45, 1.0));
  const sunCx  = kfLerp(KF_SUN_CX,  clamp(pct, 0.45, 1.0));
  const sunCy  = kfLerp(KF_SUN_CY,  clamp(pct, 0.45, 1.0));
  sunGroup.setAttribute('opacity', sunOpa);
  sunGlowEl.setAttribute('cx', sunCx); sunGlowEl.setAttribute('cy', sunCy);
  sunCoreEl.setAttribute('cx', sunCx); sunCoreEl.setAttribute('cy', sunCy);
  // 雨密度は animateRain() が参照するのでグローバル変数に渡す
  currentRainDensity = kfLerp(KF_RAIN, pct);
}

// ── 雨パーティクル ───────────────────────────────────────
let currentRainDensity = 1.0;

function createRain() {
  while (rainLayer.firstChild) rainLayer.removeChild(rainLayer.firstChild);
  rainDrops = [];
  const NS = 'http://www.w3.org/2000/svg';
  for (let i = 0; i < RAIN_MAX; i++) {
    const line = document.createElementNS(NS, 'line');
    line.setAttribute('stroke', '#7dd3fc');
    line.setAttribute('stroke-width', '0.9');
    line.setAttribute('stroke-opacity', '0.55');
    const x = Math.random() * 480;
    const y = Math.random() * 300;
    line.setAttribute('x1', x); line.setAttribute('y1', y);
    line.setAttribute('x2', x - 2); line.setAttribute('y2', y + 12);
    rainLayer.appendChild(line);
    rainDrops.push({ el: line, x, y, speed: 2.5 + Math.random() * 2.5 });
  }
}

function animateRain() {
  const activeCount = Math.floor(RAIN_MAX * currentRainDensity);
  rainDrops.forEach((d, i) => {
    if (i >= activeCount) {
      d.el.setAttribute('visibility', 'hidden');
      return;
    }
    d.el.setAttribute('visibility', 'visible');
    d.y += d.speed;
    if (d.y > 310) { d.y = -12; d.x = Math.random() * 480; }
    d.el.setAttribute('x1', d.x);    d.el.setAttribute('y1', d.y);
    d.el.setAttribute('x2', d.x - 2); d.el.setAttribute('y2', d.y + 12);
  });
  animFrameId = requestAnimationFrame(animateRain);
}

// ── フェーズラベル ───────────────────────────────────────
function updatePhase(pct) {
  if (pct < 0.48)       phaseLabel.textContent = '⛰  登っています...';
  else if (pct <= 0.52) phaseLabel.textContent = '🚩 頂上到達！';
  else                  phaseLabel.textContent = '🏃 下山中...';
}

// ── タイマーコア ─────────────────────────────────────────
function getSetSeconds() {
  return parseInt(minSel.value, 10) * 60 + parseInt(secSel.value, 10);
}

function initTimer() {
  totalSeconds = getSetSeconds() || 300;
  remaining    = totalSeconds;
  walkFrame    = 0;
  trailPts     = [];
  trailEl.setAttribute('points', '');
  timeDisplay.textContent = formatTime(remaining);
  phaseLabel.textContent  = '';
  svgProgress.setAttribute('width', '0');

  // シーンを初期状態（雨）にリセット
  applyWeather(0);
  updateHiker(0);

  // 太陽を初期位置に
  sunGroup.setAttribute('opacity', '0');
}

function tick() {
  remaining = Math.max(0, remaining - 1);
  const elapsed = totalSeconds - remaining;
  const pct = totalSeconds > 0 ? elapsed / totalSeconds : 1;

  timeDisplay.textContent = formatTime(remaining);
  svgProgress.setAttribute('width', String(pct * 384));
  updateHiker(pct);
  applyWeather(pct);
  updatePhase(pct);

  if (remaining <= 0) {
    clearInterval(interval);
    interval = null;
    startBtn.textContent = '▶ スタート';
    phaseLabel.textContent = '';
    playBeep();
  }
}

// ── オーディオ ───────────────────────────────────────────
function playBeep() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain); gain.connect(ctx.destination);
    osc.type = 'sine';
    osc.frequency.setValueAtTime(880, ctx.currentTime);
    gain.gain.setValueAtTime(0.4, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.2);
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + 1.2);
  } catch (e) { /* AudioContext非対応ブラウザでは無視 */ }
}

// ── UIイベント ───────────────────────────────────────────
startBtn.addEventListener('click', () => {
  if (interval) {
    clearInterval(interval);
    interval = null;
    startBtn.textContent = '▶ スタート';
    return;
  }
  if (remaining <= 0) initTimer();
  interval = setInterval(tick, 1000);
  startBtn.textContent = '⏸ 一時停止';
});

resetBtn.addEventListener('click', () => {
  if (interval) { clearInterval(interval); interval = null; }
  startBtn.textContent = '▶ スタート';
  initTimer();
});

document.querySelectorAll('.preset-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    minSel.value = btn.dataset.min;
    secSel.value = btn.dataset.sec;
    if (interval) { clearInterval(interval); interval = null; startBtn.textContent = '▶ スタート'; }
    initTimer();
  });
});

minSel.addEventListener('change', () => {
  document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
  if (interval) { clearInterval(interval); interval = null; startBtn.textContent = '▶ スタート'; }
  initTimer();
});
secSel.addEventListener('change', () => {
  document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
  if (interval) { clearInterval(interval); interval = null; startBtn.textContent = '▶ スタート'; }
  initTimer();
});

// ── 起動 ─────────────────────────────────────────────────
createRain();
animateRain();
// デフォルトで5分をアクティブに
document.querySelector('.preset-btn[data-min="5"]').classList.add('active');
minSel.value = '5';
initTimer();
</script>
</body>
</html>
```

- [ ] **Step 3: ブラウザで開いて動作確認**

`mountain_timer/index.html` をブラウザで開く（Windowsなら `Ctrl+O`）。以下を確認:
- 暗い雨の山シーンが表示される
- 「5分」プリセットがハイライト
- ▶ スタートを押すとカウントダウン開始
- ハイカーが左裾から動き出す
- 雨粒が降り続ける

- [ ] **Step 4: コミット**

```bash
git add mountain_timer/index.html
git commit -m "feat: mountain timer — 初期実装（登山タイマー・天気変化）"
```

---

## Task 2: 動作の最終検証と細部調整

**Files:**
- Modify: `mountain_timer/index.html`

- [ ] **Step 1: 5分タイマーで最初から最後まで通し確認**

`10秒（デモ用）` がないので、分プルダウンを `0分`・秒プルダウンを `15秒` にセットしてスタート。以下を順番に確認:

| 経過% | 確認項目 |
|-------|----------|
| 0〜40% | 雨が降っている、空が暗い、ハイカーが登っている |
| 40〜50% | 雨が弱くなる、空が明るくなる |
| 50%前後 | 虹が出る、ハイカーがバンザイ、太陽が出る |
| 50〜80% | 晴れ、ハイカーが下山 |
| 80〜100% | 夕焼け、太陽が沈む |
| 100% | ビープ音が鳴る |

- [ ] **Step 2: 虹の位置を確認・必要なら調整**

虹の半円弧（`<path d="M 5,210 A 235,235 ...">`）が山にかかるように見えるか確認。山の頂上（PEAK.y=30）付近に虹の頂点が来るのが理想。

もし位置がずれていたら `M 5,210` と `A 235,235` の数値を調整する:

```html
<!-- 虹中心y=210、半径235で試す（頂点=210-235=-25、つまりSVG上部）-->
<!-- 見た目で調整してOK。頂点がだいたいy=-10〜30に来ればよい -->
<path d="M 5,210 A 235,235 0 0 1 475,210" .../>
```

- [ ] **Step 3: 時刻表示の色を天気に合わせる**

夕焼け時（pct > 0.8）は時刻表示をアンバー→オレンジに変化させる。`applyWeather()` に追記:

```javascript
// applyWeather() 内の末尾に追加
if (pct > 0.8) {
  const t = (pct - 0.8) / 0.2;
  timeDisplay.style.background = `linear-gradient(135deg, #f59e0b, #ef4444)`;
} else if (pct > 0.45) {
  timeDisplay.style.background = `linear-gradient(135deg, #fbbf24, #38bdf8)`;
} else {
  timeDisplay.style.background = `linear-gradient(135deg, #f59e0b, #ef4444)`;
}
timeDisplay.style.webkitBackgroundClip = 'text';
timeDisplay.style.webkitTextFillColor  = 'transparent';
```

- [ ] **Step 4: リセット時に太陽・虹・雨が正しく戻ることを確認**

リセットボタンを押したあと:
- 虹: opacity=0
- 太陽: opacity=0
- 雨: 最大密度
- 空: 暗いグレー

問題なければStep 5へ。`applyWeather(0)` が呼ばれていれば自動的に正しい状態になるはず。

- [ ] **Step 5: コミット**

```bash
git add mountain_timer/index.html
git commit -m "feat: mountain timer — 天気変化・虹位置・時刻カラー調整"
```

---

## セルフレビュー

スペックとの対照:

| 要件 | 実装箇所 | 状態 |
|------|----------|------|
| 単一HTMLファイル | `mountain_timer/index.html` | Task 1 |
| 空グラデーション変化 | `applyWeather()` / KF_SKY_TOP/BTM | Task 1 |
| 雨（強→弱→消）| `animateRain()` / KF_RAIN | Task 1 |
| 雨雲フェードアウト | KF_CLOUD / rainClouds opacity | Task 1 |
| 太陽（下山中）| KF_SUN_CX/CY/OPA | Task 1 |
| 虹（頂上付近）| KF_RAINBOW / rainbowGroup | Task 1 |
| 遠景の山2つ | SVGのpolygon | Task 1 |
| メイン山 | SVGのpolygon + mtMainGrad | Task 1 |
| 木々（左右）| SVGのpolygon g | Task 1 |
| 頂上フラグ | SVG line + polygon | Task 1 |
| ハイカー移動 | `getHikerPos()` / `updateHiker()` | Task 1 |
| バンザイポーズ（頂上）| `updateHiker()` atPeak 分岐 | Task 1 |
| 歩行アニメ | `Math.sin(walkFrame)` | Task 1 |
| 足跡点線 | trailPts / polyline | Task 1 |
| プリセット5/10/15/20分 | `.preset-btn` | Task 1 |
| 分プルダウン 0〜99 | `buildMinSel()` | Task 1 |
| 秒プルダウン 0/15/30/45 | `<select id="secSel">` | Task 1 |
| スタート/一時停止トグル | startBtn click handler | Task 1 |
| リセット | resetBtn + initTimer() | Task 1 |
| ビープ音 | `playBeep()` / AudioContext | Task 1 |
| 終了時テキスト表示なし | ✓（playBeep()のみ） | Task 1 |
| 進捗バー | svgProgress width update | Task 1 |

全要件がTask 1でカバーされている。Task 2は動作確認と細部調整。
