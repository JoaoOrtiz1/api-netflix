import pytest
from app import app as flask_app

@pytest.fixture
def app():
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

def test_signup_missing_data(client):
    data = {'nome': 'Usuario Teste'}  # Email e senha estão faltando
    response = client.post('/signup', json=data)
    assert response.status_code == 400
    assert response.json == {'message': 'Nome, email e senha são obrigatórios!'}

def test_signup_success(client, mocker):
    mocker.patch('app.auth.create_user', return_value=type('obj', (object,), {'uid': '12345'}))
    mocker.patch('app.auth.create_custom_token', return_value=b'token123')
    mocker.patch('app.connect_to_db')
    conn_mock = mocker.MagicMock()
    cursor_mock = mocker.MagicMock()
    conn_mock.cursor.return_value = cursor_mock
    mocker.patch('app.connect_to_db', return_value=conn_mock)

    data = {'nome': 'Usuario Teste', 'email': 'usuario@teste.com', 'senha': '123456'}
    response = client.post('/signup', json=data)
    assert response.status_code == 201
    assert 'token' in response.json

def test_signup_failure(client, mocker):
    mocker.patch('app.auth.create_user', side_effect=Exception("Erro ao criar usuário"))
    data = {'nome': 'Usuario Teste', 'email': 'usuario@teste.com', 'senha': '123456'}
    response = client.post('/signup', json=data)
    assert response.status_code == 500
    assert response.json == {'error': 'Erro ao criar usuário'}
