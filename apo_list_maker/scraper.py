import requests
import time
import random
import re
import urllib.parse
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
        # Fallback chain: Indeed occasionally changes class/testid names
        company_tag = (
            card.select_one("[data-testid='company-name']") or
            card.select_one(".companyName") or
            card.select_one("[class*='company']")
        )
        title_tag = (
            card.select_one("h2.jobTitle a") or
            card.select_one("a.jcs-JobTitle") or
            card.select_one("h2 a")
        )
        if not company_tag or not title_tag:
            continue

        company_name = company_tag.get_text(strip=True)
        job_title = title_tag.get_text(strip=True)
        href = title_tag.get("href", "")
        job_url = f"https://jp.indeed.com{href}" if href.startswith("/") else href

        card_text = card.get_text()
        if is_dispatch(company_name, job_title) or "派遣社員" in card_text:
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

PHONE_PATTERN = re.compile(r'0\d{1,4}[-−ー・]\d{1,4}[-−ー・]\d{4}')

def lookup_phone(company_name: str, page) -> str:
    query = urllib.parse.quote(f"{company_name} 代表電話番号")
    url = f"https://search.yahoo.co.jp/search?p={query}"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(2000)
        text = page.inner_text("body")
        match = PHONE_PATTERN.search(text)
        return match.group() if match else "—"
    except Exception:
        return "—"

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
    from playwright.sync_api import sync_playwright

    all_results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="ja-JP",
        )
        indeed_page = context.new_page()

        # Phase 1: Collect companies from Indeed
        for area in areas:
            for industry_name, keyword in industries.items():
                if len(all_results) >= limit:
                    break

                print(f"🔍 {area} × {industry_name} を検索中...")
                url = f"https://jp.indeed.com/jobs?q={keyword}&l={area}+東京都"

                try:
                    indeed_page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    indeed_page.wait_for_timeout(3000)
                    html = indeed_page.content()
                    cards = parse_job_cards(html, area, industry_name)
                    before = len(all_results)
                    all_results.extend(cards)
                    all_results = deduplicate(all_results)
                    added = len(all_results) - before
                    print(f"   → {added}件追加（累計 {len(all_results)}件）")
                except Exception as e:
                    print(f"⚠️  エラー: {e}")

                time.sleep(random.uniform(1.5, 3.0))

        result = all_results[:limit]

        # Phase 2: Look up phone numbers from iタウンページ
        phone_page = context.new_page()
        for i, r in enumerate(result):
            print(f"📞 電話番号を検索中... ({i+1}/{len(result)}) {r['company']}")
            r["phone"] = lookup_phone(r["company"], phone_page)
            time.sleep(random.uniform(0.5, 1.0))

        browser.close()

    print(f"✅ 完了！{len(result)}件")
    return result
