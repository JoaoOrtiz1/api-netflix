import pytest
from app import app as flask_app

@pytest.fixture
def app():
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

def test_buscar_titulos_success(client, mocker):
    mocker.patch('app.verify_firebase_token', return_value='user_id_123')
    conn_mock = mocker.MagicMock()
    cursor_mock = mocker.MagicMock()
    cursor_mock.fetchall.return_value = [
        {'vol_no_volume': 'Titulo 1', 'vol_tx_small_descricao': 'Descricao 1'},
        {'vol_no_volume': 'Titulo 2', 'vol_tx_small_descricao': 'Descricao 2'}
    ]
    cursor_mock.close = mocker.MagicMock()
    conn_mock.cursor.return_value = cursor_mock
    mocker.patch('app.connect_to_db', return_value=conn_mock)

    data = {'genero': 'Ação', 'ano_lancamento': 2021, 'classificacao': '16'}
    response = client.post('/busca', headers={'Authorization': 'Bearer valid_token'}, json=data)
    assert response.status_code == 200
    assert len(response.json) == 2
    assert response.json[0]['titulo'] == 'Titulo 1'

def test_buscar_titulos_unauthorized(client, mocker):
    mocker.patch('app.verify_firebase_token', side_effect=ValueError('Token inválido'))
    response = client.post('/busca', headers={'Authorization': 'Bearer invalid_token'}, json={})
    assert response.status_code == 401
    assert response.json == {'message': 'Token inválido'}
