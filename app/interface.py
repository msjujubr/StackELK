import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import time
import threading
from datetime import datetime, timezone

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


# --- Consulta de auditoria no Elasticsearch ---
ELASTICSEARCH_URL = "http://localhost:9200"
INDICE_AUDITORIA = "auditoria-auth-*"

def abrir_consulta_auditoria():
    """Abre uma janela que consulta os eventos indexados no Elasticsearch."""
    janela = tk.Toplevel(root)
    janela.title("Pesquisa de Auditoria - Falhas de Autenticação")
    janela.geometry("1050x650")
    janela.minsize(900, 520)

    filtros = ttk.LabelFrame(janela, text="Filtros da pesquisa", padding=10)
    filtros.pack(fill="x", padx=10, pady=8)

    tk.Label(filtros, text="Período:").grid(row=0, column=0, sticky="w", padx=4, pady=4)
    periodo_var = tk.StringVar(value="Última 1 hora")
    periodo = ttk.Combobox(
        filtros, textvariable=periodo_var, state="readonly", width=18,
        values=("Últimos 15 minutos", "Última 1 hora", "Últimas 24 horas", "Últimos 7 dias")
    )
    periodo.grid(row=0, column=1, padx=4, pady=4)

    tk.Label(filtros, text="IP de origem:").grid(row=0, column=2, sticky="w", padx=4, pady=4)
    ip_var = tk.StringVar()
    ip_entry = ttk.Entry(filtros, textvariable=ip_var, width=20)
    ip_entry.grid(row=0, column=3, padx=4, pady=4)

    tk.Label(filtros, text="Usuário:").grid(row=0, column=4, sticky="w", padx=4, pady=4)
    usuario_var = tk.StringVar()
    usuario_entry = ttk.Entry(filtros, textvariable=usuario_var, width=18)
    usuario_entry.grid(row=0, column=5, padx=4, pady=4)

    resumo_var = tk.StringVar(value="Informe os filtros e clique em Pesquisar.")
    ttk.Label(janela, textvariable=resumo_var).pack(anchor="w", padx=14, pady=(0, 5))

    corpo = ttk.Panedwindow(janela, orient="vertical")
    corpo.pack(fill="both", expand=True, padx=10, pady=5)

    quadro_ips = ttk.LabelFrame(corpo, text="Resumo por IP (somente falhas)", padding=5)
    quadro_eventos = ttk.LabelFrame(corpo, text="Eventos encontrados", padding=5)
    corpo.add(quadro_ips, weight=1)
    corpo.add(quadro_eventos, weight=2)

    colunas_ips = ("ip", "falhas", "primeira", "ultima")
    tabela_ips = ttk.Treeview(quadro_ips, columns=colunas_ips, show="headings", height=7)
    for col, titulo, largura in (
        ("ip", "IP de origem", 180),
        ("falhas", "Quantidade de falhas", 150),
        ("primeira", "Primeira tentativa", 250),
        ("ultima", "Última tentativa", 250),
    ):
        tabela_ips.heading(col, text=titulo)
        tabela_ips.column(col, width=largura, anchor="w")
    barra_ips = ttk.Scrollbar(quadro_ips, orient="vertical", command=tabela_ips.yview)
    tabela_ips.configure(yscrollcommand=barra_ips.set)
    tabela_ips.pack(side="left", fill="both", expand=True)
    barra_ips.pack(side="right", fill="y")

    colunas_eventos = ("data", "ip", "usuario", "status", "mensagem")
    tabela_eventos = ttk.Treeview(quadro_eventos, columns=colunas_eventos, show="headings", height=10)
    for col, titulo, largura in (
        ("data", "Data/hora", 190),
        ("ip", "IP de origem", 140),
        ("usuario", "Usuário", 140),
        ("status", "Resultado", 100),
        ("mensagem", "Evento", 300),
    ):
        tabela_eventos.heading(col, text=titulo)
        tabela_eventos.column(col, width=largura, anchor="w")
    barra_eventos = ttk.Scrollbar(quadro_eventos, orient="vertical", command=tabela_eventos.yview)
    tabela_eventos.configure(yscrollcommand=barra_eventos.set)
    tabela_eventos.pack(side="left", fill="both", expand=True)
    barra_eventos.pack(side="right", fill="y")

    def pesquisar():
        for tabela in (tabela_ips, tabela_eventos):
            for item in tabela.get_children():
                tabela.delete(item)

        periodos = {
            "Últimos 15 minutos": "now-15m",
            "Última 1 hora": "now-1h",
            "Últimas 24 horas": "now-24h",
            "Últimos 7 dias": "now-7d",
        }
        filtros_query = [
            {"term": {"status_autenticacao": "FALHA"}},
            {"range": {"@timestamp": {"gte": periodos[periodo_var.get()], "lte": "now"}}},
        ]
        ip_digitado = ip_var.get().strip()
        usuario_digitado = usuario_var.get().strip()
        if ip_digitado:
            filtros_query.append({"wildcard": {"ip_origem": {"value": f"*{ip_digitado}*"}}})
        if usuario_digitado:
            filtros_query.append({"wildcard": {"usuario_alvo": {"value": f"*{usuario_digitado}*"}}})

        consulta = {
            "size": 500,
            "track_total_hits": True,
            "query": {"bool": {"filter": filtros_query}},
            "sort": [{"@timestamp": {"order": "asc"}}],
            "_source": ["@timestamp", "ip_origem", "usuario_alvo", "status_autenticacao", "mensagem"],
            "aggs": {
                "por_ip": {
                    "terms": {"field": "ip_origem", "size": 100, "order": {"_count": "desc"}},
                    "aggs": {
                        "primeira_tentativa": {"min": {"field": "@timestamp"}},
                        "ultima_tentativa": {"max": {"field": "@timestamp"}}
                    }
                }
            }
        }

        try:
            resposta = requests.post(
                f"{ELASTICSEARCH_URL}/{INDICE_AUDITORIA}/_search",
                json=consulta,
                timeout=5
            )
            resposta.raise_for_status()
            dados = resposta.json()
        except requests.exceptions.RequestException as erro:
            messagebox.showerror(
                "Erro na consulta",
                "Não foi possível consultar o Elasticsearch em localhost:9200.\n"
                "Confira se os containers estão ativos e se os logs já foram indexados.\n\n"
                f"Detalhes: {erro}",
                parent=janela
            )
            return
        except (ValueError, KeyError) as erro:
            messagebox.showerror("Erro de resposta", f"Resposta inesperada do Elasticsearch: {erro}", parent=janela)
            return

        total = dados.get("hits", {}).get("total", {})
        quantidade = total.get("value", 0) if isinstance(total, dict) else total
        hits = dados.get("hits", {}).get("hits", [])
        agregacoes = dados.get("aggregations", {}).get("por_ip", {}).get("buckets", [])

        def formatar_data(valor):
            if valor is None:
                return "-"
            try:
                return datetime.fromtimestamp(valor / 1000, tz=timezone.utc).astimezone().strftime("%d/%m/%Y %H:%M:%S")
            except (ValueError, TypeError, OSError):
                return str(valor)

        for bucket in agregacoes:
            primeira = bucket.get("primeira_tentativa", {}).get("value")
            ultima = bucket.get("ultima_tentativa", {}).get("value")
            tabela_ips.insert("", "end", values=(
                bucket.get("key", "IP desconhecido"),
                bucket.get("doc_count", 0),
                formatar_data(primeira),
                formatar_data(ultima)
            ))

        for hit in hits:
            evento = hit.get("_source", {})
            tabela_eventos.insert("", "end", values=(
                evento.get("@timestamp", "-"),
                evento.get("ip_origem", "-"),
                evento.get("usuario_alvo", "-"),
                evento.get("status_autenticacao", "-"),
                evento.get("mensagem", "-")
            ))

        resumo_var.set(
            f"{quantidade} falha(s) encontrada(s) no período selecionado. "
            f"IPs distintos: {len(agregacoes)}. A tabela de eventos mostra até 500 registros."
        )

    ttk.Button(filtros, text="Pesquisar", command=pesquisar).grid(row=0, column=6, padx=8, pady=4)
    ttk.Button(filtros, text="Limpar", command=lambda: (ip_var.set(""), usuario_var.set(""), pesquisar())).grid(
        row=0, column=7, padx=4, pady=4
    )
    janela.bind("<Return>", lambda _evento: pesquisar())
    pesquisar()


# --- Interface Gráfica ---
root = tk.Tk()
root.title("Central de Auditoria - ELK Stack")
root.geometry("640x700")
root.resizable(False, False)

# A consulta lê os eventos indexados no Elasticsearch, não o JSON apenas exibido na tela.
btn_consulta = tk.Button(
    root,
    text="Pesquisar falhas e IPs",
    command=abrir_consulta_auditoria,
    bg="#263238",
    fg="white",
    font=("Arial", 10, "bold")
)
btn_consulta.pack(fill="x", padx=15, pady=(2, 6))

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