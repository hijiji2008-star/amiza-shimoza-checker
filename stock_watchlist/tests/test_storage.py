import json
import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from storage import load_watchlist, save_watchlist, add_stock, remove_stock

@pytest.fixture
def tmp_path_watchlist(tmp_path):
    return tmp_path / 'watchlist.json'

def test_load_returns_default_when_no_file(tmp_path_watchlist):
    result = load_watchlist(tmp_path_watchlist)
    assert result == {'stocks': [], 'cache': {}}

def test_save_and_load_roundtrip(tmp_path_watchlist):
    data = {'stocks': ['7203', '6758'], 'cache': {}}
    save_watchlist(data, tmp_path_watchlist)
    assert load_watchlist(tmp_path_watchlist) == data

def test_add_stock_appends(tmp_path_watchlist):
    add_stock('7203', tmp_path_watchlist)
    data = load_watchlist(tmp_path_watchlist)
    assert '7203' in data['stocks']

def test_add_stock_no_duplicate(tmp_path_watchlist):
    add_stock('7203', tmp_path_watchlist)
    add_stock('7203', tmp_path_watchlist)
    data = load_watchlist(tmp_path_watchlist)
    assert data['stocks'].count('7203') == 1

def test_remove_stock(tmp_path_watchlist):
    add_stock('7203', tmp_path_watchlist)
    remove_stock('7203', tmp_path_watchlist)
    data = load_watchlist(tmp_path_watchlist)
    assert '7203' not in data['stocks']

def test_remove_stock_also_clears_cache(tmp_path_watchlist):
    data = {'stocks': ['7203'], 'cache': {'7203': {'name': 'トヨタ'}}}
    save_watchlist(data, tmp_path_watchlist)
    remove_stock('7203', tmp_path_watchlist)
    result = load_watchlist(tmp_path_watchlist)
    assert '7203' not in result['cache']
