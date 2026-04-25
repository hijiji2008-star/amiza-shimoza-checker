import re
from bs4 import BeautifulSoup


def _to_float(text):
    """'3,412', '9.80倍', '2.80%' などから数値を抽出する"""
    if not text:
        return None
    cleaned = re.sub(r'[^\d.]', '', text.replace(',', ''))
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def _find_by_label(soup, label):
    """テーブルの th テキストに label を含む行の td テキストを返す"""
    for th in soup.find_all('th'):
        if label in th.get_text():
            td = th.find_next_sibling('td')
            if td:
                return td.get_text(strip=True)
    return None


def parse_stock_page(soup, code):
    """Yahoo!ファイナンス 株価ページの BeautifulSoup から株データを返す"""
    h1 = soup.find('h1')
    if h1:
        name = h1.get_text(strip=True)
    else:
        title = soup.find('title')
        name_match = re.match(r'^(.+?)[\(（]', title.get_text()) if title else None
        name = name_match.group(1).strip() if name_match else code

    price = None
    for tag in soup.find_all(['span', 'div', 'td', 'p']):
        text = tag.get_text(strip=True).replace(',', '')
        if re.match(r'^\d{3,6}$', text):
            val = float(text)
            if 100 <= val <= 999999:
                price = val
                break

    change = None
    change_pct = None
    for tag in soup.find_all(['span', 'td']):
        text = tag.get_text(strip=True)
        if re.match(r'^[+\-±][\d,]+$', text):
            change = _to_float(text)
        if re.match(r'^\([+\-±][\d.]+%\)$', text):
            pct_text = re.sub(r'[^\d.\-+]', '', text)
            try:
                change_pct = float(pct_text)
            except ValueError:
                pass

    return {
        'code': code,
        'name': name,
        'price': price,
        'change': change,
        'change_pct': change_pct,
        'per': _to_float(_find_by_label(soup, 'PER')),
        'pbr': _to_float(_find_by_label(soup, 'PBR')),
        'dividend_yield': _to_float(_find_by_label(soup, '配当利回り')),
        'roe': _to_float(_find_by_label(soup, 'ROE')),
        'market_cap': _find_by_label(soup, '時価総額'),
        'news': [],
    }


def parse_news_page(soup):
    """Yahoo!ファイナンス ニュースページから見出しリストを返す (stub for Task 4)"""
    return []
