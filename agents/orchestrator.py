"""
Agente Orquestrador - Decide qual agente especializado usar baseado no contexto
"""

from typing import Dict, Any
from semantic_kernel import Kernel
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import KernelArguments
import json
from config.logging_config import get_logger

logger = get_logger("agents.orchestrator")

class OrchestratorAgent:
    """
    Orquestrador inteligente que analisa a requisição e roteia para o agente apropriado
    """

    def __init__(self, kernel: Kernel, service_id: str):
        self.kernel = kernel
        self.service_id = service_id
        logger.info("🎭 OrchestratorAgent inicializado")

    async def route_request(self, user_message: str, chat_history: ChatHistory) -> Dict[str, Any]:
        """
        Analisa a mensagem do usuário e decide qual agente(s) usar

        Returns:
            {
                "primary_agent": "SearchAgent" | "ProcessorAgent" | "WebhookAgent",
                "reasoning": "Por que esse agente foi escolhido",
                "requires_multiple_agents": bool,
                "agent_sequence": ["SearchAgent", "ProcessorAgent", "WebhookAgent"]
            }
        """
        logger.info(f"🎯 Analisando requisição para roteamento: {user_message[:100]}...")

        routing_prompt = f"""Você é um orquestrador de agentes especializado em gerenciamento de tickets.

**AGENTES DISPONÍVEIS:**

1. **SearchAgent** - Especialista em BUSCAR e CONSULTAR informações
   - Buscar ticket por número
   - Listar todos os tickets
   - Listar tickets pendentes
   - Mostrar informações de tickets
   - Consultar status
   
2. **ProcessorAgent** - Especialista em PROCESSAR e ALTERAR tickets
   - Processar tickets pendentes (mudar status para 'solved')
   - REGRA: Só pode processar tickets com status 'pending'
   - Gerar novos arquivos CSV
   
3. **WebhookAgent** - Especialista em NOTIFICAR sistemas externos
   - Enviar webhooks via MCP
   - Notificar sistemas externos
   - Verificar saúde do webhook

**MENSAGEM DO USUÁRIO:**
"{user_message}"

**SUA TAREFA:**
Analise a mensagem e determine:
1. Qual agente principal deve ser usado
2. Se precisa de múltiplos agentes em sequência
3. A ordem de execução se houver múltiplos agentes

**REGRAS:**
- Se a mensagem pede para "buscar e processar", use SearchAgent DEPOIS ProcessorAgent
- Se a mensagem pede para "processar e notificar", use ProcessorAgent DEPOIS WebhookAgent
- Se a mensagem é apenas consulta, use APENAS SearchAgent
- Se mencionar webhook/notificação, SEMPRE inclua WebhookAgent

Responda APENAS com um JSON válido neste formato:
{{
    "primary_agent": "SearchAgent",
    "reasoning": "O usuário está pedindo para buscar informações de um ticket",
    "requires_multiple_agents": false,
    "agent_sequence": ["SearchAgent"]
}}

OU para múltiplos agentes:
{{
    "primary_agent": "SearchAgent",
    "reasoning": "O usuário quer buscar, processar e notificar. Precisa de 3 agentes em sequência.",
    "requires_multiple_agents": true,
    "agent_sequence": ["SearchAgent", "ProcessorAgent", "WebhookAgent"]
}}

JSON:"""

        try:
            # Criar histórico temporário para roteamento
            routing_history = ChatHistory()
            routing_history.add_system_message("Você é um analisador de requisições. Responda APENAS com JSON válido.")
            routing_history.add_user_message(routing_prompt)

            # Obter serviço de chat
            chat_service = self.kernel.get_service(self.service_id)

            # Configurar settings
            execution_settings = self.kernel.get_prompt_execution_settings_from_service_id(
                service_id=self.service_id
            )

            # Desabilitar function calling para análise de roteamento
            execution_settings.function_choice_behavior = None
            execution_settings.temperature = 0.1  # Baixa temperatura para decisões consistentes
            execution_settings.max_tokens = 500

            logger.debug("🤖 Consultando LLM para roteamento...")

            # Chamar LLM para decisão de roteamento
            result = await chat_service.get_chat_message_contents(
                chat_history=routing_history,
                settings=execution_settings,
                kernel=self.kernel
            )

            if result and len(result) > 0:
                response_text = str(result[0].content).strip()
                logger.debug(f"📤 Resposta do LLM: {response_text}")

                # Extrair JSON da resposta
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1

                if json_start != -1 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    routing_decision = json.loads(json_str)

                    logger.info(f"✅ Roteamento decidido: {routing_decision['primary_agent']}")
                    logger.info(f"💡 Razão: {routing_decision['reasoning']}")

                    if routing_decision.get('requires_multiple_agents'):
                        logger.info(f"🔄 Múltiplos agentes: {routing_decision['agent_sequence']}")

                    return routing_decision
                else:
                    raise ValueError("JSON não encontrado na resposta")

            # Fallback: usar SearchAgent se não conseguir decidir
            logger.warning("⚠️ Não foi possível analisar resposta, usando SearchAgent como fallback")
            return {
                "primary_agent": "SearchAgent",
                "reasoning": "Fallback devido a erro na análise",
                "requires_multiple_agents": False,
                "agent_sequence": ["SearchAgent"]
            }

        except json.JSONDecodeError as e:
            logger.error(f"❌ Erro ao parsear JSON de roteamento: {str(e)}")
            return {
                "primary_agent": "SearchAgent",
                "reasoning": "Fallback devido a erro de parsing",
                "requires_multiple_agents": False,
                "agent_sequence": ["SearchAgent"]
            }
        except Exception as e:
            logger.error(f"❌ Erro no roteamento: {str(e)}", exc_info=True)
            return {
                "primary_agent": "SearchAgent",
                "reasoning": "Fallback devido a erro",
                "requires_multiple_agents": False,
                "agent_sequence": ["SearchAgent"]
            }