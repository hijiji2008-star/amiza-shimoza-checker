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
