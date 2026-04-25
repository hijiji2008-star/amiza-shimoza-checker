import pytest
from pathlib import Path
from bs4 import BeautifulSoup
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from scraper import parse_stock_page, parse_news_page

FIXTURES = Path(__file__).parent / 'fixtures'

def get_soup(filename):
    html = (FIXTURES / filename).read_text(encoding='utf-8')
    return BeautifulSoup(html, 'html.parser')

def test_parse_stock_name():
    soup = get_soup('stock_page.html')
    result = parse_stock_page(soup, '7203')
    assert result['name'] == 'トヨタ自動車'

def test_parse_stock_price():
    soup = get_soup('stock_page.html')
    result = parse_stock_page(soup, '7203')
    assert result['price'] == 3412.0

def test_parse_per():
    soup = get_soup('stock_page.html')
    result = parse_stock_page(soup, '7203')
    assert result['per'] == 9.80

def test_parse_pbr():
    soup = get_soup('stock_page.html')
    result = parse_stock_page(soup, '7203')
    assert result['pbr'] == 1.10

def test_parse_dividend_yield():
    soup = get_soup('stock_page.html')
    result = parse_stock_page(soup, '7203')
    assert result['dividend_yield'] == 2.80

def test_parse_roe():
    soup = get_soup('stock_page.html')
    result = parse_stock_page(soup, '7203')
    assert result['roe'] == 12.40

def test_parse_market_cap():
    soup = get_soup('stock_page.html')
    result = parse_stock_page(soup, '7203')
    assert result['market_cap'] == '57.20兆円'

def test_parse_missing_metric_returns_none():
    soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
    result = parse_stock_page(soup, '9999')
    assert result['per'] is None
    assert result['price'] is None
