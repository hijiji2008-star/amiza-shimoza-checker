# YT Downloader Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Flask web app that downloads YouTube videos as MP4 with quality selection, real-time SSE progress bar, configurable save folder, and one-click yt-dlp updates.

**Architecture:** Flask backend with yt-dlp for downloading. Quality list fetched on demand via POST /fetch_qualities. Download progress streamed to the browser via Server-Sent Events (SSE) using a `threading.Queue` as the bridge between yt-dlp's `progress_hooks` and the Flask SSE generator. Save-folder config persisted in `config.json`.

**Tech Stack:** Python 3, Flask, yt-dlp, threading, queue, subprocess, Vanilla JS (EventSource API), pytest + unittest.mock

---

## File Map

| File | Responsibility |
|---|---|
| `yt_downloader/downloader.py` | yt-dlp wrapper: `get_available_qualities()`, `download_video()` |
| `yt_downloader/app.py` | Flask routes: `/`, `/config`, `/fetch_qualities`, `/download`, `/update_ytdlp` |
| `yt_downloader/requirements.txt` | Python dependencies |
| `yt_downloader/templates/index.html` | Single-page UI with Vanilla JS |
| `yt_downloader/tests/__init__.py` | Empty — makes tests a package |
| `yt_downloader/tests/conftest.py` | sys.path fix so tests can import from parent dir |
| `yt_downloader/tests/test_downloader.py` | Unit tests for downloader.py (mock yt-dlp) |
| `yt_downloader/tests/test_app.py` | Flask route tests (mock downloader functions) |
| `yt_downloader/YTダウンローダー起動.command` | Double-click launch script |

---

### Task 1: Project scaffold

**Files:**
- Create: `yt_downloader/` directory tree
- Create: `yt_downloader/requirements.txt`
- Create: `yt_downloader/tests/__init__.py`
- Create: `yt_downloader/tests/conftest.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p /Users/obatatsunari/projects/yt_downloader/templates
mkdir -p /Users/obatatsunari/projects/yt_downloader/tests
touch /Users/obatatsunari/projects/yt_downloader/tests/__init__.py
```

- [ ] **Step 2: Create requirements.txt**

`yt_downloader/requirements.txt`:
```
flask
yt-dlp
pytest
```

- [ ] **Step 3: Create conftest.py**

`yt_downloader/tests/conftest.py`:
```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
```

- [ ] **Step 4: Install dependencies**

```bash
cd /Users/obatatsunari/projects/yt_downloader
pip3 install -r requirements.txt
```

Expected: `Successfully installed flask yt-dlp ...`
Verify: `python3 -c "import flask, yt_dlp; print('OK')"` -> `OK`

- [ ] **Step 5: Commit scaffold**

```bash
cd /Users/obatatsunari/projects
git add yt_downloader/
git commit -m "feat: yt_downloaderプロジェクト初期スキャフォールド"
```

---

### Task 2: downloader.py — get_available_qualities (TDD)

**Files:**
- Create: `yt_downloader/tests/test_downloader.py`
- Create: `yt_downloader/downloader.py` (quality function only)

- [ ] **Step 1: Write failing tests**

`yt_downloader/tests/test_downloader.py`:
```python
from unittest.mock import patch, MagicMock
from downloader import get_available_qualities


def _mock_ydl(formats):
    m = MagicMock()
    m.__enter__ = lambda s: m
    m.__exit__ = MagicMock(return_value=False)
    m.extract_info.return_value = {'formats': formats, 'title': 'Test Video'}
    return m


def test_get_available_qualities_sorted_descending():
    formats = [
        {'vcodec': 'avc1', 'height': 720},
        {'vcodec': 'avc1', 'height': 1080},
        {'vcodec': 'avc1', 'height': 480},
        {'vcodec': 'none', 'height': 1080},  # audio-only -- must be excluded
    ]
    with patch('downloader.yt_dlp.YoutubeDL', return_value=_mock_ydl(formats)):
        result = get_available_qualities('https://youtube.com/watch?v=x')
    assert result == [
        {'height': 1080, 'label': '1080p'},
        {'height': 720, 'label': '720p'},
        {'height': 480, 'label': '480p'},
    ]


def test_get_available_qualities_deduplicates():
    formats = [
        {'vcodec': 'avc1', 'height': 1080},
        {'vcodec': 'vp9',  'height': 1080},  # same height, different codec
    ]
    with patch('downloader.yt_dlp.YoutubeDL', return_value=_mock_ydl(formats)):
        result = get_available_qualities('https://youtube.com/watch?v=x')
    assert len(result) == 1
    assert result[0] == {'height': 1080, 'label': '1080p'}
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd /Users/obatatsunari/projects/yt_downloader
python3 -m pytest tests/test_downloader.py -v
```

