import json
from pathlib import Path

WATCHLIST_FILE = Path(__file__).parent / 'watchlist.json'


def load_watchlist(path: Path = WATCHLIST_FILE) -> dict:
    if not path.exists():
        return {'stocks': [], 'cache': {}}
    return json.loads(path.read_text(encoding='utf-8'))


def save_watchlist(data: dict, path: Path = WATCHLIST_FILE) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )


def add_stock(code: str, path: Path = WATCHLIST_FILE) -> None:
    data = load_watchlist(path)
    if code not in data['stocks']:
        data['stocks'].append(code)
    save_watchlist(data, path)


def remove_stock(code: str, path: Path = WATCHLIST_FILE) -> None:
    data = load_watchlist(path)
    data['stocks'] = [s for s in data['stocks'] if s != code]
    data['cache'].pop(code, None)
    save_watchlist(data, path)
