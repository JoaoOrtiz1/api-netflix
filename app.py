from flask import Flask, request, jsonify
import requests
import firebase_admin
from firebase_admin import credentials, auth, firestore, exceptions
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

cred = credentials.Certificate("./api-netflix-py-firebase.json")  
firebase_admin.initialize_app(cred)
FIREBASE_WEB_API_KEY = 'AIzaSyAKIdt6Ua9tOxuKth3791lgf_zd_Ef8exs'

def connect_to_db():
    return psycopg2.connect(host="localhost", dbname="netflix", user="postgres", password="1997")


@app.route('/')
def index():
    return "API rodando"

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    print(data)

    if not data or 'email' not in data or 'senha' not in data or 'nome' not in data:
        return jsonify({'message': 'Nome, email e senha são obrigatórios!'}), 400

    try:
        user = auth.create_user(
            email=data['email'],
            password=data['senha'],
            display_name=data['nome']
        )

        custom_token = auth.create_custom_token(user.uid)

        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sys_usuario (usu_no_nome, usu_no_email, usu_in_status) VALUES (%s, %s, 'A')",
            (data['nome'], data['email'])
        )
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'token': custom_token.decode('utf-8')}), 201
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500
    
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or 'email' not in data or 'senha' not in data:
        return jsonify({'message': 'Email e senha são obrigatórios!'}), 400

    try:
        payload = {
            'email': data['email'],
            'password': data['senha'],
            'returnSecureToken': True
        }
        r = requests.post(f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}', json=payload)
        
        if r.status_code == 200:
            id_token = r.json()['idToken']
            return jsonify({'token': id_token}), 200
        else:
            return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

def verify_firebase_token(auth_header):
    if not auth_header or not auth_header.startswith('Bearer '):
        raise ValueError('Token de autenticação não fornecido ou formato inválido.')
    
    token = auth_header.split('Bearer ')[1]
    decoded_token = auth.verify_id_token(token)
    return decoded_token.get('uid')


