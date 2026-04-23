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
