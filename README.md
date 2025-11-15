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