@app.route('/catalogo', methods=['GET'])
def catalog():
    try:
        auth_header = request.headers.get('Authorization')
        user_id = verify_firebase_token(auth_header)

        conn = connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT vol_no_volume, vol_tx_small_descricao FROM sys_volumes WHERE vol_in_status = 'A' ORDER BY RANDOM() LIMIT 10")
        catalog_items = cur.fetchall()
        cur.close()
        conn.close()

        result = [{'titulo': item[0], 'descricao': item[1]} for item in catalog_items]
        return jsonify(result), 200
    except ValueError as ve:
        return jsonify({'message': str(ve)}), 401
    except exceptions.AuthError:
        return jsonify({'message': 'Token de autenticação inválido.'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/detalhes/<int:codigo_titulo>', methods=['GET'])
def detalhes_titulo(codigo_titulo):
    try:
        auth_header = request.headers.get('Authorization')
        user_id = verify_firebase_token(auth_header)

        conn = connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT vol_no_volume, vol_tx_sinopse, vol_tx_elenco, vol_tx_diretor, 
                   vol_av_avaliacao, vol_tp_genero, vol_nu_classificacao
            FROM sys_volumes
            WHERE vol_co_volume = %s AND vol_in_status = 'A'
        """, (codigo_titulo,))
        detalhes = cur.fetchone()
        cur.close()
        conn.close()

        if detalhes:
            result = {
                'titulo': detalhes['vol_no_volume'],
                'sinopse': detalhes['vol_tx_sinopse'],
                'elenco': detalhes['vol_tx_elenco'],
                'diretor': detalhes['vol_tx_diretor'],
                'avaliacao': detalhes['vol_av_avaliacao'],
                'genero': detalhes['vol_tp_genero'],
                'classificacao': detalhes['vol_nu_classificacao']
            }
            return jsonify(result), 200
        else:
            return jsonify({'message': 'Título não encontrado ou inativo.'}), 404
    except ValueError as ve:
        return jsonify({'message': str(ve)}), 401
    except exceptions.AuthError:
        return jsonify({'message': 'Token de autenticação inválido.'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/historico/<int:usu_co_usuario>', methods=['GET'])
def historico_visualizacao(usu_co_usuario):
    try:
        auth_header = request.headers.get('Authorization')
        user_id = verify_firebase_token(auth_header)

        if str(usu_co_usuario) != str(user_id):
            return jsonify({'message': 'Não autorizado.'}), 403

        conn = connect_to_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT volr_no_titulo, volr_tp_volume, volr_ep_temp
            FROM sys_volumes_reproducao
            WHERE usu_co_usuario = %s
            ORDER BY volr_co_reproducao DESC
        """, (usu_co_usuario,))
        historico_items = cur.fetchall()
        cur.close()
        conn.close()

        result = [{
            'titulo': item['volr_no_titulo'],
            'tipo': 'Filme' if item['volr_tp_volume'] == 'F' else 'Série',
            'episodio_temporada': item['volr_ep_temp'] if item['volr_tp_volume'] == 'S' else None
        } for item in historico_items]
        return jsonify(result), 200
    except ValueError as ve:
        return jsonify({'message': str(ve)}), 401
    except exceptions.AuthError:
        return jsonify({'message': 'Token de autenticação inválido.'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)



# CREATE TABLE sys_usuario (
#     usu_co_usuario SERIAL PRIMARY KEY,
#     usu_no_nome VARCHAR(60) NOT NULL,
#     usu_no_email VARCHAR(60) NOT NULL UNIQUE,
#     usu_in_status VARCHAR(1) NOT NULL
# );


# CREATE TABLE sys_volumes (
#     vol_co_volume SERIAL PRIMARY KEY,
#     vol_no_volume VARCHAR(45) NOT NULL,
#     vol_in_status VARCHAR(1) , -- 'A' para ativo, 'I' para inativo
#     vol_tp_volume VARCHAR(1) , -- 'F' para filme, 'S' para série
#     vol_tx_small_descricao VARCHAR(300),
#     vol_tx_sinopse VARCHAR(5000),
#     vol_tx_elenco VARCHAR(1000),
#     vol_tx_diretor VARCHAR(40),
#     vol_av_avaliacao VARCHAR(1) , -- '1' a '5' para avaliação de uma a cinco estrelas
#     vol_tp_genero VARCHAR(25),
#     vol_nu_classificacao VARCHAR(2)
# );


# CREATE TABLE sys_volumes_reproducao (
#     volr_co_reproducao SERIAL PRIMARY KEY,
#     volr_no_titulo VARCHAR(45) NOT NULL,
#     usu_co_usuario INTEGER NOT NULL,
#     volr_co_volume INTEGER NOT NULL,
#     volr_tp_volume VARCHAR(1),
#     volr_ep_temp VARCHAR(5),
#     CONSTRAINT fk_usu_co_usuario FOREIGN KEY (usu_co_usuario) 
#         REFERENCES sys_usuario (usu_co_usuario),
#     CONSTRAINT fk_volr_co_volume FOREIGN KEY (volr_co_volume) 
#         REFERENCES sys_volumes (vol_co_volume)
# );

# {
#   "type": "service_account",
#   "project_id": "api-netflix-py",
#   "private_key_id": "4a3cd36383502473b8184086233504bacb8bce9b",
#   "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCrbs6VG8rSbUm6\nFnF8F68cmkWhH+biRVibkr7FtF9ScuHsPLX5S69HlDGs7vt2xpWNgvn35IaJuuXu\nmUg21rezCbyQvh+u6+xdjtLejUWVuOrSPg81rPdZon2Vci49v6fNt25NeRsxAtkN\ni77hmFtjq+PFsF7L/+gH5kmvrAVhODib0fPazl0sWtqcOEqVJvUCMieQcuAezP+P\nHRL9Y++RIY2//nV5streKJyX1LzFQwReQLMPcEM4eG/1T6ZGystOSYyNr+hciYA0\nqVNFCve7Yaz5FhfbcyZz8wy2wFHwwKv8j2RJjv679a89nkB6a75F5KoydBN+ajML\n7o5uHGMRAgMBAAECggEAQw3KW+RNBtWcet8AcItLASMOjSFPS73YFLHnUKlmh3dM\nCv0MKICEBLlgXMX1MdYm9P0ADQgj34dtHFB0QI7nt23dhbf36JF7GHUe4dHcH93+\na1G+3T3UWgkGmgfZMmnelsZirIbsLdVxVK0OcmsHhArdwptj2OM1vLFErSPZztZr\niJudO+cwCcvdQihLJFj6gk9Sg7P8GxcPpeEqxs+ju+R6MM+tptrWRy+yNnrZX4Wt\nG0mOxAhrLEEUDYiwW/hBo9ilYOBfOWRN7jEnFUWVyY5H2oNTsvtG77F8ch9rgl90\nwgI7cWi/5vN6W2Gh/BIi4FDD/Ra7ahdDJtEAJguu6QKBgQDt4rLA7zaBElI2qQKD\nX4x9HM0wzUCJZaL183vjSoLB+hcNHiw9hsYmvkni6+qIAMz9YRFDZaeaAgmEhdHq\nkwCa1i0ITUwjKGuBzIQAiaTts6ACkCe2QgotPbJbwZOnwwSUnH1FUis5Rnjjo4fr\n6xAnE2LHAEPUJM6qkGagQ4010wKBgQC4fLDOnkqpsuRHNoZwI3x6x4QIzuqEHL2D\nqAuEvvq3/amhWxORL2EjPJeV9QwQCFIHYPxxgT7ujcZXKpNEA8HnfC7hRdMzihZz\nWLcoH9aotUkNQCxqryGmJwx1j32pLpqavwPJFYH/gTzycRTwQZRyFQKX7/067XwA\nqYIl+03BCwKBgGHjX1s1FGCYgWwsr/QPZWg2adkjHONtB1neD6TADH51wvaK6/mF\ndBSNSSovmhrM+Y1qXAg31HfzTqdRyceVJjKQ34cDB8mP4G1REyCFg3Cs8bMcTrsZ\nAccMFFDdnzzxavkcTBAyd8bh0O0bZdsWp1btC0CIQ2EQpFpbgV+BbKIxAoGBAJbJ\nK0WlMQckdNoToav0BSDhA3SjkiAq0WbTKZ707T0Gsed05jhLDkzbkFX7dEGCW3E2\nfv5SkdouvIawAK+dlpWZ9UMga+/7FEBwqTq9UxiPG0ceRW9o9sqzrcZEYoOt2KVU\nLEblMlxgCC1r6Z45K5hWvcjrWQEZ67kq0noyvSljAoGBAJA37kPdmPkqY1lDlfja\nmeu1eaHZlCnfEAKwHbE0NqFw7LkGN6XEoqjGNcrg/bZVIxaHRG8kLnAi46JL60HU\nx5uOlJCk9suXmYb5yR9f++gOsOL0IxxyGXkhqPpuotdBETWOOd6nYnbX/MwL9aFj\n2QvJd8AjwybyHrKMtMl0U6b5\n-----END PRIVATE KEY-----\n",
#   "client_email": "firebase-adminsdk-drery@api-netflix-py.iam.gserviceaccount.com",
#   "client_id": "112612701982819493896",
#   "auth_uri": "https://accounts.google.com/o/oauth2/auth",
#   "token_uri": "https://oauth2.googleapis.com/token",
#   "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
#   "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-drery%40api-netflix-py.iam.gserviceaccount.com",
#   "universe_domain": "googleapis.com"
# }
