"""
Sistema Multi-Agente de Tickets com Semantic Kernel 1.38.0, FastAPI e MCP
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from datetime import datetime

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import KernelArguments
from semantic_kernel.prompt_template import PromptTemplateConfig

from models.schemas import ChatRequest, ChatResponse
from plugins.ticket_search_plugin import TicketSearchPlugin
from plugins.ticket_processor_plugin import TicketProcessorPlugin
from mserver.mcp_client import MCPTicketClient
from config.logging_config import get_logger

# Configurar logging
logger = get_logger("main")

# Carregar variáveis de ambiente
load_dotenv()
logger.info("🔧 Variáveis de ambiente carregadas")

# Variáveis globais
kernel = None
chat_history = ChatHistory()
mcp_client = None
service_id = "main"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa o sistema na startup e limpa no shutdown"""
    global kernel, chat_history, mcp_client, service_id

    logger.info("=" * 80)
    logger.info("🚀 INICIALIZANDO SISTEMA MULTI-AGENTE DE TICKETS")
    logger.info(f"📦 Semantic Kernel v1.38.0")
    logger.info("=" * 80)

    try:
        # 1️⃣ Inicializar MCP Client
        logger.info("📡 Etapa 1/5: Inicializando MCP Client...")
        mcp_client = MCPTicketClient()
        await mcp_client.connect()
        logger.info("✅ MCP Client conectado")

        # 2️⃣ Inicializar Kernel
        logger.info("🧠 Etapa 2/5: Inicializando Semantic Kernel...")
        kernel = Kernel()
        logger.info("✅ Kernel criado")

        # 3️⃣ Adicionar serviço de AI
        logger.info("🤖 Etapa 3/5: Configurando OpenAI...")
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-4")

        if not api_key:
            logger.error("❌ OPENAI_API_KEY não configurada no .env")
            raise ValueError("OPENAI_API_KEY não encontrada")

        chat_service = OpenAIChatCompletion(
            service_id=service_id,
            ai_model_id=model,
            api_key=api_key
        )

        kernel.add_service(chat_service)
        logger.info(f"✅ OpenAI configurado com modelo: {model}")

        # 4️⃣ Adicionar plugins
        logger.info("🔌 Etapa 4/5: Carregando plugins...")

        kernel.add_plugin(
            TicketSearchPlugin(),
            plugin_name="TicketSearch"
        )
        logger.info("  ✓ TicketSearch plugin carregado")

        kernel.add_plugin(
            TicketProcessorPlugin(),
            plugin_name="TicketProcessor"
        )
        logger.info("  ✓ TicketProcessor plugin carregado")

        kernel.add_plugin(
            mcp_client,
            plugin_name="TicketWebhookMCP"
        )
        logger.info("  ✓ TicketWebhookMCP plugin carregado")

        # 5️⃣ Inicializar histórico de chat
        logger.info("💬 Etapa 5/5: Inicializando histórico de chat...")

        system_message = """Você é um assistente especializado em gerenciamento de tickets com as seguintes capacidades:

**🔍 BUSCAR TICKETS (Plugin: TicketSearch)**
- search_ticket: Busca um ticket específico pelo número
- list_all_tickets: Lista todos os tickets do sistema

**⚙️ PROCESSAR TICKETS (Plugin: TicketProcessor)**
- process_pending_ticket: Processa tickets com status 'pending' e muda para 'solved'
- list_pending_tickets: Lista apenas tickets pendentes
- ⚠️ REGRA: Só pode processar tickets com status 'pending'

**📡 ENVIAR WEBHOOKS (Plugin: TicketWebhookMCP)**
- send_ticket_webhook: Envia webhook com status 'done'
- send_custom_ticket_webhook: Envia webhook com status customizado
- check_webhook_health: Verifica se o webhook está funcionando

**INSTRUÇÕES:**
1. Analise a solicitação do usuário cuidadosamente
2. Use as funções apropriadas para cada tarefa
3. Para processar tickets, SEMPRE verifique se o status é 'pending' primeiro
4. Forneça respostas claras e bem formatadas
5. Se houver erros, explique o que aconteceu

Seja objetivo, profissional e útil."""

        chat_history.add_system_message(system_message)
        logger.info("✅ Histórico de chat inicializado")

        logger.info("=" * 80)
        logger.info("✅ SISTEMA INICIALIZADO COM SUCESSO")
        logger.info(f"🔌 Plugins: TicketSearch, TicketProcessor, TicketWebhookMCP")
        logger.info(f"📡 MCP Server: Conectado")
        logger.info(f"🤖 Modelo: {model}")
        logger.info("=" * 80)

        yield

    except Exception as e:
        logger.error(f"❌ ERRO NA INICIALIZAÇÃO: {str(e)}", exc_info=True)
        raise

    finally:
        # Cleanup
        logger.info("🔄 Encerrando sistema...")
        if mcp_client:
            try:
                await mcp_client.disconnect()
                logger.info("✅ MCP Client desconectado")
            except Exception as e:
                logger.error(f"❌ Erro ao desconectar MCP: {str(e)}")

        logger.info("👋 Sistema encerrado")

