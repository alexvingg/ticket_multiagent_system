"""
WebhookAgent - Executor especializado em enviar notificações via MCP
"""

from semantic_kernel import Kernel
from semantic_kernel.contents import ChatHistory
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from config.logging_config import get_logger

logger = get_logger("agents.webhook")

class WebhookAgentExecutor:
    """Executor do agente de webhook"""

    def __init__(self, kernel: Kernel, service_id: str):
        self.kernel = kernel
        self.service_id = service_id
        logger.info("📡 WebhookAgentExecutor inicializado")

    async def execute(self, user_message: str, chat_history: ChatHistory, context: str = "") -> str:
        """Executa o envio de webhook usando apenas funções MCP"""
        logger.info(f"📡 WebhookAgent executando: {user_message[:100]}...")

        webhook_history = ChatHistory()
        webhook_history.add_system_message(f"""Você é o WebhookAgent, especializado em NOTIFICAR sistemas externos via MCP.

**FUNÇÕES DISPONÍVEIS:**
- send_ticket_webhook: Envia webhook com status 'done' (padrão)
- send_custom_ticket_webhook: Envia webhook com status customizado
- check_webhook_health: Verifica se o webhook está funcionando

**SUAS RESPONSABILIDADES:**
- Enviar notificações de tickets via webhook
- Notificar sistemas externos quando tickets são processados
- Verificar saúde da integração

**IMPORTANTE:**
- Use APENAS as funções do plugin TicketWebhookMCP
- O status padrão enviado é 'done'
- Sempre confirme o envio ao usuário

{context}

Execute a notificação solicitada.""")

        webhook_history.add_user_message(user_message)

        execution_settings = self.kernel.get_prompt_execution_settings_from_service_id(
            service_id=self.service_id
        )

        execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto(
            filters={"included_plugins": ["TicketWebhookMCP"]}
        )

        chat_service = self.kernel.get_service(self.service_id)

        result = await chat_service.get_chat_message_contents(
            chat_history=webhook_history,
            settings=execution_settings,
            kernel=self.kernel
        )

        if result and len(result) > 0:
            response = str(result[0].content)
            logger.info(f"✅ WebhookAgent concluído ({len(response)} caracteres)")
            return response

        logger.warning("⚠️ WebhookAgent não gerou resposta")
        return "❌ Não foi possível enviar o webhook."