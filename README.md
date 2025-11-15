# 🎫 Sistema Multi-Agente de Tickets com MCP

Sistema inteligente de gerenciamento de tickets usando **Semantic Kernel**, **FastAPI** e **Model Context Protocol (MCP)**.

## 📋 Características

- ✅ **3 Agentes Especializados**: Search, Processor e Webhook
- ✅ **Orquestração Automática**: AgentGroupChat decide qual agente usar
- ✅ **MCP Integration**: Integração externa via Model Context Protocol
- ✅ **Logging Completo**: Sistema de logs em múltiplos formatos
- ✅ **RESTful API**: FastAPI com documentação automática

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

### 3. Rode o projeto
```bash
python main.py
```

### 4. Testes com curl
```curl
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
```