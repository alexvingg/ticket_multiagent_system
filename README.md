# 🎫 Sistema Multi-Agente de Tickets com MCP

Sistema inteligente de gerenciamento de tickets usando **Semantic Kernel**, **FastAPI** e **Model Context Protocol (MCP)**.

## 📋 Características

- ✅ **3 Agentes Especializados**: Search, Processor e Webhook
- ✅ **Orquestração Automática**: AgentGroupChat decide qual agente usar
- ✅ **MCP Integration**: Integração externa via Model Context Protocol
- ✅ **Logging Completo**: Sistema de logs em múltiplos formatos
- ✅ **RESTful API**: FastAPI com documentação automática
- ✅ **Plugin de Database (genérico)**: Plugin para criar tabelas e inserir novos dados no banco (uso genérico, não específico para tickets)
- ✅ ** Agente: LLM Insert Agent (genérico)**: Agente responsável por gerar instruções via LLM para criação de tabelas e inserção/atualizacao/delecao de dados genéricos no banco — não é um agente de CRUD de tickets

## .env — configuração necessária

Antes de rodar a aplicação crie um arquivo `.env` a partir do template fornecido e preencha as variáveis necessárias (principalmente a chave do OpenAI):

```bash
cp .env.template .env
# Depois abra .env e preencha OPENAI_API_KEY e outros valores (POSTGRES_* se não usar docker-compose)
```

- `OPENAI_API_KEY` — chave obrigatória para o serviço de LLM (preencha com sua chave do OpenAI ou do provedor configurado).
- `OPENAI_MODEL` — modelo padrão (ex.: gpt-4).
- `POSTGRES_*` — configurações do banco caso queira conectar a um Postgres externo em vez do docker-compose.

## Docker Compose para PostgreSQL

O repositório já inclui um `docker-compose.yml` pronto para subir um container PostgreSQL configurado para este projeto. Não é necessário modificar o compose para usar o banco local — basta executá-lo quando quiser levantar um Postgres de desenvolvimento.

```bash
# Exemplo (executa o Postgres em background):
docker-compose up -d
```

> Observação: o `docker-compose.yml` já mapeia o volume de dados e aplica o script de inicialização `database/init.sql` automaticamente. Use-o para desenvolvimento local seguro; não exponha o banco em produção sem hardening.

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone git@github.com:alexvingg/ticket_multiagent_system.git
cd ticket_multiagent_system
```

### 2. Configure o projeto
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> Observação: se você usar o plugin de database, verifique o arquivo `database/init.sql` e as configurações em `database/connection.py`. Configure as variáveis de ambiente do Postgres (ex.: PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE) ou use o `docker-compose.yml` provido para levantar um Postgres local.

### 3. Rode o projeto
```bash
python main.py
```

## 🔧 Exemplos de uso (curl)

```bash
# Teste 1: Apenas busca (SearchAgent)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Me mostra as informações do ticket TKT-001"}'

# Teste 2: Apenas processamento (ProcessorAgent)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Resolve o ticket TKT-003"}'

# Teste 3: Apenas webhook (WebhookAgent)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Manda uma notificação do ticket TKT-001"}'

# Teste 4: Múltiplos agentes (SearchAgent → ProcessorAgent)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Busca o ticket TKT-005, se estiver pending processa ele"}'

# Teste 5: Workflow completo (3 agentes)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Pega o ticket TKT-007, processa e envia pro sistema externo"}'

# Teste 6: Criar tabela e inserir dados via LLM Insert Agent (USO GENÉRICO, não ticket)
# Exemplo: pede para criar uma tabela de 'events' e inserir um registro
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Crie uma tabela chamada events (id, title, description, occurred_at = vai ser automatico com a data atual) e insira um registro com title: \"Login error\" e description: \"Falha ao autenticar usuário\""}'

# Teste 7: Pedir ao LLM para montar a query e executar (recomendado)
# Em vez de enviar SQL bruto, envie uma solicitação em linguagem natural — o LLM construirá a SQL apropriada e o plugin `DatabaseExecutor` irá executá-la.
# Exemplo: peça para ver o último evento ou buscar por critérios sem escrever SQL você mesmo
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Quero ver o último registro da tabela events"}'

# Teste 8: Pedir ao LLM para montar a query e executar (recomendado)
# Exemplo: Atualize a descricao de um registro
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Atualize o registro da tabela events onde o titulo é Login error para definir a descrição como \"Usuario não encontrado\""}'

```