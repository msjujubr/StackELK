import logging
import json
import os
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# Garantir que o diretório de logs exista
os.makedirs("logs", exist_ok=True)

# Configuração do Logger Customizado para JSON
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
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("logs/auth_audit.log")
file_handler.setFormatter(ELKJsonFormatter())
logger.addHandler(file_handler)

# Banco de dados simulado
USUARIOS_VALIDOS = {
    "usuario_comum": "senha123",
    "admin": "admin_super_secreto"
}

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', 'anonimo')
    password = data.get('password', '')
    ip = request.remote_addr

    if username in USUARIOS_VALIDOS and USUARIOS_VALIDOS[username] == password:
        logger.info("Autenticação bem-sucedida", extra={"ip": ip, "username": username, "status": "SUCESSO"})
        return jsonify({"mensagem": "Bem-vindo!"}), 200
    else:
        logger.warning("Falha de autenticação", extra={"ip": ip, "username": username, "status": "FALHA"})
        return jsonify({"erro": "Credenciais inválidas"}), 401

if __name__ == '__main__':
    # Rodando na porta 5000
    app.run(host='0.0.0.0', port=5000)