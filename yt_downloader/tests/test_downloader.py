from unittest.mock import patch, MagicMock
from downloader import get_available_qualities, STANDARD_QUALITIES


def _mock_ydl(formats=None):
    m = MagicMock()
    m.__enter__ = lambda s: m
    m.__exit__ = MagicMock(return_value=False)
    m.extract_info.return_value = {'formats': formats or [], 'title': 'Test Video'}
    return m


def test_get_available_qualities_returns_standard_list():
    # YouTube SABR により動的フォーマット取得は不可。固定の標準画質一覧を返す。
    with patch('downloader.yt_dlp.YoutubeDL', return_value=_mock_ydl()):
        result = get_available_qualities('https://youtube.com/watch?v=x')
    assert result == STANDARD_QUALITIES


def test_get_available_qualities_validates_url():
    # 無効な URL は例外を投げる
    mock = _mock_ydl()
    mock.extract_info.side_effect = Exception('invalid URL')
    with patch('downloader.yt_dlp.YoutubeDL', return_value=mock):
        try:
            get_available_qualities('not-a-url')
            assert False, 'Should have raised'
        except Exception as e:
            assert 'invalid URL' in str(e)


def test_get_available_qualities_includes_hd():
    with patch('downloader.yt_dlp.YoutubeDL', return_value=_mock_ydl()):
        result = get_available_qualities('https://youtube.com/watch?v=x')
    heights = [q['height'] for q in result]
    assert 1080 in heights
    assert 720 in heights


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