Expected: `ModuleNotFoundError: No module named 'downloader'`

- [ ] **Step 3: Create downloader.py with get_available_qualities**

`yt_downloader/downloader.py`:
```python
import os
import queue
import yt_dlp


def get_available_qualities(url):
    opts = {'quiet': True, 'skip_download': True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    seen = set()
    qualities = []
    for f in info.get('formats', []):
        if f.get('vcodec') not in (None, 'none') and f.get('height'):
            h = f['height']
            if h not in seen:
                seen.add(h)
                qualities.append({'height': h, 'label': f'{h}p'})
    qualities.sort(key=lambda x: x['height'], reverse=True)
    return qualities
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /Users/obatatsunari/projects/yt_downloader
python3 -m pytest tests/test_downloader.py -v
```

Expected: 2 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/obatatsunari/projects
git add yt_downloader/downloader.py yt_downloader/tests/test_downloader.py
git commit -m "feat: get_available_qualities をTDDで実装"
```

---

### Task 3: downloader.py — download_video (TDD)

**Files:**
- Modify: `yt_downloader/downloader.py` (add download_video)
- Modify: `yt_downloader/tests/test_downloader.py` (add tests)

- [ ] **Step 1: Append failing tests**

Append to `yt_downloader/tests/test_downloader.py`:
```python
import queue as queue_mod
from downloader import download_video


def test_download_video_sentinel_always_last():
    """Queue must always end with None so the SSE generator can stop."""
    q = queue_mod.Queue()
    mock = _mock_ydl([])
    mock.extract_info.return_value = {'title': 'My Video', 'formats': []}
    with patch('downloader.yt_dlp.YoutubeDL', return_value=mock):
        download_video('https://youtube.com/watch?v=x', '1080', '/tmp', q)
    items = list(q.queue)
    assert items[-1] is None


def test_download_video_sends_finished_with_title():
    q = queue_mod.Queue()
    mock = _mock_ydl([])
    mock.extract_info.return_value = {'title': 'Cool Video', 'formats': []}
    with patch('downloader.yt_dlp.YoutubeDL', return_value=mock):
        download_video('https://youtube.com/watch?v=x', '1080', '/tmp', q)
    items = list(q.queue)
    finished = [i for i in items if isinstance(i, dict) and i.get('status') == 'finished']
    assert len(finished) == 1
    assert finished[0]['filename'] == 'Cool Video.mp4'


def test_download_video_sends_error_on_exception():
    q = queue_mod.Queue()
    mock = _mock_ydl([])
    mock.extract_info.side_effect = Exception('network error')
    with patch('downloader.yt_dlp.YoutubeDL', return_value=mock):
        download_video('https://youtube.com/watch?v=x', '1080', '/tmp', q)
    items = list(q.queue)
    errors = [i for i in items if isinstance(i, dict) and i.get('status') == 'error']
    assert len(errors) == 1
    assert 'network error' in errors[0]['message']
    assert items[-1] is None
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd /Users/obatatsunari/projects/yt_downloader
python3 -m pytest tests/test_downloader.py::test_download_video_sentinel_always_last -v
```

Expected: `ImportError` -- `download_video` not defined yet

- [ ] **Step 3: Add download_video to downloader.py**

Append to `yt_downloader/downloader.py` (after the existing `get_available_qualities` function):
```python

