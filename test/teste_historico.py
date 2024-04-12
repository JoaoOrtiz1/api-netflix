import pytest
from app import app as flask_app

@pytest.fixture
def app():
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

def test_historico_success(client, mocker):
    mocker.patch('app.verify_firebase_token', return_value='user_id_123')
    conn_mock = mocker.MagicMock()
    cursor_mock = mocker.MagicMock()
    cursor_mock.fetchall.return_value = [
        {'volr_no_titulo': 'Filme A', 'volr_tp_volume': 'F', 'volr_ep_temp': None},
        {'volr_no_titulo': 'Série B', 'volr_tp_volume': 'S', 'volr_ep_temp': 'S01E01'}
    ]
    cursor_mock.close = mocker.MagicMock()
    conn_mock.cursor.return_value = cursor_mock
    mocker.patch('app.connect_to_db', return_value=conn_mock)

    response = client.get('/historico/123', headers={'Authorization': 'Bearer valid_token'})
    assert response.status_code == 200
    assert len(response.json) == 2
    assert response.json[0]['titulo'] == 'Filme A'

def test_historico_unauthorized(client, mocker):
    mocker.patch('app.verify_firebase_token', side_effect=ValueError('Token inválido'))
    response = client.get('/historico/123', headers={'Authorization': 'Bearer fake_token'})
    assert response.status_code == 401
    assert response.json == {'message': 'Token inválido'}
