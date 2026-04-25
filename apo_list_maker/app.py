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
    limit_raw = (request.form.get("limit") or "").strip()
    try:
        limit = int(limit_raw) if limit_raw else 50
    except ValueError:
        limit = 50
    limit = max(10, min(limit, 100))

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
    # 起動直後に open すると間に合わないことがあるので、基本は .command 側で開く想定
    app.run(debug=False, port=5001)
