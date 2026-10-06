# Central de Logs, Auditoria e Segurança

![Python](https://img.shields.io/badge/Linguagem-Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Framework-Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-blue?style=for-the-badge)
![Elasticsearch](https://img.shields.io/badge/Ferramenta-Elasticsearch-005571?style=for-the-badge&logo=elasticsearch&logoColor=white)
![Kibana](https://img.shields.io/badge/Ferramenta-Kibana-005571?style=for-the-badge&logo=kibana&logoColor=white)
![Filebeat](https://img.shields.io/badge/Ferramenta-Filebeat-005571?style=for-the-badge&logo=elasticbeat&logoColor=white)
![Docker](https://img.shields.io/badge/Container-Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![JSON](https://img.shields.io/badge/Formato-JSON-000000?style=for-the-badge&logo=json&logoColor=white)

<!-- sudo apt install python3-tk -->

**Problemática:** Uma aplicação web possui um sistema de autenticação utilizado por diferentes usuários. Em determinado momento, o servidor começa a receber diversas tentativas consecutivas de login, principalmente para uma conta específica.

A equipe responsável precisa investigar os registros para determinar:

- Qual IP realizou as tentativas;
- Qual usuário foi alvo;
- Quando as tentativas ocorreram;
- Quantas tentativas foram realizadas;
- Quantas foram bem-sucedidas ou malsucedidas;
- Se existe um comportamento anômalo.

A análise direta dos arquivos de log torna essa investigação pouco prática. Dessa forma, os eventos são centralizados utilizando a *Stack ELK*.

**Este projeto implementa uma infraestrutura de centralização e análise de logs utilizando a *Stack ELK*, com o objetivo de identificar possíveis comportamentos anômalos relacionados a múltiplas tentativas de autenticação malsucedidas em uma aplicação web.**

A prática envolve:
- Implementação de uma aplicação web com **Flask**;
- Registro estruturado das tentativas de autenticação;
- Geração dos eventos em formato **JSON**;
- Coleta dos logs utilizando **Filebeat**;
- Armazenamento e indexação utilizando **Elasticsearch**;
- Análise dos eventos utilizando **Kibana**;
- Identificação de possíveis comportamentos anômalos.




## Arquitetura

A infraestrutura da prática segue o seguinte fluxo:

```text
┌────────────────────┐
│    Navegador /     │
│      Cliente       │
└─────────┬──────────┘
          │
          │ HTTP
          ▼
┌────────────────────┐
│  Aplicação Flask   │
│                    │
│  Autenticação      │
│  +                 │
│  Logs JSON         │
└─────────┬──────────┘
          │
          │ arquivo de log
          ▼
┌────────────────────┐
│      Filebeat      │
│                    │
│ Coleta dos eventos │
└─────────┬──────────┘
          │
          │ eventos
          ▼
┌────────────────────┐
│   Elasticsearch    │
│                    │
│ Armazenamento e    │
│ indexação          │
└─────────┬──────────┘
          │
          │ consultas
          ▼
┌────────────────────┐
│       Kibana       │
│                    │
│ Filtros, gráficos  │
│ e análise          │
└────────────────────┘
```


## Ambiente e Instalação
Recomenda-se utilizar um ambiente virtual Python.

1. Criar o ambiente virtual
python3 -m venv .venv
2. Ativar o ambiente virtual

No Linux:

source .venv/bin/activate

No Windows:

.venv\Scripts\Activate.ps1
3. Instalar as dependências
pip install flask requests

Caso seja necessário atualizar o pip:

python -m pip install --upgrade pip
▶️ Execução da Aplicação

Com o ambiente virtual ativado, execute:

python app.py

A aplicação Flask ficará disponível, por padrão, em:

http://127.0.0.1:5000

A página de autenticação poderá então ser acessada pelo navegador.


## Execução

A aplicação foi desenvolvida utilizando Python e o framework Flask. A página de autenticação permite tanto usuários previamente definidos quanto em tempo real, realizem tentativas de login.

Cada tentativa deverá gera um evento estruturado em formato JSON. Por exemplo:

```
{
    "timestamp": "2026-10-05T10:30:00",
    "ip": "127.0.0.1",
    "usuario": "usuario_invasor",
    "sucesso": false,
    "evento": "login"
}
```

Os campos registrados permitem que o Kibana posteriormente realize filtros e agregações individuais.

### Usuários de Teste

A prática utiliza dois usuários principais:

| Usuário | Função |
| :--- | :--- |
| `usuario_comum` | Realização de autenticações legítimas |
| `usuario_invasor` | Utilizado para simulação de tentativas malsucedidas |

## Geração dos Logs

A cada tentativa de autenticação, a aplicação deverá registrar um evento no arquivo de logs.

Exemplo de evento de login bem-sucedido:

{
    "timestamp": "2026-10-05T10:30:00",
    "ip": "127.0.0.1",
    "usuario": "usuario_comum",
    "sucesso": true,
    "evento": "login"
}

Exemplo de tentativa malsucedida:

{
    "timestamp": "2026-10-05T10:31:00",
    "ip": "127.0.0.1",
    "usuario": "usuario_invasor",
    "sucesso": false,
    "evento": "login"
}

O formato JSON permite que cada informação seja tratada como um campo independente pelo Elasticsearch e pelo Kibana.

🧪 Cenários de Teste

Serão realizados três cenários para representar diferentes níveis de atividade.

🟢 Caso 1 — Comportamento Bom

Representa um comportamento normal de utilização da aplicação.

O usuário usuario_comum realizará autenticações legítimas, podendo também cometer alguns erros simples de digitação.

Exemplo
usuario_comum → login correto
usuario_comum → senha incorreta
usuario_comum → login correto

Características esperadas:

Poucas tentativas;
Predominância de autenticações bem-sucedidas;
Usuário comum como alvo;
Ausência de grande quantidade de tentativas consecutivas;
Comportamento compatível com um usuário normal.
Objetivo

Estabelecer um comportamento de referência para comparação com os demais cenários.

🟡 Caso 2 — Comportamento Médio

Representa uma situação que merece investigação.

Serão realizadas algumas tentativas consecutivas de autenticação malsucedida utilizando a conta usuario_invasor.

Exemplo:

usuario_invasor → senha incorreta
usuario_invasor → senha incorreta
usuario_invasor → senha incorreta
usuario_invasor → senha incorreta
usuario_invasor → login correto

Características esperadas:

Aumento da quantidade de falhas;
Várias tentativas direcionadas ao mesmo usuário;
Tentativas concentradas em um intervalo relativamente curto;
Possível comportamento anômalo.
Objetivo

Identificar no Kibana que a frequência de falhas está acima do comportamento esperado.

🔴 Caso 3 — Pior Caso

Representa um comportamento claramente anômalo.

Serão simuladas diversas tentativas consecutivas de autenticação malsucedida contra usuario_invasor.

Exemplo:

usuario_invasor → senha incorreta
usuario_invasor → senha incorreta
usuario_invasor → senha incorreta
usuario_invasor → senha incorreta
usuario_invasor → senha incorreta
usuario_invasor → senha incorreta
usuario_invasor → senha incorreta
usuario_invasor → senha incorreta
usuario_invasor → senha incorreta
usuario_invasor → senha incorreta

Características esperadas:

Grande quantidade de falhas;
Mesmo usuário sendo repetidamente alvo;
Tentativas concentradas em curto intervalo;
Alta proporção de autenticações malsucedidas;
Possível comportamento automatizado ou tentativa de ataque.
Objetivo

Demonstrar como a centralização dos logs permite detectar rapidamente um comportamento anômalo.

Observação: todos os testes devem ser realizados exclusivamente no ambiente controlado da prática, utilizando usuários e credenciais fictícios.

📊 Análise com Kibana

Após a coleta dos eventos pelo Filebeat e sua indexação no Elasticsearch, o Kibana será utilizado para analisar os registros.

Algumas análises que podem ser realizadas:

Tentativas por usuário

Identificar quais usuários receberam mais tentativas de autenticação.

usuario_comum       → 3 tentativas
usuario_invasor     → 10 tentativas
Tentativas por IP

Identificar o endereço IP responsável pelas requisições.

127.0.0.1 → 13 tentativas
Sucesso x Falha

Comparar a quantidade de autenticações bem-sucedidas e malsucedidas.

Sucesso  → 3
Falha    → 10
Tentativas ao longo do tempo

Criar uma visualização temporal para identificar concentrações de tentativas.

Quantidade
   │
10 │             █
 8 │             █
 6 │             █
 4 │       █     █
 2 │ █     █     █
 0 └──────────────────
       Bom   Médio  Pior



| Indicador                  | Comportamento normal | Possível anomalia  |
| -------------------------- | -------------------- | ------------------ |
| Quantidade de tentativas   | Baixa                | Alta               |
| Falhas consecutivas        | Poucas               | Muitas             |
| Usuário alvo               | Variado              | Concentrado        |
| Intervalo entre tentativas | Irregular            | Muito curto        |
| Taxa de falhas             | Baixa                | Elevada            |
| IP                         | Uso normal           | Muitas requisições |


A combinação desses indicadores pode auxiliar na identificação de um possível comportamento suspeito.

🛠️ Tecnologias Utilizadas
Python — linguagem de programação;
Flask — desenvolvimento da aplicação web;
Requests — realização de requisições HTTP durante os testes;
Filebeat — coleta e encaminhamento dos logs;
Elasticsearch — armazenamento e indexação dos eventos;
Kibana — consulta, filtragem e visualização dos dados;
JSON — formato estruturado dos eventos.


.
├── app.py
├── requirements.txt
├── logs/
│   └── auth.log
├── templates/
│   └── login.html
├── static/
│   └── style.css
├── filebeat/
│   └── filebeat.yml
└── README.md

Flask
requests

pip install -r requirements.txt


🔐 Segurança e Escopo

Esta prática possui finalidade educacional e deve ser executada exclusivamente em um ambiente controlado.

As tentativas de autenticação são simuladas contra a própria aplicação desenvolvida para a prática. Não devem ser realizadas tentativas de autenticação contra sistemas, servidores ou contas de terceiros.

✅ Resultados Esperados

Ao final da prática, espera-se que seja possível:

Implementar uma aplicação web com autenticação;
Gerar logs estruturados em JSON;
Centralizar os eventos utilizando o Filebeat;
Armazenar os eventos no Elasticsearch;
Consultar os eventos no Kibana;
Identificar usuários e IPs envolvidos;
Contabilizar tentativas de autenticação;
Diferenciar autenticações bem-sucedidas e malsucedidas;
Comparar os cenários bom, médio e pior;
Identificar indícios de comportamento anômalo por meio da análise dos logs.
📚 Conclusão

A prática demonstra a importância da centralização de logs para auditoria e segurança de aplicações web.

Em vez de analisar manualmente arquivos de log, a Stack ELK permite centralizar, indexar, consultar e visualizar grandes quantidades de eventos, facilitando a identificação de padrões suspeitos.

A comparação entre os três cenários permite observar como o aumento da frequência de tentativas malsucedidas pode ser utilizado como indicador de um possível comportamento anômalo.
