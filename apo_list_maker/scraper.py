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

# 正当な会社形態の語尾（これで終わる名前は店舗ではなく法人名）
LEGIT_ENDINGS = re.compile(r'(商店|書店|薬局|薬店|酒店|食料品店|組合|協会|農協|漁協|株式会社|有限会社|合同会社)$')
# 店舗サフィックス（スペースあり・なし両対応）
STORE_SUFFIX_RE = re.compile(r'(?:店|支店|営業所|出張所|ストアー|ショップ)$', re.IGNORECASE)

def is_store_location(name: str) -> bool:
    if LEGIT_ENDINGS.search(name):
        return False
    return bool(STORE_SUFFIX_RE.search(name))

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

        if is_store_location(company_name):
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

def parse_kyujinbox_cards(html: str, area: str, industry: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    results = []

    cards = soup.select("section.p-result_card")
    print(f"   [求人ボックス] カード数: {len(cards)}")

    for card in cards:
        company_tag = card.select_one("p.p-result_company")
        title_tag = card.select_one("h2.p-result_title--ver2 a")
        if not company_tag or not title_tag:
            continue

        company_name = company_tag.get_text(strip=True)
        job_title = title_tag.get_text(strip=True)
        href = title_tag.get("href", "")
        job_url = f"https://xn--pckua2a7gp15o89zb.com{href}" if href.startswith("/") else href

        card_text = card.get_text()
        if is_dispatch(company_name, job_title) or "派遣社員" in card_text:
            continue

        if is_store_location(company_name):
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

def lookup_phone(company_name: str, page) -> tuple[str, bool]:
    """(電話番号, 東京都内かどうか) を返す"""
    query = f"{company_name} 代表電話番号"
    url = f"https://search.yahoo.co.jp/search?p={urllib.parse.quote(query)}"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(2000)
        text = page.inner_text("body")
        match = PHONE_PATTERN.search(text)
        if match:
            return match.group(), "東京都" in text
    except Exception:
        pass
    return "—", False

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

def _collect_indeed(page, areas, industries, raw_limit):
    results = []
    for area in areas:
        for industry_name, keyword in industries.items():
            if len(results) >= raw_limit:
                break
            print(f"🔍 [Indeed] {area} × {industry_name}")
            for page_num in range(8):  # 最大8ページ
                if len(results) >= raw_limit:
                    break
                url = f"https://jp.indeed.com/jobs?q={keyword}&l={area}+東京都&start={page_num * 10}"
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(3000)
                    cards = parse_job_cards(page.content(), area, industry_name)
                    if not cards:
                        break
                    before = len(results)
                    results.extend(cards)
                    results = deduplicate(results)
                    added = len(results) - before
                    print(f"   p{page_num+1}: {added}件追加（累計{len(results)}件）")
                    if added == 0:
                        break  # 新着なし → 次の検索へ
                except Exception as e:
                    print(f"⚠️  {e}")
                    break
                time.sleep(random.uniform(1.5, 3.0))
    return results


def _collect_kyujinbox(page, areas, industries, raw_limit):
    results = []
    for area in areas:
        for industry_name, keyword in industries.items():
            if len(results) >= raw_limit:
                break
            print(f"🔍 [求人ボックス] {area} × {industry_name}")
            base = (
                f"https://xn--pckua2a7gp15o89zb.com"
                f"/{urllib.parse.quote(keyword + 'の仕事')}"
                f"-{urllib.parse.quote('東京都' + area)}"
            )
            for page_num in range(1, 9):  # 最大8ページ
                if len(results) >= raw_limit:
                    break
                url = base if page_num == 1 else f"{base}?page={page_num}"
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(3000)
                    cards = parse_kyujinbox_cards(page.content(), area, industry_name)
                    if not cards:
                        break
                    before = len(results)
                    results.extend(cards)
                    results = deduplicate(results)
                    added = len(results) - before
                    print(f"   p{page_num}: {added}件追加（累計{len(results)}件）")
                    if added == 0:
                        break  # 新着なし → 次の検索へ
                except Exception as e:
                    print(f"⚠️  {e}")
                    break
                time.sleep(random.uniform(1.5, 3.0))
    return results


def search_indeed(
    areas: list[str],
    industries: dict[str, str],
    limit: int,
) -> list[dict]:
    from playwright.sync_api import sync_playwright

    # 目標件数の6倍を上限にrawデータを収集（電話フィルター後に目標件数を確保するため）
    raw_limit = limit * 6

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

        # Phase 1: 求人収集（Indeed + 求人ボックス）
        indeed_page = context.new_page()
        all_results = _collect_indeed(indeed_page, areas, industries, raw_limit)

        kyujin_page = context.new_page()
        kyujin_results = _collect_kyujinbox(kyujin_page, areas, industries, raw_limit - len(all_results))
        all_results.extend(kyujin_results)
        all_results = deduplicate(all_results)
        print(f"\n📋 収集完了: {len(all_results)}件（raw）→ 電話番号検索開始")

        # Phase 2: 電話番号検索 → 目標件数に達したら止まる
        phone_page = context.new_page()
        final_result = []
        for i, r in enumerate(all_results):
            if len(final_result) >= limit:
                break
            remaining = limit - len(final_result)
            print(f"📞 ({i+1}/{len(all_results)}) {r['company']}  ［あと{remaining}件］")
            r["phone"], r["is_tokyo"] = lookup_phone(r["company"], phone_page)
            if r["phone"] != "—" and r["is_tokyo"]:
                final_result.append(r)
            time.sleep(random.uniform(0.5, 1.0))

        browser.close()

    print(f"✅ 完了！{len(final_result)}件（東京所在地・電話番号あり）")
    return final_result
