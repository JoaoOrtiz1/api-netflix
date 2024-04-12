import pytest
from app import app as flask_app

@pytest.fixture
def app():
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

def test_catalog_success(client, mocker):
    mocker.patch('app.verify_firebase_token', return_value='user_id_123')
    conn_mock = mocker.MagicMock()
    cursor_mock = mocker.MagicMock()
    cursor_mock.fetchall.return_value = [('Titulo 1', 'Descricao 1'), ('Titulo 2', 'Descricao 2')]
    cursor_mock.close = mocker.MagicMock()
    conn_mock.cursor.return_value = cursor_mock
    mocker.patch('app.connect_to_db', return_value=conn_mock)

    response = client.get('/catalogo', headers={'Authorization': 'Bearer token'})
    assert response.status_code == 200
    assert len(response.json) == 2
    assert response.json[0]['titulo'] == 'Titulo 1'

def test_catalog_unauthorized(client, mocker):
    mocker.patch('app.verify_firebase_token', side_effect=ValueError('Token inválido'))
    response = client.get('/catalogo', headers={'Authorization': 'Bearer fake_token'})
    assert response.status_code == 401
    assert response.json == {'message': 'Token inválido'}
