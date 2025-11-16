"""
Sistema Multi-Agente com Orquestrador Inteligente + PostgreSQL
Versão 5.0 - Arquitetura Correta: Agent pensa, Plugin executa
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from datetime import datetime

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.contents import ChatHistory

from models.schemas import ChatRequest, ChatResponse
from plugins.ticket_search_plugin import TicketSearchPlugin
from plugins.ticket_processor_plugin import TicketProcessorPlugin
from plugins.database_executor_plugin import DatabaseExecutorPlugin  # NOVO
from mserver.mcp_client import MCPTicketClient
from database import db_manager
from config.logging_config import get_logger

# Importar agentes
from agents.orchestrator import OrchestratorAgent
from agents.search_agent import SearchAgentExecutor
from agents.processor_agent import ProcessorAgentExecutor
from agents.webhook_agent import WebhookAgentExecutor
from agents.llm_insert_agent import LLMInsertAgentExecutor

logger = get_logger("main")
load_dotenv()

# Variáveis globais
kernel = None
chat_history = ChatHistory()
mcp_client = None
service_id = "main"

# Agentes
orchestrator = None
search_agent = None
processor_agent = None
webhook_agent = None
llm_insert_agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa o sistema completo"""
    global kernel, chat_history, mcp_client, service_id
    global orchestrator, search_agent, processor_agent, webhook_agent, llm_insert_agent

    logger.info("=" * 80)
    logger.info("🚀 INICIALIZANDO SISTEMA MULTI-AGENTE COM POSTGRESQL")
    logger.info("📦 Versão 5.0 - Agent Pensa (LLM), Plugin Executa")
    logger.info("=" * 80)

    try:
        # 1️⃣ Conectar ao PostgreSQL
        logger.info("🐘 Etapa 1/7: Conectando ao PostgreSQL...")
        await db_manager.connect()
        logger.info("✅ PostgreSQL conectado")

        # 2️⃣ MCP Client
        logger.info("📡 Etapa 2/7: Inicializando MCP Client...")
        mcp_client = MCPTicketClient()
        await mcp_client.connect()
        logger.info("✅ MCP Client conectado")

        # 3️⃣ Kernel
        logger.info("🧠 Etapa 3/7: Inicializando Semantic Kernel...")
        kernel = Kernel()
        logger.info("✅ Kernel criado")

        # 4️⃣ AI Service
        logger.info("🤖 Etapa 4/7: Configurando OpenAI...")
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        if not api_key:
            raise ValueError("OPENAI_API_KEY não encontrada")

        kernel.add_service(
            OpenAIChatCompletion(
                service_id=service_id,
                ai_model_id=model,
                api_key=api_key
            )
        )
        logger.info(f"✅ OpenAI configurado com modelo: {model}")

        # 5️⃣ Plugins
        logger.info("🔌 Etapa 5/7: Carregando plugins...")

        # Plugins de Tickets
        kernel.add_plugin(TicketSearchPlugin(), plugin_name="TicketSearch")
        logger.info("  ✓ TicketSearch plugin carregado")

        kernel.add_plugin(TicketProcessorPlugin(), plugin_name="TicketProcessor")
        logger.info("  ✓ TicketProcessor plugin carregado")

        kernel.add_plugin(mcp_client, plugin_name="TicketWebhookMCP")
        logger.info("  ✓ TicketWebhookMCP plugin carregado")

        # Plugin de Database (NOVO - Executor Simples)
        kernel.add_plugin(DatabaseExecutorPlugin(), plugin_name="DatabaseExecutor")
        logger.info("  ✓ DatabaseExecutor plugin carregado (executor simples)")

        # 6️⃣ Inicializar Agentes
        logger.info("🎭 Etapa 6/7: Inicializando agentes especializados...")

        orchestrator = OrchestratorAgent(kernel, service_id)
        logger.info("  ✓ Orchestrator inicializado")

        search_agent = SearchAgentExecutor(kernel, service_id)
        logger.info("  ✓ SearchAgent inicializado")

        processor_agent = ProcessorAgentExecutor(kernel, service_id)
        logger.info("  ✓ ProcessorAgent inicializado")

        webhook_agent = WebhookAgentExecutor(kernel, service_id)
        logger.info("  ✓ WebhookAgent inicializado")

        llm_insert_agent = LLMInsertAgentExecutor(kernel, service_id)
        logger.info("  ✓ LLMInsertAgent inicializado (LLM pensa, plugin executa)")

        # 7️⃣ Chat History
        logger.info("💬 Etapa 7/7: Inicializando histórico...")
        chat_history.add_system_message("""Sistema multi-agente ativo com arquitetura limpa:

**Tickets:**
- SearchAgent: Busca e consulta tickets
- ProcessorAgent: Processa tickets pending
- WebhookAgent: Envia notificações via MCP

**Banco de Dados:**
- LLMInsertAgent: LLM pensa e gera SQL → DatabaseExecutor plugin executa

🎯 Arquitetura correta: Agente decide, Plugin executa.

Todos os agentes estão operacionais.""")

        logger.info("=" * 80)
        logger.info("✅ SISTEMA INICIALIZADO COM SUCESSO")
        logger.info("🎭 Agentes Ativos:")
        logger.info("   🔍 SearchAgent - Busca tickets")
        logger.info("   ⚙️ ProcessorAgent - Processa tickets")
        logger.info("   📡 WebhookAgent - Notificações MCP")
        logger.info("   🧠 LLMInsertAgent - LLM pensa, plugin executa")
        logger.info(f"🤖 Modelo: {model}")
        logger.info(f"🐘 PostgreSQL: Conectado")
        logger.info("🏗️ Arquitetura: Agent (cérebro) → Plugin (mãos)")
        logger.info("=" * 80)

        yield

    except Exception as e:
        logger.error(f"❌ ERRO NA INICIALIZAÇÃO: {str(e)}", exc_info=True)
        raise

    finally:
        logger.info("🔄 Encerrando sistema...")

        if mcp_client:
            try:
                await mcp_client.disconnect()
                logger.info("✅ MCP Client desconectado")
            except Exception as e:
                logger.error(f"❌ Erro ao desconectar MCP: {str(e)}")

        if db_manager:
            try:
                await db_manager.disconnect()
                logger.info("✅ PostgreSQL desconectado")
            except Exception as e:
                logger.error(f"❌ Erro ao desconectar PostgreSQL: {str(e)}")

        logger.info("👋 Sistema encerrado")

