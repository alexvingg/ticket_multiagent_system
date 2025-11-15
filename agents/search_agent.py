"""
SearchAgent - Executor especializado em buscar e consultar tickets
"""

from semantic_kernel import Kernel
from semantic_kernel.contents import ChatHistory
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from config.logging_config import get_logger

logger = get_logger("agents.search")

class SearchAgentExecutor:
    """Executor do agente de busca"""

    def __init__(self, kernel: Kernel, service_id: str):
        self.kernel = kernel
        self.service_id = service_id
        logger.info("🔍 SearchAgentExecutor inicializado")

    async def execute(self, user_message: str, chat_history: ChatHistory) -> str:
        """Executa a busca usando apenas funções de search"""
        logger.info(f"🔍 SearchAgent executando: {user_message[:100]}...")

        # Criar contexto específico para SearchAgent
        search_history = ChatHistory()
        search_history.add_system_message("""Você é o SearchAgent, especializado em BUSCAR informações de tickets.

**FUNÇÕES DISPONÍVEIS:**
- search_ticket: Busca um ticket específico por número
- list_all_tickets: Lista todos os tickets do sistema

**SUAS RESPONSABILIDADES:**
- Buscar tickets por número
- Listar tickets
- Mostrar informações detalhadas de tickets
- Responder perguntas sobre status de tickets

**IMPORTANTE:**
- Use APENAS as funções do plugin TicketSearch
- Forneça respostas claras e bem formatadas
- Se o ticket não existir, informe claramente

Execute a busca solicitada.""")

        search_history.add_user_message(user_message)

        # Configurar execution settings APENAS com plugin TicketSearch
        execution_settings = self.kernel.get_prompt_execution_settings_from_service_id(
            service_id=self.service_id
        )

        execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto(
            filters={"included_plugins": ["TicketSearch"]}
        )

        # Executar
        chat_service = self.kernel.get_service(self.service_id)

        result = await chat_service.get_chat_message_contents(
            chat_history=search_history,
            settings=execution_settings,
            kernel=self.kernel
        )

        if result and len(result) > 0:
            response = str(result[0].content)
            logger.info(f"✅ SearchAgent concluído ({len(response)} caracteres)")
            return response

        logger.warning("⚠️ SearchAgent não gerou resposta")
        return "❌ Não foi possível buscar as informações solicitadas."