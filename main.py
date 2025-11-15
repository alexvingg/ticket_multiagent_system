"""
Sistema Multi-Agente com Orquestrador Inteligente
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
from mserver.mcp_client import MCPTicketClient
from config.logging_config import get_logger

# Importar agentes
from agents.orchestrator import OrchestratorAgent
from agents.search_agent import SearchAgentExecutor
from agents.processor_agent import ProcessorAgentExecutor
from agents.webhook_agent import WebhookAgentExecutor

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa o sistema"""
    global kernel, chat_history, mcp_client, service_id
    global orchestrator, search_agent, processor_agent, webhook_agent

    logger.info("=" * 80)
    logger.info("🚀 INICIALIZANDO SISTEMA MULTI-AGENTE COM ORQUESTRADOR")
    logger.info("=" * 80)

    try:
        # 1️⃣ MCP Client
        logger.info("📡 Etapa 1/6: Inicializando MCP Client...")
        mcp_client = MCPTicketClient()
        await mcp_client.connect()

        # 2️⃣ Kernel
        logger.info("🧠 Etapa 2/6: Inicializando Semantic Kernel...")
        kernel = Kernel()

        # 3️⃣ AI Service
        logger.info("🤖 Etapa 3/6: Configurando OpenAI...")
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-4")

        if not api_key:
            raise ValueError("OPENAI_API_KEY não encontrada")

        kernel.add_service(
            OpenAIChatCompletion(
                service_id=service_id,
                ai_model_id=model,
                api_key=api_key
            )
        )

        # 4️⃣ Plugins
        logger.info("🔌 Etapa 4/6: Carregando plugins...")
        kernel.add_plugin(TicketSearchPlugin(), plugin_name="TicketSearch")
        kernel.add_plugin(TicketProcessorPlugin(), plugin_name="TicketProcessor")
        kernel.add_plugin(mcp_client, plugin_name="TicketWebhookMCP")

        # 5️⃣ Inicializar Agentes
        logger.info("🎭 Etapa 5/6: Inicializando agentes especializados...")

        orchestrator = OrchestratorAgent(kernel, service_id)
        search_agent = SearchAgentExecutor(kernel, service_id)
        processor_agent = ProcessorAgentExecutor(kernel, service_id)
        webhook_agent = WebhookAgentExecutor(kernel, service_id)

        logger.info("  ✓ Orchestrator inicializado")
        logger.info("  ✓ SearchAgent inicializado")
        logger.info("  ✓ ProcessorAgent inicializado")
        logger.info("  ✓ WebhookAgent inicializado")

        # 6️⃣ Chat History
        logger.info("💬 Etapa 6/6: Inicializando histórico...")
        chat_history.add_system_message("Sistema multi-agente com orquestrador inteligente ativo.")

        logger.info("=" * 80)
        logger.info("✅ SISTEMA INICIALIZADO - ORQUESTRADOR ATIVO")
        logger.info("=" * 80)

        yield

    except Exception as e:
        logger.error(f"❌ ERRO: {str(e)}", exc_info=True)
        raise
    finally:
        if mcp_client:
            await mcp_client.disconnect()

app = FastAPI(
    title="Sistema Multi-Agente com Orquestrador Inteligente",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Sistema Multi-Agente com Orquestrador Inteligente",
        "version": "3.0.0",
        "architecture": "Orchestrator → [SearchAgent | ProcessorAgent | WebhookAgent]",
        "agents": {
            "orchestrator": "Analisa requisição e roteia para agente apropriado",
            "search": "Busca e consulta tickets",
            "processor": "Processa tickets pendentes",
            "webhook": "Envia notificações via MCP"
        },
        "status": "online"
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Endpoint com roteamento inteligente via orquestrador"""
    global orchestrator, search_agent, processor_agent, webhook_agent, chat_history

    logger.info(f"💬 Nova mensagem: {request.message}")

    try:
        # Adicionar mensagem ao histórico
        chat_history.add_user_message(request.message)

        # 1️⃣ ORQUESTRADOR decide qual(is) agente(s) usar
        routing_decision = await orchestrator.route_request(request.message, chat_history)

        agent_name = routing_decision['primary_agent']
        logger.info(f"🎯 Agente selecionado: {agent_name}")
        logger.info(f"💡 Razão: {routing_decision['reasoning']}")

        # 2️⃣ EXECUTAR agente(s)
        if routing_decision.get('requires_multiple_agents'):
            # Workflow com múltiplos agentes
            responses = []
            context = ""

            for agent_name in routing_decision['agent_sequence']:
                logger.info(f"🔄 Executando {agent_name}...")

                if agent_name == "SearchAgent":
                    response = await search_agent.execute(request.message, chat_history)
                elif agent_name == "ProcessorAgent":
                    response = await processor_agent.execute(request.message, chat_history, context)
                elif agent_name == "WebhookAgent":
                    response = await webhook_agent.execute(request.message, chat_history, context)
                else:
                    response = f"❌ Agente {agent_name} não encontrado"

                responses.append(f"**{agent_name}:**\n{response}")
                context += f"\nResultado de {agent_name}: {response}\n"

            final_response = "\n\n".join(responses)
            agent_used = "MultiAgent: " + " → ".join(routing_decision['agent_sequence'])

        else:
            # Executar apenas um agente
            if agent_name == "SearchAgent":
                final_response = await search_agent.execute(request.message, chat_history)
            elif agent_name == "ProcessorAgent":
                final_response = await processor_agent.execute(request.message, chat_history)
            elif agent_name == "WebhookAgent":
                final_response = await webhook_agent.execute(request.message, chat_history)
            else:
                final_response = f"❌ Agente {agent_name} não encontrado"

            agent_used = agent_name

        # Adicionar resposta ao histórico
        chat_history.add_assistant_message(final_response)

        return ChatResponse(
            response=final_response,
            agent_used=agent_used,
            session_id=request.session_id,
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"❌ Erro: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/reset")
async def reset_chat():
    global chat_history
    chat_history = ChatHistory()
    chat_history.add_system_message("Sistema reiniciado.")
    return {"message": "Histórico resetado"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "orchestrator": orchestrator is not None,
        "agents": {
            "search": search_agent is not None,
            "processor": processor_agent is not None,
            "webhook": webhook_agent is not None
        },
        "mcp": mcp_client is not None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)