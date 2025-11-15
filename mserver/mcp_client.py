"""
Cliente MCP v1.21.1 que conecta ao servidor e expõe ferramentas
"""

import asyncio
import sys
import os
from typing import Any, Annotated
from semantic_kernel.functions import kernel_function
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json

# Adicionar path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.logging_config import get_logger

logger = get_logger("mcp.client")

class MCPTicketClient:
    """Cliente MCP v1.21.1 para integração com tickets"""

    def __init__(self):
        self.session: ClientSession | None = None
        self._context_manager = None
        self._read_stream = None
        self._write_stream = None
        self._server_process = None
        logger.info("🔌 MCPTicketClient v1.21.1 inicializado")

    async def connect(self):
        """Conecta ao servidor MCP"""
        logger.info("📡 Conectando ao MCP Server v1.21.1...")

        try:
            # Caminho absoluto para o servidor
            current_dir = os.path.dirname(os.path.abspath(__file__))
            server_path = os.path.join(current_dir, "mcp_server.py")

            logger.info(f"📂 Servidor MCP: {server_path}")

            if not os.path.exists(server_path):
                raise FileNotFoundError(f"Servidor MCP não encontrado em: {server_path}")

            # Obter python do virtualenv ou sistema
            python_executable = sys.executable
            logger.info(f"🐍 Python: {python_executable}")

            server_params = StdioServerParameters(
                command=python_executable,
                args=[server_path],
                env={
                    **os.environ,
                    "PYTHONPATH": os.path.dirname(current_dir),
                    "PYTHONUNBUFFERED": "1"
                }
            )

            logger.info("🔌 Criando conexão stdio com MCP Server...")

            # Criar contexto do cliente com timeout
            self._context_manager = stdio_client(server_params)

            # Aguardar conexão com timeout
            try:
                self._read_stream, self._write_stream = await asyncio.wait_for(
                    self._context_manager.__aenter__(),
                    timeout=10.0
                )
                logger.info("✅ Streams stdio criados")
            except asyncio.TimeoutError:
                logger.error("❌ Timeout ao criar streams stdio")
                raise TimeoutError("Timeout ao conectar com MCP Server")

            # Inicializar sessão
            logger.info("🔗 Inicializando sessão MCP...")
            self.session = ClientSession(self._read_stream, self._write_stream)
            await self.session.__aenter__()

            # Inicializar protocolo com timeout
            logger.info("📡 Enviando initialize ao servidor...")
            try:
                init_result = await asyncio.wait_for(
                    self.session.initialize(),
                    timeout=5.0
                )
                logger.info("✅ Protocolo MCP inicializado com sucesso")
            except asyncio.TimeoutError:
                logger.error("❌ Timeout ao inicializar protocolo MCP")
                raise TimeoutError("MCP Server não respondeu ao initialize")

            logger.info("✅ MCP Client v1.21.1 conectado ao servidor!")

            # Listar ferramentas disponíveis
            try:
                tools_result = await asyncio.wait_for(
                    self.session.list_tools(),
                    timeout=5.0
                )
                if hasattr(tools_result, 'tools'):
                    tool_names = [t.name for t in tools_result.tools]
                    logger.info(f"📌 Ferramentas MCP disponíveis ({len(tool_names)}): {tool_names}")
                else:
                    logger.warning("⚠️ Nenhuma ferramenta MCP listada")
            except asyncio.TimeoutError:
                logger.warning("⚠️ Timeout ao listar ferramentas")
            except Exception as e:
                logger.warning(f"⚠️ Não foi possível listar ferramentas: {str(e)}")

        except FileNotFoundError as e:
            logger.error(f"❌ Arquivo não encontrado: {str(e)}")
            raise
        except TimeoutError as e:
            logger.error(f"❌ Timeout: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao MCP Server: {str(e)}", exc_info=True)
            raise

    async def disconnect(self):
        """Desconecta do servidor MCP"""
        logger.info("🔌 Desconectando do MCP Server v1.21.1...")

        try:
            if self.session:
                await self.session.__aexit__(None, None, None)
                self.session = None
            if self._context_manager:
                await self._context_manager.__aexit__(None, None, None)
                self._context_manager = None
            logger.info("✅ MCP Client desconectado com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao desconectar: {str(e)}", exc_info=True)

    @kernel_function(
        name="send_ticket_webhook",
        description="Envia notificação de ticket para sistema externo via MCP com status 'done'"
    )
    async def send_ticket_webhook(
            self,
            ticket_number: Annotated[str, "O número do ticket a ser notificado (ex: TKT-001)"]
    ) -> str:
        """Envia webhook através do MCP Server"""
        logger.info(f"📤 Solicitação de webhook para ticket: {ticket_number}")

        if not self.session:
            logger.error("❌ Cliente MCP não está conectado")
            return "❌ Erro: Cliente MCP não está conectado. Por favor, reinicie o sistema."

        try:
            logger.debug(f"🔧 Chamando MCP tool: send_ticket_notification")

            result = await asyncio.wait_for(
                self.session.call_tool(
                    "send_ticket_notification",
                    arguments={"ticket_number": ticket_number}
                ),
                timeout=15.0
            )

            if hasattr(result, 'content') and result.content and len(result.content) > 0:
                response_text = result.content[0].text
                logger.info(f"✅ Webhook enviado com sucesso via MCP para {ticket_number}")
                return response_text

            logger.warning("⚠️ MCP retornou resposta vazia")
            return f"✅ Webhook enviado para {ticket_number} (sem resposta detalhada do servidor)"

        except asyncio.TimeoutError:
            logger.error(f"❌ Timeout ao enviar webhook")
            return f"❌ Timeout ao enviar webhook para {ticket_number}"
        except Exception as e:
            logger.error(f"❌ Erro ao enviar webhook via MCP: {str(e)}", exc_info=True)
            return f"❌ Erro ao enviar webhook via MCP: {str(e)}"

    @kernel_function(
        name="send_custom_ticket_webhook",
        description="Envia webhook customizado com status e metadados específicos"
    )
    async def send_custom_webhook(
            self,
            ticket_number: Annotated[str, "O número do ticket"],
            status: Annotated[str, "Status do ticket (done, pending, in_progress, cancelled)"] = "done",
            metadata: Annotated[str, "Metadados adicionais em formato JSON (opcional)"] = "{}"
    ) -> str:
        """Envia webhook customizado através do MCP Server"""
        logger.info(f"📤 Webhook customizado para {ticket_number} com status {status}")

        if not self.session:
            logger.error("❌ Cliente MCP não está conectado")
            return "❌ Erro: Cliente MCP não está conectado"

        try:
            # Parse metadata
            try:
                metadata_dict = json.loads(metadata) if metadata and metadata != "{}" else {}
                logger.debug(f"📦 Metadata parsed: {metadata_dict}")
            except json.JSONDecodeError as je:
                logger.error(f"❌ Metadata inválido: {str(je)}")
                return "❌ Erro: metadata deve ser um JSON válido"

            result = await asyncio.wait_for(
                self.session.call_tool(
                    "send_custom_webhook",
                    arguments={
                        "ticket_number": ticket_number,
                        "status": status,
                        "metadata": metadata_dict
                    }
                ),
                timeout=15.0
            )

            if hasattr(result, 'content') and result.content and len(result.content) > 0:
                response_text = result.content[0].text
                logger.info(f"✅ Webhook customizado enviado com sucesso")
                return response_text

            return f"✅ Webhook customizado enviado para {ticket_number}"

        except asyncio.TimeoutError:
            return f"❌ Timeout ao enviar webhook customizado"
        except Exception as e:
            logger.error(f"❌ Erro ao enviar webhook customizado: {str(e)}", exc_info=True)
            return f"❌ Erro ao enviar webhook customizado via MCP: {str(e)}"

    @kernel_function(
        name="check_webhook_health",
        description="Verifica se o endpoint de webhook está acessível e funcionando"
    )
    async def check_webhook_health(self) -> str:
        """Verifica saúde do webhook através do MCP Server"""
        logger.info("🔍 Verificação de saúde do webhook solicitada")

        if not self.session:
            logger.error("❌ Cliente MCP não está conectado")
            return "❌ Erro: Cliente MCP não está conectado"

        try:
            result = await asyncio.wait_for(
                self.session.call_tool("check_webhook_status", arguments={}),
                timeout=10.0
            )

            if hasattr(result, 'content') and result.content and len(result.content) > 0:
                response_text = result.content[0].text
                logger.info("✅ Verificação de saúde concluída")
                return response_text

            return "✅ Webhook verificado (sem detalhes)"

        except asyncio.TimeoutError:
            return "❌ Timeout ao verificar webhook"
        except Exception as e:
            logger.error(f"❌ Erro ao verificar webhook: {str(e)}", exc_info=True)
            return f"❌ Erro ao verificar webhook via MCP: {str(e)}"