# Inicializar FastAPI
app = FastAPI(
    title="Sistema Multi-Agente com PostgreSQL",
    description="Arquitetura Correta: Agent pensa (LLM), Plugin executa",
    version="5.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("🌐 FastAPI inicializado")

@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "message": "Sistema Multi-Agente - Arquitetura Limpa",
        "version": "5.0.0",
        "architecture": "Agent (LLM pensa) → Plugin (executa)",
        "agents": {
            "search": "🔍 Busca tickets",
            "processor": "⚙️ Processa tickets",
            "webhook": "📡 Notificações MCP",
            "llm_insert": "🧠 Gera SQL via LLM, DatabaseExecutor executa"
        },
        "plugins": {
            "DatabaseExecutor": "🔧 Executa SQL (check_table_exists, execute_sql, execute_query)"
        },
        "database": {
            "type": "PostgreSQL",
            "schema": "ticket_system",
            "status": "connected" if db_manager.pool else "disconnected"
        },
        "status": "online",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Endpoint principal"""
    global orchestrator, search_agent, processor_agent, webhook_agent, llm_insert_agent, chat_history

    logger.info(f"💬 Nova mensagem: {request.message}")

    agent_used = "Unknown"
    final_response = ""

    try:
        chat_history.add_user_message(request.message)

        # Orquestrador decide
        routing_decision = await orchestrator.route_request(request.message, chat_history)

        agent_name = routing_decision['primary_agent']
        logger.info(f"🎯 Agente selecionado: {agent_name}")
        logger.info(f"💡 Razão: {routing_decision['reasoning']}")

        # Executar agente(s)
        if routing_decision.get('requires_multiple_agents'):
            responses = []
            context = ""

            for current_agent_name in routing_decision['agent_sequence']:
                logger.info(f"🔄 Executando {current_agent_name}...")

                response = ""

                if current_agent_name == "SearchAgent":
                    response = await search_agent.execute(request.message, chat_history)
                elif current_agent_name == "ProcessorAgent":
                    response = await processor_agent.execute(request.message, chat_history, context)
                elif current_agent_name == "WebhookAgent":
                    response = await webhook_agent.execute(request.message, chat_history, context)
                elif current_agent_name == "InsertAgent" or current_agent_name == "DatabaseAgent":
                    response = await llm_insert_agent.execute(request.message, chat_history, context)
                else:
                    response = f"❌ Agente {current_agent_name} não encontrado"
                    logger.error(f"❌ Agente desconhecido: {current_agent_name}")

                responses.append(f"**{current_agent_name}:**\n{response}")
                context += f"\nResultado de {current_agent_name}: {response}\n"

            final_response = "\n\n━━━━━━━━━━━━━━━━━━━━\n\n".join(responses)
            agent_used = "MultiAgent: " + " → ".join(routing_decision['agent_sequence'])

        else:
            agent_used = agent_name

            if agent_name == "SearchAgent":
                final_response = await search_agent.execute(request.message, chat_history)

            elif agent_name == "ProcessorAgent":
                final_response = await processor_agent.execute(request.message, chat_history)

            elif agent_name == "WebhookAgent":
                final_response = await webhook_agent.execute(request.message, chat_history)

            elif agent_name == "InsertAgent" or agent_name == "DatabaseAgent":
                final_response = await llm_insert_agent.execute(request.message, chat_history)
                agent_used = "LLMInsertAgent"

            else:
                final_response = f"❌ Agente {agent_name} não encontrado"
                agent_used = "Error"
                logger.error(f"❌ Agente desconhecido: {agent_name}")

        chat_history.add_assistant_message(final_response)
        logger.info(f"✅ Resposta gerada por: {agent_used}")

        return ChatResponse(
            response=final_response,
            agent_used=agent_used,
            session_id=request.session_id,
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"❌ Erro: {str(e)}", exc_info=True)

        error_response = f"""❌ **Erro ao Processar**

**Erro:** {str(e)}

**Mensagem:** {request.message[:100]}..."""

        return ChatResponse(
            response=error_response,
            agent_used="Error",
            session_id=request.session_id,
            timestamp=datetime.utcnow()
        )

@app.post("/chat/reset")
async def reset_chat():
    """Reset do histórico"""
    global chat_history
    chat_history = ChatHistory()
    chat_history.add_system_message("Sistema reiniciado. Agent pensa, Plugin executa.")
    return {"message": "Histórico resetado", "timestamp": datetime.utcnow().isoformat()}

@app.get("/chat/history")
async def get_chat_history():
    """Histórico de conversa"""
    history_messages = []
    for msg in chat_history.messages:
        history_messages.append({
            "role": str(msg.role),
            "content": str(msg.content),
        })

    return {
        "total_messages": len(history_messages),
        "messages": history_messages,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "architecture": "Agent (LLM) → Plugin (executor)",
        "components": {
            "orchestrator": orchestrator is not None,
            "agents": {
                "search": search_agent is not None,
                "processor": processor_agent is not None,
                "webhook": webhook_agent is not None,
                "llm_insert": llm_insert_agent is not None
            },
            "database": {
                "connected": db_manager.pool is not None,
                "host": db_manager.host,
                "database": db_manager.database
            },
            "mcp": mcp_client is not None,
            "kernel": kernel is not None
        }
    }

@app.get("/database/tables")
async def list_database_tables():
    """Lista tabelas"""
    try:
        tables = await db_manager.fetch("""
                                        SELECT table_name
                                        FROM information_schema.tables
                                        WHERE table_schema = 'ticket_system'
                                          AND table_type = 'BASE TABLE'
                                        ORDER BY table_name;
                                        """)

        tables_info = []
        for table in tables:
            table_name = table['table_name']
            count_query = f"SELECT COUNT(*) FROM ticket_system.{table_name}"
            total = await db_manager.fetchval(count_query)

            tables_info.append({
                "table_name": table_name,
                "row_count": total,
                "schema": "ticket_system"
            })

        return {
            "total_tables": len(tables_info),
            "tables": tables_info,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Erro: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/database/table/{table_name}")
async def get_table_info(table_name: str):
    """Info de uma tabela"""
    try:
        exists = await db_manager.table_exists(table_name)

        if not exists:
            raise HTTPException(status_code=404, detail=f"Tabela {table_name} não encontrada")

        columns = await db_manager.get_table_columns(table_name)
        count_query = f"SELECT COUNT(*) FROM ticket_system.{table_name}"
        total = await db_manager.fetchval(count_query)

        return {
            "table_name": table_name,
            "schema": "ticket_system",
            "exists": True,
            "columns": [
                {
                    "name": col['column_name'],
                    "type": col['data_type'],
                    "nullable": col['is_nullable'] == 'YES'
                }
                for col in columns
            ],
            "total_rows": total,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Estatísticas"""
    total_tables = 0
    total_rows = 0

    try:
        tables = await db_manager.fetch("""
                                        SELECT table_name
                                        FROM information_schema.tables
                                        WHERE table_schema = 'ticket_system'
                                          AND table_type = 'BASE TABLE';
                                        """)
        total_tables = len(tables)

        for table in tables:
            count_query = f"SELECT COUNT(*) FROM ticket_system.{table['table_name']}"
            count = await db_manager.fetchval(count_query)
            total_rows += count

    except Exception as e:
        logger.error(f"❌ Erro: {str(e)}")

    return {
        "system": {
            "version": "5.0.0",
            "architecture": "Agent (LLM pensa) → Plugin (executa)",
            "agents_count": 4,
            "plugins_count": len(kernel.plugins) if kernel else 0
        },
        "chat": {
            "total_messages": len(chat_history.messages) if chat_history else 0
        },
        "database": {
            "connected": db_manager.pool is not None,
            "total_tables": total_tables,
            "total_rows": total_rows
        },
        "agents": {
            "orchestrator": "active" if orchestrator else "inactive",
            "search": "active" if search_agent else "inactive",
            "processor": "active" if processor_agent else "inactive",
            "webhook": "active" if webhook_agent else "inactive",
            "llm_insert": "active" if llm_insert_agent else "inactive"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Iniciando servidor FastAPI...")
    logger.info("📍 URL: http://localhost:8000")
    logger.info("📚 Docs: http://localhost:8000/docs")
    logger.info("🏗️ Arquitetura: Agent (cérebro LLM) → Plugin (executor)")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")