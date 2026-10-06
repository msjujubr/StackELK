import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import time
import threading
from datetime import datetime

URL_LOGIN = "http://localhost:5000/login"

def registrar_na_tela(status_code, dados_resposta, payload, ip):
    # Atualiza Status
    lbl_status_val.config(
        text=f"{status_code} ({'Sucesso' if status_code == 200 else 'Falha'})",
        fg="#2e7d32" if status_code == 200 else "#c62828"
    )

    # Exibe Resposta HTTP
    txt_resposta.config(state='normal')
    txt_resposta.delete('1.0', tk.END)
    txt_resposta.insert(tk.END, json.dumps(dados_resposta, indent=2, ensure_ascii=False))
    txt_resposta.config(state='disabled')

    # Exibe Estrutura JSON do Log ELK
    log_simulado = {
        "@timestamp": datetime.utcnow().isoformat() + "Z",
        "level": "INFO" if status_code == 200 else "WARNING",
        "ip_origem": ip or "127.0.0.1",
        "usuario_alvo": payload.get("username"),
        "status_autenticacao": "SUCESSO" if status_code == 200 else "FALHA",
        "mensagem": "Autenticação bem-sucedida" if status_code == 200 else "Falha de autenticação"
    }

    txt_log.config(state='normal')
    txt_log.insert('1.0', json.dumps(log_simulado, ensure_ascii=False) + "\n")
    txt_log.config(state='disabled')

def enviar_requisicao(usuario, senha, ip="127.0.0.1"):
    headers = {'X-Forwarded-For': ip} if ip else {}
    payload = {"username": usuario, "password": senha}

    try:
        response = requests.post(URL_LOGIN, json=payload, headers=headers, timeout=3)
        registrar_na_tela(response.status_code, response.json(), payload, ip)
    except requests.exceptions.ConnectionError:
        messagebox.showerror("Erro", "O Flask não está rodando na porta 5000.")

# Função para rodar os cenários do main.py na tela (em Thread separada para não travar a janela)
def rodar_cenario(tipo):
    def executar():
        btn_bom.config(state='disabled')
        btn_medio.config(state='disabled')
        btn_pior.config(state='disabled')

        if tipo == "bom":
            enviar_requisicao("usuario_comum", "senha123", "192.168.1.15")
            time.sleep(1)
            enviar_requisicao("usuario_comum", "senha12", "192.168.1.15")
            time.sleep(1)
            enviar_requisicao("usuario_comum", "senha123", "192.168.1.15")

        elif tipo == "medio":
            for i in range(8):
                enviar_requisicao("admin", f"senha_antiga_{i}", "192.168.1.50")
                time.sleep(0.8)

        elif tipo == "pior":
            for i in range(30): # 30 tentativas para amostragem na tela
                alvo = "admin" if i % 2 == 0 else "usuario_comum"
                enviar_requisicao(alvo, f"pwd_{i}", "203.0.113.45")
                time.sleep(0.05)

        btn_bom.config(state='normal')
        btn_medio.config(state='normal')
        btn_pior.config(state='normal')

    threading.Thread(target=executar, daemon=True).start()

def login_manual():
    usuario = entry_usuario.get().strip()
    senha = entry_senha.get()
    ip = entry_ip.get().strip()
    enviar_requisicao(usuario, senha, ip)

# --- Interface Gráfica ---
root = tk.Tk()
root.title("Central de Auditoria - ELK Stack")
root.geometry("640x700")
root.resizable(False, False)

# Painel de Automação dos 3 Casos
frame_casos = ttk.LabelFrame(root, text=" Executar Cenários Automatizados (main.py) ", padding=10)
frame_casos.pack(fill="x", padx=15, pady=5)

btn_bom = tk.Button(frame_casos, text="Caso BOM", bg="#2e7d32", fg="white", font=("Arial", 9, "bold"), command=lambda: rodar_cenario("bom"))
btn_bom.pack(side="left", expand=True, fill="x", padx=3)

btn_medio = tk.Button(frame_casos, text="Caso MÉDIO", bg="#f57c00", fg="white", font=("Arial", 9, "bold"), command=lambda: rodar_cenario("medio"))
btn_medio.pack(side="left", expand=True, fill="x", padx=3)

btn_pior = tk.Button(frame_casos, text="Caso PIOR (Força Bruta)", bg="#c62828", fg="white", font=("Arial", 9, "bold"), command=lambda: rodar_cenario("pior"))
btn_pior.pack(side="left", expand=True, fill="x", padx=3)

# Formulário Manual
frame_form = ttk.LabelFrame(root, text=" Teste Manual Individual ", padding=10)
frame_form.pack(fill="x", padx=15, pady=5)

tk.Label(frame_form, text="Usuário:").grid(row=0, column=0, sticky="w")
entry_usuario = tk.Entry(frame_form, width=25)
entry_usuario.grid(row=0, column=1, pady=2)
entry_usuario.insert(0, "usuario_comum")

tk.Label(frame_form, text="Senha:").grid(row=0, column=2, sticky="w", padx=(10, 0))
entry_senha = tk.Entry(frame_form, width=20, show="*")
entry_senha.grid(row=0, column=3, pady=2)
entry_senha.insert(0, "senha123")

tk.Label(frame_form, text="IP Simulado:").grid(row=1, column=0, sticky="w")
entry_ip = tk.Entry(frame_form, width=25)
entry_ip.grid(row=1, column=1, pady=2)
entry_ip.insert(0, "192.168.1.15")

btn_enviar = tk.Button(frame_form, text="Enviar Teste", command=login_manual, bg="#1976d2", fg="white")
btn_enviar.grid(row=1, column=2, columnspan=2, padx=10, sticky="ew")

# Resposta HTTP
frame_resposta = ttk.LabelFrame(root, text=" Última Resposta do Servidor (HTTP) ", padding=10)
frame_resposta.pack(fill="x", padx=15, pady=5)

frame_status = tk.Frame(frame_resposta)
frame_status.pack(fill="x")
tk.Label(frame_status, text="Status Code: ", font=("Arial", 9, "bold")).pack(side="left")
lbl_status_val = tk.Label(frame_status, text="Aguardando...", font=("Arial", 9))
lbl_status_val.pack(side="left")

txt_resposta = tk.Text(frame_resposta, height=3, width=70, state='disabled', bg="#f5f5f5")
txt_resposta.pack(pady=5)

# Console de Logs ELK
frame_log = ttk.LabelFrame(root, text=" Feed de Logs Gerados em Tempo Real (JSON) ", padding=10)
frame_log.pack(fill="both", expand=True, padx=15, pady=5)

txt_log = tk.Text(frame_log, height=10, width=70, state='disabled', bg="#1e1e1e", fg="#00ff00", font=("Consolas", 8))
txt_log.pack(fill="both", expand=True)

root.mainloop()