import webbrowser
from pathlib import Path
from flask import Flask, render_template, request, jsonify

from storage import load_watchlist, save_watchlist, add_stock, remove_stock
from scraper import fetch_stock_data, fetch_all

app = Flask(__name__)
WATCHLIST_FILE = Path(__file__).parent / 'watchlist.json'


@app.route('/')
def index():
    data = load_watchlist(WATCHLIST_FILE)
    stocks = [
        data['cache'].get(code, {'code': code, 'name': code, 'error': 'キャッシュなし'})
        for code in data['stocks']
    ]
    return render_template('index.html', stocks=stocks, view='dashboard')


@app.route('/stock/<code>')
def stock_detail(code):
    data = load_watchlist(WATCHLIST_FILE)
    stock = data['cache'].get(code, {'code': code, 'error': 'データがありません'})
    return render_template('index.html', stock=stock, view='detail')


@app.route('/api/watchlist/add', methods=['POST'])
def api_add():
    code = request.json.get('code', '').strip().upper()
    if not code:
        return jsonify({'error': 'code is required'}), 400
    try:
        stock_data = fetch_stock_data(code)
        add_stock(code, WATCHLIST_FILE)
        wl = load_watchlist(WATCHLIST_FILE)
        wl['cache'][code] = stock_data
        save_watchlist(wl, WATCHLIST_FILE)
        return jsonify({'ok': True, 'stock': stock_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/watchlist/<code>', methods=['DELETE'])
def api_remove(code):
    remove_stock(code, WATCHLIST_FILE)
    return jsonify({'ok': True})


@app.route('/api/refresh', methods=['POST'])
def api_refresh():
    wl = load_watchlist(WATCHLIST_FILE)
    if not wl['stocks']:
        return jsonify({'ok': True, 'updated': 0})
    results = fetch_all(wl['stocks'])
    wl['cache'].update(results)
    save_watchlist(wl, WATCHLIST_FILE)
    return jsonify({'ok': True, 'updated': len(results)})


@app.route('/api/stock/<code>')
def api_stock(code):
    wl = load_watchlist(WATCHLIST_FILE)
    stock = wl['cache'].get(code)
    if not stock:
        return jsonify({'error': 'not found'}), 404
    return jsonify(stock)


if __name__ == '__main__':
    import os
    if not os.environ.get('WERKZEUG_RUN_MAIN'):
        webbrowser.open('http://localhost:5003')
    app.run(port=5003, debug=True)
