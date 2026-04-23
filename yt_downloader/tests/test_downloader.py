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
