import json
import os
import platform
import queue
import subprocess
import sys
import threading

from flask import Flask, Response, jsonify, render_template, request

from downloader import get_available_qualities, download_video, has_cookies

app = Flask(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
DEFAULT_SAVE_DIR = os.path.expanduser('~/Downloads')


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {'save_dir': DEFAULT_SAVE_DIR}


def save_config(data):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(data, f)


@app.route('/')
def index():
    config = load_config()
    return render_template('index.html', save_dir=config['save_dir'])


@app.route('/config', methods=['GET'])
def get_config():
    config = load_config()
    config['cookies_ok'] = has_cookies()
    return jsonify(config)


@app.route('/config', methods=['POST'])
def update_config():
    data = request.get_json()
    save_dir = (data.get('save_dir') or '').strip()
    if not save_dir:
        return jsonify({'error': '保存先を入力してください'}), 400
    if not os.path.isdir(save_dir):
        return jsonify({'error': f'フォルダが存在しません: {save_dir}'}), 400
    save_config({'save_dir': save_dir})
    return jsonify({'save_dir': save_dir})


@app.route('/fetch_qualities', methods=['POST'])
def fetch_qualities():
    data = request.get_json()
    url = (data.get('url') or '').strip()
    if not url:
        return jsonify({'error': 'URLを入力してください'}), 400
    try:
        qualities = get_available_qualities(url)
        return jsonify({'qualities': qualities})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/download')
def download():
    url = (request.args.get('url') or '').strip()
    quality = request.args.get('quality', '1080')
    if not url:
        return jsonify({'error': 'URLが必要です'}), 400

    config = load_config()
    progress_queue = queue.Queue()

    threading.Thread(
        target=download_video,
        args=(url, quality, config['save_dir'], progress_queue),
        daemon=True,
    ).start()

    def generate():
        while True:
            item = progress_queue.get()
            if item is None:
                break
            yield f'data: {json.dumps(item, ensure_ascii=False)}\n\n'

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )


@app.route('/update_ytdlp', methods=['POST'])
def update_ytdlp():
    try:
        if platform.system() == 'Darwin':
            cmd = ['brew', 'upgrade', 'yt-dlp']
        else:
            cmd = [sys.executable, '-m', 'pip', 'install', '--upgrade', 'yt-dlp']
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            return jsonify({'message': 'yt-dlp を最新版に更新しました'})
        return jsonify({'error': result.stderr or result.stdout}), 500
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'タイムアウト（120秒）'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(port=5002, debug=True)