# Inicializar FastAPI
app = FastAPI(
    title="Sistema Multi-Agente de Tickets com MCP",
    description="API com Semantic Kernel 1.38.0 e Model Context Protocol para gerenciar tickets",
    version="2.2.0",
    lifespan=lifespan
)

# Configurar CORS
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
    """Endpoint raiz com informações do sistema"""
    logger.info("📍 GET / - Root endpoint acessado")
    return {
        "message": "Sistema Multi-Agente de Tickets com MCP",
        "version": "2.2.0",
        "semantic_kernel_version": "1.38.0",
        "capabilities": [
            "🔍 Buscar tickets e listar todos os tickets",
            "⚙️ Processar tickets pendentes (pending → solved)",
            "📡 Enviar webhooks via MCP para sistemas externos"
        ],
        "plugins": [
            {
                "name": "TicketSearch",
                "functions": ["search_ticket", "list_all_tickets"]
            },
            {
                "name": "TicketProcessor",
                "functions": ["process_pending_ticket", "list_pending_tickets"]
            },
            {
                "name": "TicketWebhookMCP",
                "functions": ["send_ticket_webhook", "send_custom_ticket_webhook", "check_webhook_health"]
            }
        ],
        "integration": "MCP (Model Context Protocol) v1.21.1",
        "status": "online",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint principal - processa mensagens com function calling automático
    """
    global kernel, chat_history, service_id

    logger.info(f"💬 Nova mensagem recebida - Session: {request.session_id}")
    logger.info(f"📝 Mensagem: {request.message}")

    if not kernel:
        logger.error("❌ Sistema não inicializado")
        raise HTTPException(status_code=500, detail="Sistema não inicializado")

    try:
        # Adicionar mensagem do usuário ao histórico
        chat_history.add_user_message(request.message)
        logger.debug("✅ Mensagem adicionada ao histórico")

        # Obter serviço de chat
        chat_service = kernel.get_service(service_id)

        # Configurar execution settings com function calling automático
        execution_settings = kernel.get_prompt_execution_settings_from_service_id(
            service_id=service_id
        )

        # Configurar auto function calling
        execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto(
            filters={"excluded_plugins": []}
        )

        logger.info("🤖 Invocando modelo com function calling automático...")

        # Invocar o chat completion com function calling
        result = await chat_service.get_chat_message_contents(
            chat_history=chat_history,
            settings=execution_settings,
            kernel=kernel
        )

        if result and len(result) > 0:
            response_message = result[0]
            response_text = str(response_message.content)

            logger.info(f"✅ Resposta gerada ({len(response_text)} caracteres)")
            logger.debug(f"📤 Resposta: {response_text[:200]}...")

            # Adicionar resposta ao histórico
            chat_history.add_assistant_message(response_text)

            # Detectar qual tipo de operação foi realizada
            agent_used = "MultiAgent"
            message_lower = request.message.lower()

            if any(word in message_lower for word in ["busca", "procura", "status", "informação", "mostrar"]):
                agent_used = "SearchAgent"
            elif any(word in message_lower for word in ["processa", "resolver", "finaliza", "solved"]):
                agent_used = "ProcessorAgent"
            elif any(word in message_lower for word in ["webhook", "notifica", "envia", "integra"]):
                agent_used = "WebhookAgent"

            return ChatResponse(
                response=response_text,
                agent_used=agent_used,
                session_id=request.session_id,
                timestamp=datetime.utcnow()
            )

        logger.error("❌ Nenhuma resposta gerada pelo modelo")
        raise HTTPException(status_code=500, detail="Nenhuma resposta gerada")

    except Exception as e:
        logger.error(f"❌ Erro ao processar chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@app.post("/chat/reset")
async def reset_chat():
    """Reset do histórico de conversa"""
    global chat_history

    logger.info("🔄 Resetando histórico de chat")

    chat_history = ChatHistory()

    # Re-adicionar mensagem de sistema
    system_message = """Você é um assistente especializado em gerenciamento de tickets.

Use as funções disponíveis nos plugins:
- TicketSearch: para buscar e listar tickets
- TicketProcessor: para processar tickets pendentes
- TicketWebhookMCP: para enviar notificações

Sempre forneça respostas claras e bem formatadas."""

    chat_history.add_system_message(system_message)

    return {
        "message": "Histórico resetado com sucesso",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/chat/history")
async def get_chat_history():
    """Retorna o histórico de conversa"""
    logger.info("📜 Histórico de chat solicitado")

    history_messages = []

    for msg in chat_history.messages:
        history_messages.append({
            "role": str(msg.role),
            "content": str(msg.content),
            "name": msg.name if hasattr(msg, 'name') else None
        })

    return {
        "total_messages": len(history_messages),
        "messages": history_messages,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check completo do sistema"""
    logger.info("🏥 Health check solicitado")

    plugins_list = []
    if kernel:
        for plugin in kernel.plugins:
            functions = list(plugin.functions.keys())
            plugins_list.append({
                "name": plugin.name,
                "functions_count": len(functions),
                "functions": functions
            })

    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "versions": {
            "semantic_kernel": "1.38.0",
            "fastapi": "0.121.2",
            "mcp": "1.21.1"
        },
        "components": {
            "kernel": kernel is not None,
            "mcp_client": mcp_client is not None,
            "chat_history_messages": len(chat_history.messages) if chat_history else 0,
            "plugins": plugins_list
        }
    }

    logger.info(f"✅ Health check realizado")
    return health_status

