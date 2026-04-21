from bs4 import BeautifulSoup

DISPATCH_KEYWORDS = [
    "派遣", "スタッフィング", "テンプ", "パーソル", "アデコ",
    "マンパワー", "リクルートスタッフ", "フルキャスト", "ランスタッド",
    "ウィルグループ", "アウトソーシング",
]

def is_dispatch(company_name: str, job_title: str) -> bool:
    text = company_name + job_title
    return any(kw in text for kw in DISPATCH_KEYWORDS)

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
