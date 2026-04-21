import pytest
from scraper import is_dispatch, parse_job_cards

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
