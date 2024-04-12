import pytest
from app import app as flask_app

@pytest.fixture
def app():
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

def test_detalhes_titulo_success(client, mocker):
    mocker.patch('app.verify_firebase_token', return_value='user_id_123')
    conn_mock = mocker.MagicMock()
    cursor_mock = mocker.MagicMock()
    cursor_mock.fetchone.return_value = {
        'vol_no_volume': 'Titulo 1', 
        'vol_tx_sinopse': 'Sinopse detalhada',
        'vol_tx_elenco': 'Elenco principal',
        'vol_tx_diretor': 'Diretor',
        'vol_av_avaliacao': '5 estrelas',
        'vol_tp_genero': 'Ação',
        'vol_nu_classificacao': '18+'
    }
    cursor_mock.close = mocker.MagicMock()
    conn_mock.cursor.return_value = cursor_mock
    mocker.patch('app.connect_to_db', return_value=conn_mock)

    response = client.get('/detalhes/1', headers={'Authorization': 'Bearer valid_token'})
    assert response.status_code == 200
    assert response.json['titulo'] == 'Titulo 1'

def test_detalhes_titulo_not_found(client, mocker):
    mocker.patch('app.verify_firebase_token', return_value='user_id_123')
    conn_mock = mocker.MagicMock()
    cursor_mock = mocker.MagicMock()
    cursor_mock.fetchone.return_value = None
    cursor_mock.close = mocker.MagicMock()
    conn_mock.cursor.return_value = cursor_mock
    mocker.patch('app.connect_to_db', return_value=conn_mock)

    response = client.get('/detalhes/999', headers={'Authorization': 'Bearer valid_token'})
    assert response.status_code == 404
    assert response.json == {'message': 'Título não encontrado ou inativo.'}
