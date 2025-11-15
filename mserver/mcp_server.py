"""
MCP Server v1.21.1 para integração com sistema de tickets externo
"""

import asyncio
import httpx
import sys
import os
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
from dotenv import load_dotenv

# Adicionar path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

# Logging básico para debug
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - MCP_SERVER - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TicketMCPServer:
    """Servidor MCP v1.21.1 para gerenciar integrações de tickets"""

    def __init__(self):
        self.server = Server("ticket-integration-server")
        self.webhook_url = os.getenv("WEBHOOK_URL", "https://webhook.site/test")
        logger.info(f"🚀 MCP Server inicializado - Webhook URL: {self.webhook_url}")
        self.setup_handlers()

    def setup_handlers(self):
        """Configura os handlers do MCP"""
        logger.info("⚙️ Configurando handlers do MCP Server")

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """Lista as ferramentas disponíveis no MCP"""
            logger.info("📋 Listando ferramentas MCP disponíveis")
            return [
                Tool(
                    name="send_ticket_notification",
                    description="Envia notificação de ticket para sistema externo com status 'done'",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "ticket_number": {
                                "type": "string",
                                "description": "Número do ticket a ser notificado"
                            }
                        },
                        "required": ["ticket_number"]
                    }
                ),
                Tool(
                    name="send_custom_webhook",
                    description="Envia webhook customizado para sistema externo",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "ticket_number": {
                                "type": "string",
                                "description": "Número do ticket"
                            },
                            "status": {
                                "type": "string",
                                "description": "Status a ser enviado",
                                "enum": ["done", "pending", "in_progress", "cancelled"]
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Metadados adicionais (opcional)"
                            }
                        },
                        "required": ["ticket_number", "status"]
                    }
                ),
                Tool(
                    name="check_webhook_status",
                    description="Verifica se o endpoint de webhook está acessível",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """Executa as ferramentas do MCP"""
            logger.info(f"🔧 MCP Tool chamada: {name} com argumentos: {arguments}")

            try:
                if name == "send_ticket_notification":
                    return await self._send_ticket_notification(arguments)

                elif name == "send_custom_webhook":
                    return await self._send_custom_webhook(arguments)

                elif name == "check_webhook_status":
                    return await self._check_webhook_status()

                else:
                    logger.error(f"❌ Ferramenta MCP desconhecida: {name}")
                    return [TextContent(
                        type="text",
                        text=f"❌ Ferramenta '{name}' não encontrada"
                    )]
            except Exception as e:
                logger.error(f"❌ Erro ao executar tool {name}: {str(e)}", exc_info=True)
                return [TextContent(
                    type="text",
                    text=f"❌ Erro ao executar {name}: {str(e)}"
                )]

    async def _send_ticket_notification(self, args: dict) -> list[TextContent]:
        """Envia notificação padrão de ticket com status 'done'"""
        ticket_number = args.get("ticket_number")
        logger.info(f"📤 MCP: Enviando notificação para ticket {ticket_number}")

        if not ticket_number:
            logger.error("❌ ticket_number não fornecido")
            return [TextContent(
                type="text",
                text="❌ Erro: ticket_number é obrigatório"
            )]

        try:
            payload = {
                "ticket_number": ticket_number,
                "status": "done"
            }

            logger.info(f"📦 Payload: {json.dumps(payload)}")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10.0,
                    headers={"Content-Type": "application/json"}
                )

                logger.info(f"📡 Resposta HTTP: {response.status_code}")

                if response.status_code in [200, 201]:
                    logger.info(f"✅ Webhook enviado com sucesso para {ticket_number}")
                    message = f"""✅ **Webhook Enviado com Sucesso!**

📌 Ticket: {ticket_number}
📊 Status: done
🌐 URL: {self.webhook_url}
📡 HTTP Status: {response.status_code}
✉️ Payload: {json.dumps(payload, indent=2)}
"""
                else:
                    logger.warning(f"⚠️ Webhook enviado mas status não esperado: {response.status_code}")
                    message = f"""⚠️ **Webhook Enviado com Aviso**

📌 Ticket: {ticket_number}
📡 HTTP Status: {response.status_code}
⚠️ O servidor retornou um código não esperado
"""

                return [TextContent(type="text", text=message)]

        except httpx.TimeoutException:
            logger.error(f"⏱️ Timeout ao enviar webhook para {ticket_number}")
            return [TextContent(
                type="text",
                text=f"❌ Timeout ao enviar webhook para {ticket_number}"
            )]
        except Exception as e:
            logger.error(f"❌ Erro ao enviar webhook: {str(e)}", exc_info=True)
            return [TextContent(
                type="text",
                text=f"❌ Erro ao enviar webhook: {str(e)}"
            )]

    async def _send_custom_webhook(self, args: dict) -> list[TextContent]:
        """Envia webhook customizado"""
        ticket_number = args.get("ticket_number")
        status = args.get("status", "done")
        metadata = args.get("metadata", {})

        logger.info(f"📤 MCP: Enviando webhook customizado para {ticket_number} com status {status}")

        if not ticket_number:
            return [TextContent(
                type="text",
                text="❌ Erro: ticket_number é obrigatório"
            )]

        try:
            payload = {
                "ticket_number": ticket_number,
                "status": status,
                **metadata
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10.0,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code in [200, 201]:
                    message = f"""✅ **Webhook Customizado Enviado!**

📌 Ticket: {ticket_number}
📊 Status: {status}
📡 HTTP Status: {response.status_code}
"""
                    return [TextContent(type="text", text=message)]
                else:
                    return [TextContent(
                        type="text",
                        text=f"⚠️ Webhook enviado com status {response.status_code}"
                    )]

        except Exception as e:
            logger.error(f"❌ Erro ao enviar webhook customizado: {str(e)}")
            return [TextContent(
                type="text",
                text=f"❌ Erro: {str(e)}"
            )]

    async def _check_webhook_status(self) -> list[TextContent]:
        """Verifica saúde do webhook"""
        logger.info(f"🔍 MCP: Verificando status do webhook")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.webhook_url,
                    timeout=5.0
                )

                message = f"""🔍 **Status do Webhook**

🌐 URL: {self.webhook_url}
📡 Status: {'✅ Acessível' if response.status_code == 200 else '⚠️ Código ' + str(response.status_code)}
"""
                return [TextContent(type="text", text=message)]

        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Webhook inacessível: {str(e)}"
            )]

    async def run(self):
        """Inicia o servidor MCP"""
        logger.info("🚀 MCP Server rodando e aguardando conexões...")

        try:
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options()
                )
        except Exception as e:
            logger.error(f"❌ Erro no MCP Server: {str(e)}", exc_info=True)
            raise

async def main():
    """Função principal para rodar o servidor standalone"""
    logger.info("=" * 60)
    logger.info("🚀 INICIANDO MCP SERVER STANDALONE")
    logger.info("=" * 60)

    server = TicketMCPServer()
    await server.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 MCP Server encerrado pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {str(e)}", exc_info=True)
        sys.exit(1)