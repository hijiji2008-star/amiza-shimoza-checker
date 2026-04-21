# アポリストメーカー Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Indeed Japanから求人掲載中の企業を自動収集し、派遣会社を除外した架電リストをブラウザで表示するローカルWebアプリを作る。

**Architecture:** FlaskのローカルサーバーをPythonで起動し、ブラウザでエリア・業種を選択してフォームを送信するとIndeed Japanをスクレイピングして結果をHTML一覧で返す。スクレイピングロジックは`scraper.py`に分離し、単体テスト可能にする。

**Tech Stack:** Python 3.10+, Flask, requests, beautifulsoup4, pytest

---

## ファイル構成

```
apo_list_maker/
  app.py                 # Flaskルート + 定数（区・業種リスト）
  scraper.py             # Indeed検索・HTML解析・フィルタリング
  requirements.txt       # 依存ライブラリ
  templates/
    index.html           # フォーム画面 + 結果テーブル（Jinja2）
  tests/
    test_scraper.py      # scraper.pyの単体テスト
```

---

### Task 1: プロジェクトセットアップ

**Files:**
- Create: `apo_list_maker/requirements.txt`
- Create: `apo_list_maker/tests/__init__.py`（空ファイル）

- [ ] **Step 1: ディレクトリ作成**

```bash
mkdir -p apo_list_maker/templates apo_list_maker/tests
touch apo_list_maker/tests/__init__.py
```

- [ ] **Step 2: requirements.txt を作成**

```
flask==3.0.3
requests==2.31.0
beautifulsoup4==4.12.3
pytest==8.2.0
```

- [ ] **Step 3: 依存ライブラリをインストール**

```bash
cd apo_list_maker
pip install -r requirements.txt
```

期待される出力: `Successfully installed flask-3.0.3 requests-2.31.0 beautifulsoup4-4.12.3 pytest-8.2.0`（バージョンは前後する場合あり）

- [ ] **Step 4: コミット**

```bash
git add apo_list_maker/
git commit -m "chore: アポリストメーカー プロジェクト初期化"
```

---

### Task 2: フィルタリングロジック + テスト

**Files:**
- Create: `apo_list_maker/scraper.py`（`is_dispatch` 関数のみ）
- Create: `apo_list_maker/tests/test_scraper.py`

- [ ] **Step 1: テストを書く**

`apo_list_maker/tests/test_scraper.py`:

```python
import pytest
from scraper import is_dispatch

def test_is_dispatch_company_name_keyword():
    assert is_dispatch("パーソルスタッフィング株式会社", "販売スタッフ") is True

def test_is_dispatch_company_name_派遣():
    assert is_dispatch("ABC派遣センター", "倉庫作業員") is True

def test_is_dispatch_job_title_keyword():
    assert is_dispatch("株式会社サンプル商事", "派遣スタッフ募集") is True

def test_is_not_dispatch_normal_company():
    assert is_dispatch("株式会社サンプル商事", "販売スタッフ") is False

def test_is_not_dispatch_empty():
    assert is_dispatch("", "") is False
```

- [ ] **Step 2: テストを実行して失敗を確認**

```bash
cd apo_list_maker
pytest tests/test_scraper.py -v
```

期待される出力: `ImportError: No module named 'scraper'`（関数未定義のため失敗）

- [ ] **Step 3: `is_dispatch` 関数を実装**

`apo_list_maker/scraper.py`:

```python
DISPATCH_KEYWORDS = [
    "派遣", "スタッフィング", "テンプ", "パーソル", "アデコ",
    "マンパワー", "リクルートスタッフ", "フルキャスト", "ランスタッド",
    "ウィルグループ", "アウトソーシング",
]

def is_dispatch(company_name: str, job_title: str) -> bool:
    text = company_name + job_title
    return any(kw in text for kw in DISPATCH_KEYWORDS)
```

- [ ] **Step 4: テストを再実行して全件パスを確認**

```bash
pytest tests/test_scraper.py -v
```

期待される出力:
```
tests/test_scraper.py::test_is_dispatch_company_name_keyword PASSED
tests/test_scraper.py::test_is_dispatch_company_name_派遣 PASSED
tests/test_scraper.py::test_is_dispatch_job_title_keyword PASSED
tests/test_scraper.py::test_is_not_dispatch_normal_company PASSED
tests/test_scraper.py::test_is_not_dispatch_empty PASSED
5 passed in 0.XXs
```

- [ ] **Step 5: コミット**

```bash
git add apo_list_maker/scraper.py apo_list_maker/tests/test_scraper.py
git commit -m "feat: 派遣会社フィルタリングロジック追加"
```

---

### Task 3: HTMLパース（求人カード解析）+ テスト

**Files:**
- Modify: `apo_list_maker/scraper.py`（`parse_job_cards` 関数を追加）
- Modify: `apo_list_maker/tests/test_scraper.py`（テストを追加）

- [ ] **Step 1: テストを追加**

`apo_list_maker/tests/test_scraper.py` の末尾に追記:

```python
from scraper import parse_job_cards

SAMPLE_HTML_DISPATCH = """
<html><body>
<div class="job_seen_beacon">
  <h2 class="jobTitle"><a class="jcs-JobTitle" href="/rc/clk?jk=aaa111"><span>派遣スタッフ募集</span></a></h2>
  <span data-testid="company-name">パーソルスタッフィング株式会社</span>
</div>
</body></html>
"""

SAMPLE_HTML_VALID = """
<html><body>
<div class="job_seen_beacon">
  <h2 class="jobTitle"><a class="jcs-JobTitle" href="/rc/clk?jk=bbb222"><span>販売スタッフ</span></a></h2>
  <span data-testid="company-name">株式会社サンプル商事</span>
</div>
</body></html>
"""

SAMPLE_HTML_MULTI = """
<html><body>
<div class="job_seen_beacon">
  <h2 class="jobTitle"><a class="jcs-JobTitle" href="/rc/clk?jk=aaa111"><span>派遣スタッフ</span></a></h2>
  <span data-testid="company-name">フルキャスト株式会社</span>
</div>
<div class="job_seen_beacon">
  <h2 class="jobTitle"><a class="jcs-JobTitle" href="/rc/clk?jk=bbb222"><span>倉庫作業員</span></a></h2>
  <span data-testid="company-name">株式会社田中倉庫</span>
</div>
</body></html>
"""

def test_parse_excludes_dispatch():
    results = parse_job_cards(SAMPLE_HTML_DISPATCH, "新宿区", "販売・小売")
    assert results == []

def test_parse_includes_valid_company():
    results = parse_job_cards(SAMPLE_HTML_VALID, "新宿区", "販売・小売")
    assert len(results) == 1
    r = results[0]
    assert r["company"] == "株式会社サンプル商事"
    assert r["area"] == "新宿区"
    assert r["industry"] == "販売・小売"
    assert r["indeed_url"] == "https://jp.indeed.com/rc/clk?jk=bbb222"
    assert r["job_title"] == "販売スタッフ"
    assert r["website"] == "—"

def test_parse_multi_filters_dispatch_only():
    results = parse_job_cards(SAMPLE_HTML_MULTI, "新宿区", "倉庫・物流")
    assert len(results) == 1
    assert results[0]["company"] == "株式会社田中倉庫"
```

- [ ] **Step 2: テストを実行して失敗を確認**

```bash
pytest tests/test_scraper.py -v -k "parse"
```

期待される出力: `ImportError: cannot import name 'parse_job_cards'`

- [ ] **Step 3: `parse_job_cards` 関数を実装**

`apo_list_maker/scraper.py` に追記:

```python
from bs4 import BeautifulSoup

def parse_job_cards(html: str, area: str, industry: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for card in soup.select("div.job_seen_beacon"):
        company_tag = card.select_one("[data-testid='company-name']")
        title_tag = card.select_one("h2.jobTitle a")
        if not company_tag or not title_tag:
            continue

        company_name = company_tag.get_text(strip=True)
        job_title = title_tag.get_text(strip=True)
        href = title_tag.get("href", "")
        job_url = f"https://jp.indeed.com{href}" if href.startswith("/") else href

        if is_dispatch(company_name, job_title):
            continue

        results.append({
            "company": company_name,
            "industry": industry,
            "area": area,
            "indeed_url": job_url,
            "website": "—",
            "job_title": job_title,
        })

    return results
```

- [ ] **Step 4: テストを再実行して全件パスを確認**

```bash
pytest tests/test_scraper.py -v
```

期待される出力: `8 passed in 0.XXs`

- [ ] **Step 5: コミット**

```bash
git add apo_list_maker/scraper.py apo_list_maker/tests/test_scraper.py
git commit -m "feat: Indeed求人カードのHTMLパース処理を追加"
```

---

### Task 4: Indeed検索 + 重複排除

**Files:**
- Modify: `apo_list_maker/scraper.py`（`search_indeed` 関数を追加）
- Modify: `apo_list_maker/tests/test_scraper.py`（重複排除テストを追加）

- [ ] **Step 1: 重複排除テストを追加**

`apo_list_maker/tests/test_scraper.py` の末尾に追記:

```python
from scraper import deduplicate

def test_deduplicate_removes_same_company():
    records = [
        {"company": "株式会社A", "area": "新宿区", "industry": "販売・小売", "indeed_url": "https://jp.indeed.com/1", "website": "—", "job_title": "販売"},
        {"company": "株式会社A", "area": "渋谷区", "industry": "倉庫・物流", "indeed_url": "https://jp.indeed.com/2", "website": "—", "job_title": "倉庫"},
        {"company": "株式会社B", "area": "新宿区", "industry": "販売・小売", "indeed_url": "https://jp.indeed.com/3", "website": "—", "job_title": "販売"},
    ]
    result = deduplicate(records)
    assert len(result) == 2
    companies = [r["company"] for r in result]
    assert "株式会社A" in companies
    assert "株式会社B" in companies

def test_deduplicate_keeps_first_occurrence():
    records = [
        {"company": "株式会社A", "area": "新宿区", "industry": "販売・小売", "indeed_url": "https://jp.indeed.com/1", "website": "—", "job_title": "販売"},
        {"company": "株式会社A", "area": "渋谷区", "industry": "倉庫・物流", "indeed_url": "https://jp.indeed.com/2", "website": "—", "job_title": "倉庫"},
    ]
    result = deduplicate(records)
    assert result[0]["area"] == "新宿区"
```

- [ ] **Step 2: テストを実行して失敗を確認**

```bash
pytest tests/test_scraper.py -v -k "deduplicate"
```

期待される出力: `ImportError: cannot import name 'deduplicate'`

- [ ] **Step 3: `deduplicate` と `search_indeed` を実装**

`apo_list_maker/scraper.py` の先頭に `import` を追加し、関数を追記:

```python
import requests
import time
import random
```

```python
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
}

def deduplicate(records: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for r in records:
        if r["company"] not in seen:
            seen.add(r["company"])
            result.append(r)
    return result

def search_indeed(
    areas: list[str],
    industries: dict[str, str],
    limit: int,
) -> list[dict]:
    """
    areas: 区名のリスト e.g. ["新宿区", "渋谷区"]
    industries: {表示名: 検索キーワード} e.g. {"販売・小売": "販売"}
    limit: 最大取得件数
    """
    all_results = []

    for area in areas:
        for industry_name, keyword in industries.items():
            if len(all_results) >= limit:
                break

            print(f"🔍 {area} × {industry_name} を検索中...")
            url = f"https://jp.indeed.com/jobs?q={keyword}&l={area}+東京都"

            try:
                resp = requests.get(url, headers=HEADERS, timeout=10)
                resp.raise_for_status()
                cards = parse_job_cards(resp.text, area, industry_name)
                before = len(all_results)
                all_results.extend(cards)
                all_results = deduplicate(all_results)
                print(f"   → {len(all_results) - before}件追加（累計 {len(all_results)}件）")

            except requests.RequestException as e:
                print(f"⚠️  エラー: {e}")
                time.sleep(5)

            time.sleep(random.uniform(1.0, 2.0))

    result = all_results[:limit]
    print(f"✅ 完了！{len(result)}件")
    return result
```

- [ ] **Step 4: テストを全件実行してパスを確認**

```bash
pytest tests/test_scraper.py -v
```

期待される出力: `10 passed in 0.XXs`

- [ ] **Step 5: コミット**

```bash
git add apo_list_maker/scraper.py apo_list_maker/tests/test_scraper.py
git commit -m "feat: Indeed検索・重複排除ロジックを追加"
```

---

### Task 5: Flaskアプリ（ルート定義）

**Files:**
- Create: `apo_list_maker/app.py`

- [ ] **Step 1: `app.py` を作成**

`apo_list_maker/app.py`:

```python
import webbrowser
from flask import Flask, render_template, request
from scraper import search_indeed

app = Flask(__name__)

WARDS = [
    "千代田区", "中央区", "港区", "新宿区", "文京区",
    "台東区", "墨田区", "江東区", "品川区", "目黒区",
    "大田区", "世田谷区", "渋谷区", "中野区", "杉並区",
    "豊島区", "北区", "荒川区", "板橋区", "練馬区",
    "足立区", "葛飾区", "江戸川区",
]

INDUSTRIES = {
    "販売・小売": "販売",
    "倉庫・物流": "倉庫",
    "製造": "製造",
    "飲食": "飲食",
    "事務": "事務",
    "IT・通信": "IT",
}

@app.route("/")
def index():
    return render_template("index.html", wards=WARDS, industries=list(INDUSTRIES.keys()))

@app.route("/search", methods=["POST"])
def search():
    selected_areas = request.form.getlist("areas")
    selected_industries = request.form.getlist("industries")
    limit = int(request.form.get("limit", 50))

    error = None
    results = []

    if not selected_areas or not selected_industries:
        error = "エリアと業種を両方選択してください"
    else:
        filtered = {k: v for k, v in INDUSTRIES.items() if k in selected_industries}
        results = search_indeed(selected_areas, filtered, limit)

    return render_template(
        "index.html",
        wards=WARDS,
        industries=list(INDUSTRIES.keys()),
        results=results,
        count=len(results),
        error=error,
    )

if __name__ == "__main__":
    webbrowser.open("http://localhost:5000")
    app.run(debug=False)
```

- [ ] **Step 2: Flaskが起動するか確認（Ctrl+Cで停止）**

```bash
cd apo_list_maker
python app.py
```

期待される出力: `* Running on http://127.0.0.1:5000` ※ブラウザが開くがテンプレートがないのでエラー画面になる。起動できれば OK。

- [ ] **Step 3: コミット**

```bash
git add apo_list_maker/app.py
git commit -m "feat: Flaskルート定義を追加"
```

---

### Task 6: HTMLテンプレート（フォーム + 結果テーブル）

**Files:**
- Create: `apo_list_maker/templates/index.html`

- [ ] **Step 1: `index.html` を作成**

