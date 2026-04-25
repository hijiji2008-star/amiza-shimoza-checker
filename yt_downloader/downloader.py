import os
import platform
import queue
import re
import subprocess
import sys

COOKIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookies.txt')

STANDARD_QUALITIES = [
    {'height': 2160, 'label': '4K (2160p)'},
    {'height': 1440, 'label': '1440p'},
    {'height': 1080, 'label': '1080p (HD)'},
    {'height': 720,  'label': '720p (HD)'},
    {'height': 480,  'label': '480p'},
    {'height': 360,  'label': '360p'},
]

_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')
_PROGRESS_RE = re.compile(r'\[download\]\s+([\d.]+)%\s+of\s+\S+\s+at\s+(\S+)\s+ETA\s+(\S+)')


def _strip_ansi(s):
    return _ANSI_RE.sub('', s)


def _base_cmd():
    cmd = [sys.executable, '-m', 'yt_dlp']
    if os.path.exists(COOKIES_FILE):
        cmd += ['--cookies', COOKIES_FILE]
    elif platform.system() == 'Windows':
        # Windows では Chrome のクッキーを直接読める
        cmd += ['--cookies-from-browser', 'chrome']
    return cmd


def has_cookies():
    # Mac: cookies.txt 必須（Chrome v10 暗号化でブラウザ直読み不可）
    # Windows: Chrome ブラウザクッキー直読み可能、または cookies.txt を使用
    return os.path.exists(COOKIES_FILE) or platform.system() == 'Windows'


def get_available_qualities(url):
    result = subprocess.run(
        _base_cmd() + ['--print', 'title', url],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        err = _strip_ansi((result.stderr or result.stdout).strip())
        raise Exception(err)
    return STANDARD_QUALITIES


def download_video(url, quality, save_dir, progress_queue):
    fmt = f'best[height<={quality}][ext=mp4]/best[height<={quality}]/best[ext=mp4]/best'
    cmd = _base_cmd() + [
        '-f', fmt,
        '-o', os.path.join(save_dir, '%(title)s.%(ext)s'),
        '--merge-output-format', 'mp4',
        '--newline',
        url,
    ]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        filename = 'video.mp4'
        error_msg = None

        for line in proc.stdout:
            line = _strip_ansi(line.rstrip())
            m = _PROGRESS_RE.search(line)
            if m:
                progress_queue.put({
                    'status': 'downloading',
                    'percent': float(m.group(1)),
                    'speed': m.group(2),
                    'eta': m.group(3),
                })
            elif '[download] Destination:' in line:
                filename = os.path.basename(line.split('Destination: ', 1)[-1])
            elif line.startswith('ERROR:'):
                error_msg = line[6:].strip()

        proc.wait()
        if proc.returncode == 0:
            progress_queue.put({'status': 'finished', 'filename': filename})
        else:
            progress_queue.put({'status': 'error', 'message': error_msg or 'ダウンロードに失敗しました'})
    except Exception as e:
        progress_queue.put({'status': 'error', 'message': _strip_ansi(str(e))})
    finally:
        progress_queue.put(None)
