import requests
import time
import random

URL = "http://localhost:5000/login"

def tentar_login(username, password, simulacao_ip=None):
    headers = {'X-Forwarded-For': simulacao_ip} if simulacao_ip else {}
    try:
        requests.post(URL, json={"username": username, "password": password}, headers=headers)
    except requests.exceptions.ConnectionError:
        print("Erro: Flask")

def cenario_bom():
    print("BOM CASO: Usuario legitimo com pequenos erros normais.")
    # Usuario acerta de primeira
    tentar_login("usuario_comum", "senha123", "192.168.1.15")
    time.sleep(1)
    # Usuario erra a senha por digitacao, mas acerta em seguida
    tentar_login("usuario_comum", "senha12", "192.168.1.15")
    time.sleep(2)
    tentar_login("usuario_comum", "senha123", "192.168.1.15")
    print("    -> Pronto.\n")

def cenario_medio():
    print("MEDIO CASO: Comportamento esquecido/insistencia moderada.")
    # Alguém tentando lembrar a senha do admin ou um script lento
    ips = ["192.168.1.50", "192.168.1.51"]
    for i in range(8):
        tentar_login("admin", f"senha_antiga_{i}", random.choice(ips))
        time.sleep(1.5) # Tempo espacado, nao dispara alarmes agressivos de rate limit
    print("    -> Pronto.\n")

def cenario_pior():
    print("PIOR CASO: Ataque pelo usuario_invasor.")
    # Invasor tenta dezenas de senhas rapidamente contra o admin e o usuario_comum
    ip_invasor = "203.0.113.45" # IP externo/malicioso
    
    for i in range(60):
        alvo = "admin" if i % 2 == 0 else "usuario_comum"
        tentar_login(alvo, f"pwd_{i}_{random.randint(1000,9999)}", ip_invasor)
        time.sleep(0.05) # Alta frequencia caracteriza anomalia grave
    print("    -> Pronto.\n")

if __name__ == "__main__":
    cenario_bom()
    time.sleep(3)
    cenario_medio()
    time.sleep(3)
    print("Simulacao finalizada")