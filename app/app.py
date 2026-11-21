import logging
import json
import os
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

DIRETORIO_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRETORIO_LOGS = os.path.join(DIRETORIO_PROJETO, "logs")
os.makedirs(DIRETORIO_LOGS, exist_ok=True)

# Configuracao do Logger para JSON
class ELKJsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "@timestamp": datetime.utcnow().isoformat() + "Z", # Formato ISO8601 exigido pelo Elastic
            "level": record.levelname,
            "ip_origem": record.__dict__.get("ip", "unknown"),
            "usuario_alvo": record.__dict__.get("username", "unknown"),
            "status_autenticacao": record.__dict__.get("status", "unknown"),
            "mensagem": record.getMessage()
        }
        return json.dumps(log_record)

logger = logging.getLogger("auditoria_auth")
print("LOGGER:", logger.name, logger.handlers)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(os.path.join(DIRETORIO_LOGS, "auth_audit_v3.log"))
file_handler.setFormatter(ELKJsonFormatter())
logger.addHandler(file_handler)

# Banco de dados ficticio
USUARIOS_VALIDOS = {
    "usuario_comum": "senha123",
    "admin": "admin_super_secreto"
}

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', 'anonimo')
    password = data.get('password', '')
    # Para simulacao local
    ip = request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip()
    print("REQUISICAO RECEBIDA:", username)
    if username in USUARIOS_VALIDOS and USUARIOS_VALIDOS[username] == password:
        logger.info("Autenticacao bem-sucedida", extra={"ip": ip, "username": username, "status": "SUCESSO"})
        return jsonify({"mensagem": "Bem-vindo!"}), 200
    else:
        logger.warning("Falha de autenticacao", extra={"ip": ip, "username": username, "status": "FALHA"})
        return jsonify({"erro": "Credenciais inválidas"}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)