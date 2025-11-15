"""
ProcessorAgent - Executor especializado em processar tickets pendentes
"""

from semantic_kernel import Kernel
from semantic_kernel.contents import ChatHistory
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from config.logging_config import get_logger

logger = get_logger("agents.processor")

class ProcessorAgentExecutor:
    """Executor do agente de processamento"""

    def __init__(self, kernel: Kernel, service_id: str):
        self.kernel = kernel
        self.service_id = service_id
        logger.info("⚙️ ProcessorAgentExecutor inicializado")

    async def execute(self, user_message: str, chat_history: ChatHistory, context: str = "") -> str:
        """Executa o processamento usando apenas funções de processor"""
        logger.info(f"⚙️ ProcessorAgent executando: {user_message[:100]}...")

        processor_history = ChatHistory()
        processor_history.add_system_message(f"""Você é o ProcessorAgent, especializado em PROCESSAR tickets pendentes.

**FUNÇÕES DISPONÍVEIS:**
- process_pending_ticket: Processa um ticket pending e muda para 'solved'
- list_pending_tickets: Lista apenas tickets com status 'pending'

**REGRA CRÍTICA:**
- Você SOMENTE pode processar tickets com status 'pending'
- Se o ticket não estiver 'pending', informe o usuário

**SUAS RESPONSABILIDADES:**
- Processar tickets pendentes
- Listar tickets pendentes
- Validar status antes de processar
- Gerar novos arquivos CSV

**IMPORTANTE:**
- Use APENAS as funções do plugin TicketProcessor
- Sempre verifique o status antes de processar
- Confirme o sucesso do processamento

{context}

Execute o processamento solicitado.""")

        processor_history.add_user_message(user_message)

        execution_settings = self.kernel.get_prompt_execution_settings_from_service_id(
            service_id=self.service_id
        )

        execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto(
            filters={"included_plugins": ["TicketProcessor"]}
        )

        chat_service = self.kernel.get_service(self.service_id)

        result = await chat_service.get_chat_message_contents(
            chat_history=processor_history,
            settings=execution_settings,
            kernel=self.kernel
        )

        if result and len(result) > 0:
            response = str(result[0].content)
            logger.info(f"✅ ProcessorAgent concluído ({len(response)} caracteres)")
            return response

        logger.warning("⚠️ ProcessorAgent não gerou resposta")
        return "❌ Não foi possível processar o ticket."