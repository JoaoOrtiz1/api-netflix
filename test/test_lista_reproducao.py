import pytest
from app import app as flask_app

@pytest.fixture
def app():
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

def test_criar_lista_reproducao_success(client, mocker):
    mocker.patch('app.verify_firebase_token', return_value='user_id_123')
    mocker.patch('app.connect_to_db')
    conn_mock = mocker.MagicMock()
    cursor_mock = mocker.MagicMock()
    cursor_mock.fetchone.return_value = None  # Simula ausência de resultado na verificação prévia
    cursor_mock.close = mocker.MagicMock()
    conn_mock.cursor.return_value = cursor_mock
    mocker.patch('app.connect_to_db', return_value=conn_mock)

    data = {'user_id': 1, 'nome_lista': 'Lista Favoritos', 'codigos_volumes': [100, 101]}
    response = client.post('/lista_reproducao', headers={'Authorization': 'Bearer valid_token'}, json=data)
    assert response.status_code == 201
    assert response.json == {'message': 'Lista de reprodução criada com sucesso!'}

def test_criar_lista_reproducao_missing_data(client):
    response = client.post('/lista_reproducao', json={})
    assert response.status_code == 400
    assert response.json == {'message': 'Token, ID do usuário, nome da lista e códigos dos volumes são obrigatórios!'}
