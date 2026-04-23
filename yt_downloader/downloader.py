import os
import queue
import re
import yt_dlp


STANDARD_QUALITIES = [
    {'height': 2160, 'label': '4K (2160p)'},
    {'height': 1440, 'label': '1440p'},
    {'height': 1080, 'label': '1080p (HD)'},
    {'height': 720,  'label': '720p (HD)'},
    {'height': 480,  'label': '480p'},
    {'height': 360,  'label': '360p'},
]

COOKIES_PATH = os.path.join(os.path.dirname(__file__), 'cookies.txt')

_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')


def _strip_ansi(s):
    return _ANSI_RE.sub('', s)


def _base_opts():
    opts = {'quiet': True, 'no_warnings': True}
    if os.path.exists(COOKIES_PATH):
        opts['cookiefile'] = COOKIES_PATH
    return opts


def has_cookies():
    return os.path.exists(COOKIES_PATH)


def get_available_qualities(url):
    with yt_dlp.YoutubeDL(_base_opts()) as ydl:
        ydl.extract_info(url, download=False)
    return STANDARD_QUALITIES


def download_video(url, quality, save_dir, progress_queue):
    def progress_hook(d):
        if d['status'] == 'downloading':
            raw = d.get('_percent_str', '0%').strip()
            try:
                pct = float(raw.replace('%', ''))
            except ValueError:
                pct = 0.0
            progress_queue.put({
                'status': 'downloading',
                'percent': pct,
                'speed': d.get('_speed_str', ''),
                'eta': d.get('_eta_str', ''),
            })

    opts = {
        **_base_opts(),
        'format': f'bestvideo[height<={quality}]+bestaudio/bestvideo[height<={quality}]/bestvideo+bestaudio/best',
        'outtmpl': os.path.join(save_dir, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'progress_hooks': [progress_hook],
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'video')
            progress_queue.put({'status': 'finished', 'filename': f'{title}.mp4'})
    except Exception as e:
        progress_queue.put({'status': 'error', 'message': _strip_ansi(str(e))})
    finally:
        progress_queue.put(None)