def download_video(url, quality, save_dir, progress_queue):
    def progress_hook(d):
        if d['status'] == 'downloading':
            raw = d.get('_percent_str', '0%').strip()
            try:
                pct = float(raw.replace('%', ''))
            except ValueError:
                pct = 0.0
            progress_queue.put({
                'status': 'downloading',
                'percent': pct,
                'speed': d.get('_speed_str', ''),
                'eta': d.get('_eta_str', ''),
            })

    opts = {
        'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
        'outtmpl': os.path.join(save_dir, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'progress_hooks': [progress_hook],
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'video')
            progress_queue.put({'status': 'finished', 'filename': f'{title}.mp4'})
    except Exception as e:
        progress_queue.put({'status': 'error', 'message': str(e)})
    finally:
        progress_queue.put(None)
```

- [ ] **Step 4: Run all downloader tests**

```bash
cd /Users/obatatsunari/projects/yt_downloader
python3 -m pytest tests/test_downloader.py -v
```

Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/obatatsunari/projects
git add yt_downloader/downloader.py yt_downloader/tests/test_downloader.py
git commit -m "feat: download_video をTDDで実装（SSEキュー・エラーハンドリング）"
```

---

### Task 4: Flask app.py

**Files:**
- Create: `yt_downloader/app.py`

- [ ] **Step 1: Create app.py**

`yt_downloader/app.py`:
```python
import json
import os
import queue
import subprocess
import threading

from flask import Flask, Response, jsonify, render_template, request

from downloader import get_available_qualities, download_video

app = Flask(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
DEFAULT_SAVE_DIR = os.path.expanduser('~/Downloads')


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {'save_dir': DEFAULT_SAVE_DIR}


def save_config(data):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(data, f)


@app.route('/')
def index():
    config = load_config()
    return render_template('index.html', save_dir=config['save_dir'])


@app.route('/config', methods=['GET'])
def get_config():
    return jsonify(load_config())


@app.route('/config', methods=['POST'])
def update_config():
    data = request.get_json()
    save_dir = (data.get('save_dir') or '').strip()
    if not save_dir:
        return jsonify({'error': '保存先を入力してください'}), 400
    if not os.path.isdir(save_dir):
        return jsonify({'error': f'フォルダが存在しません: {save_dir}'}), 400
    save_config({'save_dir': save_dir})
    return jsonify({'save_dir': save_dir})


@app.route('/fetch_qualities', methods=['POST'])
def fetch_qualities():
    data = request.get_json()
    url = (data.get('url') or '').strip()
    if not url:
        return jsonify({'error': 'URLを入力してください'}), 400
    try:
        qualities = get_available_qualities(url)
        return jsonify({'qualities': qualities})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/download')
def download():
    url = (request.args.get('url') or '').strip()
    quality = request.args.get('quality', '1080')
    if not url:
        return jsonify({'error': 'URLが必要です'}), 400

    config = load_config()
    progress_queue = queue.Queue()

    threading.Thread(
        target=download_video,
        args=(url, quality, config['save_dir'], progress_queue),
        daemon=True,
    ).start()

    def generate():
        while True:
            item = progress_queue.get()
            if item is None:
                break
            yield f'data: {json.dumps(item, ensure_ascii=False)}\n\n'

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )


@app.route('/update_ytdlp', methods=['POST'])
def update_ytdlp():
    try:
        result = subprocess.run(
            ['pip3', 'install', '-U', 'yt-dlp'],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            return jsonify({'message': 'yt-dlp を最新版に更新しました'})
        return jsonify({'error': result.stderr}), 500
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'タイムアウト（120秒）'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(port=5002, debug=True)
```

- [ ] **Step 2: Verify app starts**

```bash
cd /Users/obatatsunari/projects/yt_downloader
python3 -c "import app; print('app imported OK')"
```

Expected: `app imported OK`

- [ ] **Step 3: Commit**

```bash
cd /Users/obatatsunari/projects
git add yt_downloader/app.py
git commit -m "feat: Flask全ルート実装（config・fetch_qualities・download SSE・update_ytdlp）"
```

---

### Task 5: Flask route tests

**Files:**
- Create: `yt_downloader/tests/test_app.py`

- [ ] **Step 1: Write tests**

`yt_downloader/tests/test_app.py`:
```python
import json, os
from unittest.mock import patch
import pytest
import app as flask_app


@pytest.fixture
def client(tmp_path):
    flask_app.app.config['TESTING'] = True
    flask_app.CONFIG_PATH = str(tmp_path / 'config.json')
    with flask_app.app.test_client() as c:
        yield c


def test_get_config_default(client):
    resp = client.get('/config')
    assert resp.status_code == 200
    assert 'save_dir' in resp.get_json()


def test_update_config_nonexistent_dir(client):
    resp = client.post('/config',
                       data=json.dumps({'save_dir': '/no/such/dir/xyz'}),
                       content_type='application/json')
    assert resp.status_code == 400
    assert 'error' in resp.get_json()


def test_update_config_valid_dir(client, tmp_path):
    resp = client.post('/config',
                       data=json.dumps({'save_dir': str(tmp_path)}),
                       content_type='application/json')
    assert resp.status_code == 200
    assert resp.get_json()['save_dir'] == str(tmp_path)


def test_fetch_qualities_missing_url(client):
    resp = client.post('/fetch_qualities',
                       data=json.dumps({}),
                       content_type='application/json')
    assert resp.status_code == 400


def test_fetch_qualities_returns_list(client):
    mock_qualities = [{'height': 1080, 'label': '1080p'}]
    with patch('app.get_available_qualities', return_value=mock_qualities):
        resp = client.post('/fetch_qualities',
                           data=json.dumps({'url': 'https://youtube.com/watch?v=x'}),
                           content_type='application/json')
    assert resp.status_code == 200
    assert resp.get_json()['qualities'] == mock_qualities


def test_fetch_qualities_handles_error(client):
    with patch('app.get_available_qualities', side_effect=Exception('invalid url')):
        resp = client.post('/fetch_qualities',
                           data=json.dumps({'url': 'bad-url'}),
                           content_type='application/json')
    assert resp.status_code == 400
    assert 'error' in resp.get_json()


def test_update_ytdlp_success(client):
    with patch('app.subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        resp = client.post('/update_ytdlp')
    assert resp.status_code == 200
    assert 'message' in resp.get_json()


def test_update_ytdlp_failure(client):
    with patch('app.subprocess.run') as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = 'pip error'
        resp = client.post('/update_ytdlp')
    assert resp.status_code == 500
    assert 'error' in resp.get_json()
```

- [ ] **Step 2: Run all tests**

```bash
cd /Users/obatatsunari/projects/yt_downloader
python3 -m pytest tests/ -v
```

Expected: All 13 tests PASS (5 downloader + 8 app)

- [ ] **Step 3: Commit**

```bash
cd /Users/obatatsunari/projects
git add yt_downloader/tests/test_app.py
git commit -m "test: Flaskルートの全ユニットテストを追加"
```

---

### Task 6: Frontend UI

**Files:**
- Create: `yt_downloader/templates/index.html`

Note: Quality radio buttons are created with `createElement` (not innerHTML) to avoid XSS risk from video metadata.

- [ ] **Step 1: Create index.html**

`yt_downloader/templates/index.html`:
```html
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YT Downloader</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: #0d1117;
  color: #e6edf3;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 16px;
}
.card {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 12px;
  padding: 28px 24px;
  width: 100%;
  max-width: 560px;
}
h1 {
  font-size: 1.4rem;
  font-weight: 700;
  margin-bottom: 24px;
  background: linear-gradient(135deg, #818cf8, #38bdf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.section { margin-bottom: 20px; }
.label {
  display: block;
  font-size: 0.75rem;
  color: #8b949e;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 6px;
}
.row { display: flex; gap: 8px; align-items: center; }
input[type="text"] {
  flex: 1;
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 6px;
  padding: 9px 12px;
  color: #e6edf3;
  font-size: 0.95rem;
  outline: none;
  transition: border-color 0.15s;
}
input[type="text"]:focus { border-color: #818cf8; }
#saveDirDisplay {
  flex: 1;
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 6px;
  padding: 9px 12px;
  color: #8b949e;
  font-size: 0.85rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.btn {
  padding: 8px 16px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  white-space: nowrap;
  transition: opacity 0.15s;
}
.btn:hover { opacity: 0.85; }
.btn:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-primary { background: linear-gradient(135deg, #818cf8, #38bdf8); color: #0d1117; }
.btn-secondary { background: #21262d; color: #e6edf3; border: 1px solid #30363d; }
.btn-ghost { background: #21262d; color: #f85149; border: 1px solid #30363d; font-size: 0.85rem; }
.quality-options { display: flex; gap: 14px; flex-wrap: wrap; margin-top: 6px; }
.quality-opt { display: flex; align-items: center; gap: 6px; cursor: pointer; }
.quality-opt input[type="radio"] { accent-color: #818cf8; }
#downloadBtn { width: 100%; padding: 11px; font-size: 1rem; margin-top: 16px; display: none; }
#progressSection { display: none; margin-top: 16px; }
.bar-bg { background: #0d1117; border-radius: 99px; height: 8px; overflow: hidden; margin-bottom: 8px; }
.bar-fill {
  height: 100%;
  width: 0%;
  background: linear-gradient(135deg, #818cf8, #38bdf8);
  border-radius: 99px;
  transition: width 0.3s;
}
.progress-meta { display: flex; justify-content: space-between; font-size: 0.78rem; color: #8b949e; }
#statusMsg { margin-top: 14px; font-size: 0.9rem; min-height: 1.2em; }
.ok { color: #3fb950; }
.err { color: #f85149; }
hr { border: none; border-top: 1px solid #30363d; margin: 20px 0; }
.update-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
#updateMsg { font-size: 0.82rem; color: #8b949e; }
</style>
</head>
<body>
<div class="card">
  <h1>YT Downloader</h1>

  <div class="section">
    <span class="label">保存先フォルダ</span>
    <div class="row">
      <div id="saveDirDisplay">読み込み中...</div>
      <button class="btn btn-secondary" id="changeDirBtn">変更</button>
    </div>
  </div>

  <div class="section">
    <span class="label">YouTube URL</span>
    <div class="row">
      <input type="text" id="urlInput" placeholder="https://www.youtube.com/watch?v=..." />
      <button class="btn btn-primary" id="fetchBtn">画質を取得</button>
    </div>
  </div>

  <div id="qualitySection" class="section" style="display:none">
    <span class="label">画質</span>
    <div class="quality-options" id="qualityOptions"></div>
    <button class="btn btn-primary" id="downloadBtn">ダウンロード</button>
  </div>

  <div id="progressSection">
    <div class="bar-bg"><div class="bar-fill" id="barFill"></div></div>
    <div class="progress-meta">
      <span id="pctLabel">0%</span>
      <span id="speedLabel"></span>
      <span id="etaLabel"></span>
    </div>
  </div>

  <div id="statusMsg"></div>

  <hr>

  <div class="update-row">
    <button class="btn btn-ghost" id="updateBtn">yt-dlp を更新</button>
    <span id="updateMsg">ダウンロードできなくなったらクリック</span>
  </div>
</div>

<script>
(function () {
  let es = null;

  async function loadConfig() {
    const res = await fetch('/config');
    const data = await res.json();
    document.getElementById('saveDirDisplay').textContent = data.save_dir;
  }

  async function changeDir() {
    const current = document.getElementById('saveDirDisplay').textContent;
    const newDir = prompt('新しい保存先フォルダのパス:', current);
    if (!newDir) return;
    const res = await fetch('/config', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({save_dir: newDir}),
    });
    const data = await res.json();
    if (data.error) { setStatus(data.error, 'err'); return; }
    document.getElementById('saveDirDisplay').textContent = data.save_dir;
    setStatus('保存先を更新しました', 'ok');
  }

  async function fetchQualities() {
    const url = document.getElementById('urlInput').value.trim();
    if (!url) { setStatus('URLを入力してください', 'err'); return; }
    const btn = document.getElementById('fetchBtn');
    btn.disabled = true;
    btn.textContent = '取得中...';
    setStatus('');
    try {
      const res = await fetch('/fetch_qualities', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({url}),
      });
      const data = await res.json();
      if (data.error) { setStatus(data.error, 'err'); return; }
      renderQualities(data.qualities);
    } finally {
      btn.disabled = false;
      btn.textContent = '画質を取得';
    }
  }

  function renderQualities(qualities) {
    const wrap = document.getElementById('qualityOptions');
    wrap.textContent = '';
    qualities.forEach(function (q, i) {
      const lbl = document.createElement('label');
      lbl.className = 'quality-opt';
      const radio = document.createElement('input');
      radio.type = 'radio';
      radio.name = 'quality';
      radio.value = String(q.height);
      if (i === 0) radio.checked = true;
      const span = document.createElement('span');
      span.textContent = q.label;
      lbl.appendChild(radio);
      lbl.appendChild(span);
      wrap.appendChild(lbl);
    });
    document.getElementById('qualitySection').style.display = 'block';
    document.getElementById('downloadBtn').style.display = 'block';
  }

  function startDownload() {
    const url = document.getElementById('urlInput').value.trim();
    const sel = document.querySelector('input[name="quality"]:checked');
    if (!sel) { setStatus('画質を選択してください', 'err'); return; }

    if (es) es.close();
    document.getElementById('progressSection').style.display = 'block';
    document.getElementById('downloadBtn').disabled = true;
    document.getElementById('barFill').style.width = '0%';
    document.getElementById('pctLabel').textContent = '0%';
    setStatus('ダウンロード中...');

    es = new EventSource('/download?url=' + encodeURIComponent(url) + '&quality=' + encodeURIComponent(sel.value));

    es.onmessage = function (e) {
      const d = JSON.parse(e.data);
      if (d.status === 'downloading') {
        const pct = Math.min(d.percent, 100);
        document.getElementById('barFill').style.width = pct + '%';
        document.getElementById('pctLabel').textContent = pct.toFixed(1) + '%';
        document.getElementById('speedLabel').textContent = d.speed || '';
        document.getElementById('etaLabel').textContent = d.eta ? ('残り ' + d.eta) : '';
      } else if (d.status === 'finished') {
        document.getElementById('barFill').style.width = '100%';
        document.getElementById('pctLabel').textContent = '100%';
        document.getElementById('speedLabel').textContent = '';
        document.getElementById('etaLabel').textContent = '';
        setStatus('完了: ' + d.filename, 'ok');
        document.getElementById('downloadBtn').disabled = false;
        es.close();
      } else if (d.status === 'error') {
        setStatus('エラー: ' + d.message, 'err');
        document.getElementById('downloadBtn').disabled = false;
        es.close();
      }
    };

    es.onerror = function () {
      setStatus('接続エラーが発生しました', 'err');
      document.getElementById('downloadBtn').disabled = false;
      es.close();
    };
  }

  async function updateYtdlp() {
    const btn = document.getElementById('updateBtn');
    btn.disabled = true;
    document.getElementById('updateMsg').textContent = '更新中...';
    try {
      const res = await fetch('/update_ytdlp', {method: 'POST'});
      const data = await res.json();
      document.getElementById('updateMsg').textContent = data.message || ('エラー: ' + data.error);
    } catch (err) {
      document.getElementById('updateMsg').textContent = 'エラーが発生しました';
    } finally {
      btn.disabled = false;
    }
  }

  function setStatus(msg, cls) {
    const el = document.getElementById('statusMsg');
    el.textContent = msg;
    el.className = cls || '';
  }

  document.getElementById('changeDirBtn').addEventListener('click', changeDir);
  document.getElementById('fetchBtn').addEventListener('click', fetchQualities);
  document.getElementById('downloadBtn').addEventListener('click', startDownload);
  document.getElementById('updateBtn').addEventListener('click', updateYtdlp);

  loadConfig();
}());
</script>
</body>
</html>
```

- [ ] **Step 2: Start the app and verify manually**

```bash
cd /Users/obatatsunari/projects/yt_downloader
python3 app.py
```

Open http://localhost:5002 and verify:
- 保存先フォルダが表示される
- 「変更」ボタンで保存先を変更できる
- URLを入力して「画質を取得」で画質ラジオボタンが出る
- 「ダウンロード」でプログレスバーがリアルタイム更新される
- 完了後にファイル名が表示される
- 「yt-dlp を更新」ボタンが動作する

- [ ] **Step 3: Commit**

```bash
cd /Users/obatatsunari/projects
git add yt_downloader/templates/index.html
git commit -m "feat: フロントエンドUI（プログレスバー・画質選択・更新ボタン）を実装"
```

---

### Task 7: Launch script + final check

**Files:**
- Create: `yt_downloader/YTダウンローダー起動.command`

- [ ] **Step 1: Create launch script**

`yt_downloader/YTダウンローダー起動.command`:
```bash
#!/bin/bash
cd "$(dirname "$0")"
python3 app.py
```

- [ ] **Step 2: Make executable**

```bash
chmod +x "/Users/obatatsunari/projects/yt_downloader/YTダウンローダー起動.command"
```

- [ ] **Step 3: Run full test suite**

```bash
cd /Users/obatatsunari/projects/yt_downloader
python3 -m pytest tests/ -v
```

Expected: All 13 tests PASS

- [ ] **Step 4: Final commit**

```bash
cd /Users/obatatsunari/projects
git add yt_downloader/
git commit -m "feat: 起動スクリプト追加・YTダウンローダー初期実装完了"
```
