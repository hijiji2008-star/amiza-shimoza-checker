import os
import queue
import yt_dlp


def get_available_qualities(url):
    opts = {'quiet': True, 'skip_download': True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    seen = set()
    qualities = []
    for f in info.get('formats', []):
        if f.get('vcodec') not in (None, 'none') and f.get('height'):
            h = f['height']
            if h not in seen:
                seen.add(h)
                qualities.append({'height': h, 'label': f'{h}p'})
    qualities.sort(key=lambda x: x['height'], reverse=True)
    return qualities


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
        'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
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
