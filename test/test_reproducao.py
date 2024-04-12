import pytest
from app import app as flask_app

@pytest.fixture
def app():
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

def test_reproducao_success(client, mocker):
    mocker.patch('app.verify_firebase_token', return_value='user_id_123')
    mocker.patch('app.connect_to_db')
    conn_mock = mocker.MagicMock()
    cursor_mock = mocker.MagicMock()
    cursor_mock.fetchone.side_effect = [(1,), (1,)]  # Simula que o usuário e título existem
    cursor_mock.close = mocker.MagicMock()
    conn_mock.cursor.return_value = cursor_mock
    mocker.patch('app.connect_to_db', return_value=conn_mock)

    data = {'user_id': 1, 'titulo_id': 1}
    response = client.post('/reproducao', headers={'Authorization': 'Bearer valid_token'}, json=data)
    assert response.status_code == 201
    assert response.json == {'message': 'Reprodução registrada com sucesso!'}

def test_reproducao_missing_data(client):
    response = client.post('/reproducao', json={})
    assert response.status_code == 400
    assert response.json == {'message': 'ID do usuário e ID do título são obrigatórios!'}
