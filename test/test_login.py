import pytest
from app import app as flask_app

@pytest.fixture
def app():
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

def test_login_missing_data(client):
    data = {'email': 'usuario@teste.com'}  # Senha está faltando
    response = client.post('/login', json=data)
    assert response.status_code == 400
    assert response.json == {'message': 'Email e senha são obrigatórios!'}

def test_login_success(client, mocker):
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'idToken': 'token123'}
    mocker.patch('requests.post', return_value=mock_response)

    data = {'email': 'usuario@teste.com', 'senha': '123456'}
    response = client.post('/login', json=data)
    assert response.status_code == 200
    assert response.json == {'token': 'token123'}

def test_login_failure(client, mocker):
    mock_response = mocker.MagicMock()
    mock_response.status_code = 401
    mock_response.json.return_value = {'error': 'Credenciais inválidas'}
    mocker.patch('requests.post', return_value=mock_response)

    data = {'email': 'usuario@teste.com', 'senha': '123456'}
    response = client.post('/login', json=data)
    assert response.status_code == 401
    assert response.json == {'error': 'Credenciais inválidas'}
