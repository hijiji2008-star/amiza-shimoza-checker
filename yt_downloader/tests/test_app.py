import json, os
from unittest.mock import patch
import pytest
import app as flask_app


@pytest.fixture
def client(tmp_path):
    flask_app.app.config['TESTING'] = True
    flask_app.CONFIG_PATH = str(tmp_path / 'config.json')
    with flask_app.app.test_client() as c:
        yield c


def test_get_config_default(client):
    resp = client.get('/config')
    assert resp.status_code == 200
    assert 'save_dir' in resp.get_json()


def test_update_config_nonexistent_dir(client):
    resp = client.post('/config',
                       data=json.dumps({'save_dir': '/no/such/dir/xyz'}),
                       content_type='application/json')
    assert resp.status_code == 400
    assert 'error' in resp.get_json()


def test_update_config_valid_dir(client, tmp_path):
    resp = client.post('/config',
                       data=json.dumps({'save_dir': str(tmp_path)}),
                       content_type='application/json')
    assert resp.status_code == 200
    assert resp.get_json()['save_dir'] == str(tmp_path)


def test_fetch_qualities_missing_url(client):
    resp = client.post('/fetch_qualities',
                       data=json.dumps({}),
                       content_type='application/json')
    assert resp.status_code == 400


def test_fetch_qualities_returns_list(client):
    mock_qualities = [{'height': 1080, 'label': '1080p'}]
    with patch('app.get_available_qualities', return_value=mock_qualities):
        resp = client.post('/fetch_qualities',
                           data=json.dumps({'url': 'https://youtube.com/watch?v=x'}),
                           content_type='application/json')
    assert resp.status_code == 200
    assert resp.get_json()['qualities'] == mock_qualities


def test_fetch_qualities_handles_error(client):
    with patch('app.get_available_qualities', side_effect=Exception('invalid url')):
        resp = client.post('/fetch_qualities',
                           data=json.dumps({'url': 'bad-url'}),
                           content_type='application/json')
    assert resp.status_code == 400
    assert 'error' in resp.get_json()


def test_update_ytdlp_success(client):
    with patch('app.subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        resp = client.post('/update_ytdlp')
    assert resp.status_code == 200
    assert 'message' in resp.get_json()


def test_update_ytdlp_failure(client):
    with patch('app.subprocess.run') as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = 'pip error'
        resp = client.post('/update_ytdlp')
    assert resp.status_code == 500
    assert 'error' in resp.get_json()
