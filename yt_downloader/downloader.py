import os
import queue
import yt_dlp


STANDARD_QUALITIES = [
    {'height': 2160, 'label': '4K (2160p)'},
    {'height': 1440, 'label': '1440p'},
    {'height': 1080, 'label': '1080p (HD)'},
    {'height': 720,  'label': '720p (HD)'},
    {'height': 480,  'label': '480p'},
    {'height': 360,  'label': '360p'},
]


def get_available_qualities(url):
    # URL が有効な YouTube 動画かを検証するだけ
    # YouTube の SABR 制限により yt-dlp はフォーマット一覧の URL を取得できないため、
    # 固定の標準画質オプションを返す。ダウンロード時に yt-dlp が実際の画質を選択する。
    opts = {'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(opts) as ydl:
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
        'format': f'bestvideo[height<={quality}]+bestaudio/bestvideo[height<={quality}]/bestvideo+bestaudio/best',
        'outtmpl': os.path.join(save_dir, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'progress_hooks': [progress_hook],
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'video')
            progress_queue.put({'status': 'finished', 'filename': f'{title}.mp4'})
    except Exception as e:
        progress_queue.put({'status': 'error', 'message': str(e)})
    finally:
        progress_queue.put(None)