@app.get("/mcp/status")
async def mcp_status():
    """Status detalhado da conexão MCP"""
    logger.info("📡 Status do MCP solicitado")

    if not mcp_client:
        logger.error("❌ MCP não inicializado")
        raise HTTPException(status_code=503, detail="MCP não inicializado")

    try:
        # Verificar webhook através do MCP
        health = await mcp_client.check_webhook_health()

        logger.info("✅ Status do MCP verificado")

        return {
            "mcp_version": "1.21.1",
            "mcp_connected": True,
            "webhook_health": health,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Erro ao verificar status do MCP: {str(e)}", exc_info=True)
        return {
            "mcp_version": "1.21.1",
            "mcp_connected": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/plugins")
async def list_plugins():
    """Lista todos os plugins e funções disponíveis"""
    logger.info("🔌 Lista de plugins solicitada")

    if not kernel:
        raise HTTPException(status_code=500, detail="Kernel não inicializado")

    plugins_info = []

    for plugin in kernel.plugins:
        functions = []
        for function_name, function in plugin.functions.items():
            func_info = {
                "name": function_name,
                "description": function.description if hasattr(function, 'description') else "N/A"
            }

            # Adicionar informações dos parâmetros se disponível
            if hasattr(function, 'metadata') and hasattr(function.metadata, 'parameters'):
                func_info["parameters"] = [
                    {
                        "name": p.name,
                        "description": p.description if hasattr(p, 'description') else "N/A",
                        "required": p.is_required if hasattr(p, 'is_required') else False
                    }
                    for p in function.metadata.parameters
                ]

            functions.append(func_info)

        plugins_info.append({
            "plugin_name": plugin.name,
            "description": plugin.description if hasattr(plugin, 'description') else "N/A",
            "functions_count": len(functions),
            "functions": functions
        })

    return {
        "total_plugins": len(plugins_info),
        "plugins": plugins_info,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/logs/summary")
async def logs_summary():
    """Resumo dos logs disponíveis"""
    logger.info("📊 Resumo de logs solicitado")

    log_dir = os.getenv("LOG_DIR", "logs")

    try:
        if not os.path.exists(log_dir):
            return {
                "log_directory": log_dir,
                "exists": False,
                "message": "Diretório de logs não existe",
                "timestamp": datetime.utcnow().isoformat()
            }

        log_files = []
        for file in os.listdir(log_dir):
            if file.endswith('.log'):
                file_path = os.path.join(log_dir, file)
                file_size = os.path.getsize(file_path)
                file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))

                # Ler últimas linhas
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        last_lines = lines[-5:] if len(lines) > 5 else lines
                except:
                    last_lines = []

                log_files.append({
                    "filename": file,
                    "size_bytes": file_size,
                    "size_kb": round(file_size / 1024, 2),
                    "size_mb": round(file_size / (1024 * 1024), 2),
                    "last_modified": file_modified.isoformat(),
                    "lines_count": len(lines) if 'lines' in locals() else 0,
                    "preview": [line.strip() for line in last_lines]
                })

        return {
            "log_directory": log_dir,
            "exists": True,
            "total_files": len(log_files),
            "total_size_mb": round(sum(f['size_mb'] for f in log_files), 2),
            "files": sorted(log_files, key=lambda x: x['last_modified'], reverse=True),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Erro ao listar logs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao listar logs: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Estatísticas do sistema"""
    logger.info("📊 Estatísticas solicitadas")

    stats = {
        "system": {
            "uptime": "N/A",  # Você pode adicionar tracking de uptime se quiser
            "version": "2.2.0",
            "environment": os.getenv("ENVIRONMENT", "development")
        },
        "chat": {
            "total_messages": len(chat_history.messages) if chat_history else 0,
            "system_messages": sum(1 for m in chat_history.messages if "system" in str(m.role).lower()) if chat_history else 0,
            "user_messages": sum(1 for m in chat_history.messages if "user" in str(m.role).lower()) if chat_history else 0,
            "assistant_messages": sum(1 for m in chat_history.messages if "assistant" in str(m.role).lower()) if chat_history else 0
        },
        "plugins": {
            "total": len(kernel.plugins) if kernel else 0,
            "names": [p.name for p in kernel.plugins] if kernel else []
        },
        "timestamp": datetime.utcnow().isoformat()
    }

    return stats

if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Iniciando servidor FastAPI...")
    logger.info("📍 URL: http://localhost:8000")
    logger.info("📚 Docs: http://localhost:8000/docs")
    logger.info("📊 ReDoc: http://localhost:8000/redoc")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )