# Stack ELK - Prática 03: Central de Logs, Auditoria e Segurança

Implementação didática para centralizar os logs de um serviço web, pesquisar eventos e identificar uma sequência de respostas HTTP 404.

## 1. O que o sistema implementa

A solução atende ao roteiro da Prática 03 com os seguintes componentes:

| Componente | Utilização no projeto |
|---|---|
| Flask | Aplicação web de demonstração, com página inicial, rota informativa e endpoint de saúde. |
| Nginx | Servidor web de entrada e proxy para o Flask. Gera `access.log` em JSON e `error.log` em texto. |
| Filebeat | Monitora os dois arquivos de log compartilhados e encaminha os eventos pela rede Docker. |
| Elasticsearch | Indexa e armazena os eventos enviados pelo Filebeat. |
| Kibana | Permite consultar os registros no Discover e montar visualizações por código HTTP e IP de origem. |
| Docker Compose | Sobe os serviços, cria a rede virtual e configura os volumes persistentes. |

A prática permite utilizar Logstash **ou** Filebeat como coletor. Esta implementação utiliza Filebeat.

## 2. Arquitetura e fluxo dos dados

```text
Navegador / scripts de teste
            |
            v
       NGINX :8080  --------------------> access.log (JSON)
            |                             error.log (texto)
            v                                  |
       Aplicação Flask                         |
                                               v
                                         FILEBEAT
                                               |
                                      rede Docker interna
                                               |
                                               v
                                         ELASTICSEARCH
                                               |
                                               v
                                            KIBANA
                                         localhost:5601
```

O volume Docker `nginx_logs` é montado no Nginx em `/var/log/stackelk` com permissão de escrita e no Filebeat como somente leitura. O diretório separado evita os links simbólicos de stdout/stderr presentes no caminho padrão de logs da imagem oficial do Nginx. Assim, não é necessário transferir arquivos manualmente entre os containers.

O log de acesso é estruturado em JSON e contém, entre outros, os campos `timestamp`, `event.dataset`, `client.ip`, `http.request.method`, `http.response.status_code`, `url.original` e `user_agent.original`. O Filebeat interpreta cada linha como um evento independente. O log de erro é enviado como mensagem textual, identificado por `event.dataset: nginx.error`.

O endpoint `/arquivos/` é servido diretamente pelo Nginx. Quando um arquivo não existe, o Nginx registra a resposta 404 no `access.log` e a falha de abertura do arquivo no `error.log`. Essa rota é utilizada pelo gerador de tráfego para produzir a evidência experimental solicitada.

## 3. Requisitos

- Docker Engine instalado e em execução.
- Docker Compose v2 (`docker compose`).
- Aproximadamente 2 a 3 GB de memória livre para executar Elasticsearch e Kibana confortavelmente.
- Porta TCP 8080, 9200 e 5601 disponíveis no computador hospedeiro.

### Ajuste recomendado no Linux

O Elasticsearch requer um valor adequado para `vm.max_map_count`. Execute no hospedeiro:

```bash
sudo sysctl -w vm.max_map_count=262144
```

Para persistir após reinicializações:

```bash
echo 'vm.max_map_count=262144' | sudo tee /etc/sysctl.d/99-elasticsearch.conf
sudo sysctl --system
```

## 4. Inicialização

Na pasta do projeto, execute:

```bash
docker compose config
docker compose pull
docker compose up -d --build
```

Verifique o estado dos containers:

```bash
docker compose ps
```

Acompanhe a inicialização, caso necessário:

```bash
docker compose logs -f elasticsearch
docker compose logs -f kibana
docker compose logs -f filebeat
```

A aplicação estará disponível em:

- Aplicação web: <http://localhost:8080>
- Elasticsearch: <http://localhost:9200>
- Kibana: <http://localhost:5601>

A versão da Stack Elastic está fixada em `.env`, para manter Elasticsearch, Kibana e Filebeat na mesma versão. Altere `STACK_VERSION` somente se desejar atualizar os três componentes em conjunto.

## 5. Validação: tráfego legítimo e anomalia HTTP 404

O script `scripts/gerar_trafego.py` usa apenas a biblioteca padrão do Python, portanto não exige `pip install`.

### 5.1. Gerar tráfego normal

Em um terminal, dentro da pasta do projeto:

```bash
python3 scripts/gerar_trafego.py --normal-only --count 30
```

O script acessa alternadamente a página inicial, `/sobre`, `/api/status`, `/health` e o arquivo estático existente. Essas requisições devem produzir respostas HTTP 200 no log de acesso.

### 5.2. Simular a anomalia / varredura de páginas

Execute:

```bash
python3 scripts/gerar_trafego.py --attack-only --count 250 --delay 0.01
```

O script tenta acessar 250 arquivos com nomes inexistentes em `/arquivos/inexistentes/`. O Nginx responde HTTP 404 e registra a falha de abertura no `error.log`. O endereço de origem observado em `client.ip` é o endereço que o Nginx recebe na conexão; quando o teste é executado no próprio hospedeiro, ele pode aparecer como o endereço de gateway da rede Docker.

Também é possível executar as duas fases de uma vez:

```bash
python3 scripts/gerar_trafego.py --count 30 --not-found 250 --delay 0.01
```

O resultado impresso pelo script resume a quantidade de respostas por código HTTP. Após os testes, aguarde alguns segundos para o Filebeat encaminhar todos os eventos.

## 6. Consulta no Kibana

### 6.1. Criar a Data View

Execute o script auxiliar:

```bash
bash scripts/criar_data_view.sh
```

Ele aguarda o Kibana ficar disponível e cria a Data View `filebeat-*`, usando `@timestamp` como campo temporal. Também evita criar novamente a Data View se ela já existir.

### 6.2. Encontrar as falhas HTTP 404

1. Abra <http://localhost:5601>.
2. Acesse **Analytics > Discover**.
3. Selecione a Data View `filebeat-*`.
4. Ajuste o período para **Last 15 minutes** (ou um intervalo que inclua a execução do teste).
5. No campo de consulta KQL, informe:

```text
event.dataset : "nginx.access" and http.response.status_code : 404
```

6. Adicione as colunas `@timestamp`, `client.ip`, `http.response.status_code` e `url.original`.

A consulta apresenta as requisições malsucedidas, seus horários, o IP de origem e os recursos procurados. O total de documentos retornados corresponde à quantidade de eventos 404 indexados dentro do intervalo selecionado.

Para consultar as mensagens do arquivo de erro do Nginx, utilize:

```text
event.dataset : "nginx.error"
```

Para comparar o tráfego legítimo com as falhas:

```text
event.dataset : "nginx.access" and http.response.status_code >= 400
```

### 6.3. Visualização por IP (opcional, recomendado para a apresentação)

No Kibana, abra **Analytics > Visualize Library** e crie uma visualização Lens:

- Métrica: **Count of records**.
- Quebra por: **Top values of `client.ip`**.
- Filtro KQL: `event.dataset : "nginx.access" and http.response.status_code : 404`.
- Título sugerido: **Falhas HTTP 404 por IP de origem**.

Salve a visualização e adicione-a a um Dashboard. Uma segunda visualização pode apresentar a contagem de respostas por `http.response.status_code` ao longo do tempo.

## 7. Verificação dos arquivos de log

O volume é compartilhado entre Nginx e Filebeat. Para inspecionar os arquivos no container Nginx:

```bash
docker compose exec nginx sh -c 'tail -n 5 /var/log/stackelk/access.log'
docker compose exec nginx sh -c 'tail -n 5 /var/log/stackelk/error.log'
```

Para verificar o envio pelo Filebeat:

```bash
docker compose logs --since=5m filebeat
```

Para verificar o índice diretamente no Elasticsearch:

```bash
curl 'http://localhost:9200/_cat/indices?v'
```

## 8. Encerramento e limpeza

Parar os containers sem apagar os dados:

```bash
docker compose down
```

Apagar também os volumes persistentes (índices do Elasticsearch, logs e estado do Filebeat):

```bash
docker compose down -v
```

**Atenção:** `down -v` remove os dados coletados e deve ser utilizado somente quando desejar reiniciar os testes do zero.

## 9. Estrutura do projeto

```text
StackELK-Pratica03/
|-- app/
|   |-- app.py
|   |-- Dockerfile
|   `-- requirements.txt
|-- filebeat/
|   `-- filebeat.yml
|-- nginx/
|   `-- default.conf
|-- scripts/
|   |-- criar_data_view.sh
|   `-- gerar_trafego.py
|-- web/
|   `-- arquivos/
|       `-- LEIA-ME.txt
|-- .env
|-- .env.example
|-- .gitignore
|-- docker-compose.yml
`-- README.md
```

## 10. Correspondência com o enunciado da Prática 03

| Requisito | Implementação |
|---|---|
| Subir um serviço web | Flask publicado por meio do Nginx. |
| Criar `docker-compose.yml` com a Stack ELK | Elasticsearch, Filebeat e Kibana definidos no Compose. |
| Coletar `access.log` | Input `nginx-access-log` em `filebeat/filebeat.yml`. |
| Coletar `error.log` | Input `nginx-error-log` em `filebeat/filebeat.yml`. |
| Comunicação pela rede interna Docker | Filebeat envia para `http://elasticsearch:9200` na rede `stackelk-network`. |
| Gerar tráfego normal | Opção `--normal-only` do script de tráfego. |
| Gerar centenas de respostas HTTP 404 | Opção `--attack-only --count 250`. |
| Encontrar o momento, IP e quantidade de falhas | Discover com KQL e coluna `client.ip`; Lens opcional para agregação. |

## 11. Limitações e observações de segurança

Esta configuração é destinada a laboratório local e apresentação acadêmica. A autenticação e o TLS do Elasticsearch foram desabilitados para simplificar a execução local; não publique este ambiente diretamente na Internet nem o utilize em produção. As portas 9200 e 5601 ficam publicadas no hospedeiro para facilitar a demonstração. Em um ambiente real, seria necessário habilitar autenticação, TLS, controle de acesso, retenção e proteção dos dados de log.

A imagem do Nginx utiliza uma versão Alpine fixa, e as três imagens Elastic usam a mesma versão definida em `.env`. Para atualizar a Stack, atualize e valide os componentes conjuntamente.
