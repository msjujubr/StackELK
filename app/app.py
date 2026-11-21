from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

HOME = """<!doctype html>
<html lang=\"pt-BR\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Stack ELK - Prática 03</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 850px; margin: 3rem auto;
           padding: 0 1.2rem; line-height: 1.6; color: #202938; }
    h1 { color: #075985; }
    code { background: #eef2f7; padding: .15rem .35rem; border-radius: 4px; }
    .box { background: #f0f9ff; border-left: 4px solid #0284c7; padding: 1rem; }
    a { color: #0369a1; }
  </style>
</head>
<body>
  <h1>Aplicação de demonstração - Stack ELK</h1>
  <p>Este serviço Flask está publicado por meio do Nginx. As requisições são
     registradas nos arquivos <code>access.log</code> e <code>error.log</code>,
     coletados pelo Filebeat e enviados ao Elasticsearch.</p>
  <div class="box">
    <strong>Rotas disponíveis</strong>
    <ul>
      <li><a href="/">Página inicial</a></li>
      <li><a href="/sobre">Sobre o projeto</a></li>
      <li><a href="/api/status">API de status</a></li>
      <li><a href="/health">Saúde da aplicação Flask</a></li>
      <li><a href="/arquivos/LEIA-ME.txt">Arquivo estático servido pelo Nginx</a></li>
    </ul>
  </div>
  <p>Para a validação da Prática 03, o script de teste também requisita centenas
     de arquivos inexistentes em <code>/arquivos/</code>, gerando respostas HTTP 404.</p>
</body>
</html>"""


@app.get("/")
def index():
    return render_template_string(HOME)


@app.get("/sobre")
def about():
    return (
        "<h1>Sobre</h1><p>Ambiente didático de centralização e análise de logs "
        "com Nginx, Filebeat, Elasticsearch e Kibana.</p>",
        200,
        {"Content-Type": "text/html; charset=utf-8"},
    )


@app.get("/api/status")
def api_status():
    return jsonify(status="online", projeto="Stack ELK - Prática 03")


@app.get("/health")
def health():
    return jsonify(status="ok"), 200


@app.errorhandler(404)
def not_found(_error):
    return jsonify(erro="Recurso não encontrado", status=404), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