`apo_list_maker/templates/index.html`:

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>アポリストメーカー</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: #0d1117; color: #e6edf3; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; min-height: 100vh; }
    header { background: #161b22; border-bottom: 1px solid #30363d; padding: 16px 24px; }
    header h1 { font-size: 20px; font-weight: 700; background: linear-gradient(90deg, #818cf8, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    main { max-width: 1000px; margin: 32px auto; padding: 0 24px; }
    .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 24px; margin-bottom: 24px; }
    .card h2 { font-size: 15px; color: #8b949e; margin-bottom: 16px; text-transform: uppercase; letter-spacing: .05em; }
    .ward-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); gap: 8px; }
    .industry-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 8px; }
    label.checkbox { display: flex; align-items: center; gap: 8px; padding: 6px 10px; border: 1px solid #30363d; border-radius: 6px; cursor: pointer; font-size: 13px; transition: border-color .15s; }
    label.checkbox:hover { border-color: #818cf8; }
    label.checkbox input[type=checkbox]:checked + span { color: #38bdf8; }
    label.checkbox input[type=checkbox]:checked { accent-color: #818cf8; }
    .controls { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; margin-top: 8px; }
    select { background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #e6edf3; padding: 8px 12px; font-size: 14px; }
    button[type=submit] { background: linear-gradient(90deg, #818cf8, #38bdf8); border: none; border-radius: 6px; color: #0d1117; font-size: 14px; font-weight: 700; padding: 10px 24px; cursor: pointer; transition: opacity .15s; }
    button[type=submit]:hover { opacity: .85; }
    .error { background: #2d1b1b; border: 1px solid #f85149; border-radius: 6px; color: #f85149; padding: 12px 16px; margin-bottom: 16px; }
    .result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
    .result-header span { font-size: 14px; color: #8b949e; }
    .copy-btn { background: #21262d; border: 1px solid #30363d; border-radius: 6px; color: #e6edf3; font-size: 13px; padding: 6px 14px; cursor: pointer; transition: background .15s; }
    .copy-btn:hover { background: #30363d; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th { background: #0d1117; color: #8b949e; font-weight: 600; padding: 10px 12px; text-align: left; border-bottom: 1px solid #30363d; }
    td { padding: 10px 12px; border-bottom: 1px solid #21262d; vertical-align: top; }
    tr:hover td { background: #1c2128; }
    a { color: #38bdf8; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .loading { display: none; color: #8b949e; font-size: 14px; margin-top: 8px; }
  </style>
</head>
<body>
  <header><h1>アポリストメーカー</h1></header>
  <main>
    <form method="POST" action="/search" onsubmit="showLoading()">
      <div class="card">
        <h2>エリア（複数選択可）</h2>
        <div class="ward-grid">
          {% for ward in wards %}
          <label class="checkbox">
            <input type="checkbox" name="areas" value="{{ ward }}"
              {% if request.form.getlist('areas') and ward in request.form.getlist('areas') %}checked{% endif %}>
            <span>{{ ward }}</span>
          </label>
          {% endfor %}
        </div>
      </div>

      <div class="card">
        <h2>業種（複数選択可）</h2>
        <div class="industry-grid">
          {% for industry in industries %}
          <label class="checkbox">
            <input type="checkbox" name="industries" value="{{ industry }}"
              {% if request.form.getlist('industries') and industry in request.form.getlist('industries') %}checked{% endif %}>
            <span>{{ industry }}</span>
          </label>
          {% endfor %}
        </div>
      </div>

      <div class="controls">
        <label style="font-size:14px; color:#8b949e;">取得件数上限:
          <select name="limit">
            <option value="50">50件</option>
            <option value="100">100件</option>
            <option value="200">200件</option>
          </select>
        </label>
        <button type="submit">リスト作成</button>
        <span class="loading" id="loading">🔍 検索中... しばらくお待ちください</span>
      </div>
    </form>

    {% if error %}
    <div class="error">{{ error }}</div>
    {% endif %}

    {% if results is defined and results %}
    <div class="card">
      <div class="result-header">
        <span>{{ count }}件（派遣会社除外済み）</span>
        <button class="copy-btn" onclick="copyTable()">全コピー（Excel貼付け用）</button>
      </div>
      <table id="result-table">
        <thead>
          <tr>
            <th>#</th>
            <th>会社名</th>
            <th>業種</th>
            <th>エリア</th>
            <th>公式HP</th>
            <th>Indeed掲載ページ</th>
            <th>求人タイトル</th>
          </tr>
        </thead>
        <tbody>
          {% for r in results %}
          <tr>
            <td>{{ loop.index }}</td>
            <td>{{ r.company }}</td>
            <td>{{ r.industry }}</td>
            <td>{{ r.area }}</td>
            <td>{% if r.website != '—' %}<a href="{{ r.website }}" target="_blank">{{ r.website }}</a>{% else %}—{% endif %}</td>
            <td><a href="{{ r.indeed_url }}" target="_blank">Indeedを見る</a></td>
            <td>{{ r.job_title }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    {% endif %}
  </main>

  <script>
    function showLoading() {
      document.getElementById('loading').style.display = 'inline';
    }

    function copyTable() {
      const table = document.getElementById('result-table');
      const rows = Array.from(table.rows);
      const tsv = rows.map(row =>
        Array.from(row.cells).map(cell => cell.innerText.trim()).join('\t')
      ).join('\n');
      navigator.clipboard.writeText(tsv).then(() => {
        const btn = document.querySelector('.copy-btn');
        btn.textContent = 'コピーしました！';
        setTimeout(() => btn.textContent = '全コピー（Excel貼付け用）', 2000);
      });
    }
  </script>
</body>
</html>
```

- [ ] **Step 2: アプリを起動して動作確認**

```bash
cd apo_list_maker
python app.py
```

ブラウザで `http://localhost:5000` を開き、以下を確認する:
- 23区のチェックボックスが表示される
- 業種チェックボックスが表示される
- フォームを送信すると「検索中...」が表示される
- 結果が表示される（実際にIndeedに繋いで確認）

※ Indeedのサイト構造によっては結果が0件になることがある。その場合は Task 7 のデバッグ手順に従う。

- [ ] **Step 3: コミット**

```bash
git add apo_list_maker/templates/index.html
git commit -m "feat: フォーム画面・結果テーブルのHTMLテンプレートを追加"
```

---

### Task 7: 動作確認・セレクタ調整

**Files:**
- Modify: `apo_list_maker/scraper.py`（必要に応じてセレクタを修正）

Indeedはサイト構造を変更することがある。結果が0件の場合は以下で原因を確認する。

- [ ] **Step 1: 実際のHTMLを確認するデバッグスクリプトを実行**

```python
# デバッグ用（ターミナルで実行）
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
}

resp = requests.get("https://jp.indeed.com/jobs?q=販売&l=新宿区+東京都", headers=HEADERS)
soup = BeautifulSoup(resp.text, "html.parser")

# 実際のHTMLを確認
cards = soup.select("div.job_seen_beacon")
print(f"カード件数: {len(cards)}")
if cards:
    print(cards[0].prettify()[:2000])  # 最初のカードのHTML構造を確認
```

- [ ] **Step 2: セレクタを実際の構造に合わせて修正**

`parse_job_cards` 内のセレクタ（`"div.job_seen_beacon"`、`"[data-testid='company-name']"`、`"h2.jobTitle a"`）をStep 1の出力に合わせて修正する。

変更例（実際のHTMLに合わせる）:
```python
# 会社名のセレクタ例
company_tag = (
    card.select_one("[data-testid='company-name']") or
    card.select_one(".companyName") or
    card.select_one("[class*='company']")
)

# タイトルリンクのセレクタ例
title_tag = (
    card.select_one("h2.jobTitle a") or
    card.select_one("a.jcs-JobTitle") or
    card.select_one("h2 a")
)
```

- [ ] **Step 3: テストが引き続きパスすることを確認**

```bash
pytest tests/test_scraper.py -v
```

期待される出力: `10 passed in 0.XXs`（テストはサンプルHTMLを使うため影響なし）

- [ ] **Step 4: 最終コミット**

```bash
git add apo_list_maker/scraper.py
git commit -m "fix: Indeedセレクタを実際のHTML構造に合わせて調整"
```

---

## 実行方法（完成後）

```bash
cd apo_list_maker
python app.py
# → ブラウザが自動で開く
# → エリア・業種を選んで「リスト作成」ボタン
# → 結果が表示されたら「全コピー」でExcelに貼り付け
```
