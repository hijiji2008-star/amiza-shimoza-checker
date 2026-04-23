from unittest.mock import patch, MagicMock
from downloader import get_available_qualities


def _mock_ydl(formats):
    m = MagicMock()
    m.__enter__ = lambda s: m
    m.__exit__ = MagicMock(return_value=False)
    m.extract_info.return_value = {'formats': formats, 'title': 'Test Video'}
    return m


def test_get_available_qualities_sorted_descending():
    formats = [
        {'vcodec': 'avc1', 'height': 720},
        {'vcodec': 'avc1', 'height': 1080},
        {'vcodec': 'avc1', 'height': 480},
        {'vcodec': 'none', 'height': 1080},  # audio-only -- must be excluded
    ]
    with patch('downloader.yt_dlp.YoutubeDL', return_value=_mock_ydl(formats)):
        result = get_available_qualities('https://youtube.com/watch?v=x')
    assert result == [
        {'height': 1080, 'label': '1080p'},
        {'height': 720, 'label': '720p'},
        {'height': 480, 'label': '480p'},
    ]


def test_get_available_qualities_deduplicates():
    formats = [
        {'vcodec': 'avc1', 'height': 1080},
        {'vcodec': 'vp9',  'height': 1080},  # same height, different codec
    ]
    with patch('downloader.yt_dlp.YoutubeDL', return_value=_mock_ydl(formats)):
        result = get_available_qualities('https://youtube.com/watch?v=x')
    assert len(result) == 1
    assert result[0] == {'height': 1080, 'label': '1080p'}


import queue as queue_mod
from downloader import download_video


def test_download_video_sentinel_always_last():
    """Queue must always end with None so the SSE generator can stop."""
    q = queue_mod.Queue()
    mock = _mock_ydl([])
    mock.extract_info.return_value = {'title': 'My Video', 'formats': []}
    with patch('downloader.yt_dlp.YoutubeDL', return_value=mock):
        download_video('https://youtube.com/watch?v=x', '1080', '/tmp', q)
    items = list(q.queue)
    assert items[-1] is None


def test_download_video_sends_finished_with_title():
    q = queue_mod.Queue()
    mock = _mock_ydl([])
    mock.extract_info.return_value = {'title': 'Cool Video', 'formats': []}
    with patch('downloader.yt_dlp.YoutubeDL', return_value=mock):
        download_video('https://youtube.com/watch?v=x', '1080', '/tmp', q)
    items = list(q.queue)
    finished = [i for i in items if isinstance(i, dict) and i.get('status') == 'finished']
    assert len(finished) == 1
    assert finished[0]['filename'] == 'Cool Video.mp4'


def test_download_video_sends_error_on_exception():
    q = queue_mod.Queue()
    mock = _mock_ydl([])
    mock.extract_info.side_effect = Exception('network error')
    with patch('downloader.yt_dlp.YoutubeDL', return_value=mock):
        download_video('https://youtube.com/watch?v=x', '1080', '/tmp', q)
    items = list(q.queue)
    errors = [i for i in items if isinstance(i, dict) and i.get('status') == 'error']
    assert len(errors) == 1
    assert 'network error' in errors[0]['message']
    assert items[-1] is None
