"""
LLM Insert Agent - SIMPLIFICADO
LLM gera SQL, Plugin executa
"""

from semantic_kernel import Kernel
from semantic_kernel.contents import ChatHistory
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from config.logging_config import get_logger

logger = get_logger("agents.llm_insert")

class LLMInsertAgentExecutor:
    """
    Agente SIMPLES:
    1. Pede LLM gerar SQL
    2. Usa plugin para executar
    """

    def __init__(self, kernel: Kernel, service_id: str):
        self.kernel = kernel
        self.service_id = service_id
        logger.info("🤖 LLMInsertAgent - LLM gera, plugin executa (INSERT + SELECT)")

    async def execute(self, user_message: str, chat_history: ChatHistory, context: str = "") -> str:
        """
        Fluxo SIMPLES:
        1. LLM gera SQL
        2. Plugin DatabaseExecutor executa
        """
        logger.info(f"🤖 Processando: {user_message[:100]}...")

        # Criar histórico com instruções
        agent_history = ChatHistory()
        agent_history.add_system_message(f"""Você é um assistente que ajuda a gerenciar banco de dados PostgreSQL.

**REGRAS CRÍTICAS:**
- **SEMPRE** use o formato: ticket_system.nome_tabela
- Nome de tabela: SEMPRE em inglês e no plural
- Exemplos corretos:
  - SELECT * FROM ticket_system.events
  - INSERT INTO ticket_system.products ...
  - UPDATE ticket_system.users SET ...

**FERRAMENTAS DISPONÍVEIS:**
- check_table_exists: Verifica se tabela existe
- execute_sql: Executa SQL (CREATE TABLE, CREATE TRIGGER, etc)
- execute_query: Executa query com retorno (INSERT RETURNING, SELECT)

**PARA INSERIR DADOS (INSERT):**

1. Use check_table_exists para ver se a tabela existe
2. Se NÃO existir: use execute_sql para criar (CREATE TABLE SIMPLES)
3. Use execute_query para inserir os dados (INSERT ... RETURNING *)
4. Devolva o resultado em formato JSON

**PARA ATUALIZAR DADOS (UPDATE):**

1. Use check_table_exists para ver se a tabela existe
2. Verifique a instrucao do usuário para entender quais colunas atualizar e quais condições usar
4. Devolva o resultado da atualizacao em formato JSON

**PARA CONSULTAR DADOS (SELECT):**

1. Use check_table_exists para ver se a tabela existe
2. Se a tabela NÃO existir:
   - Devolva mensagem: "Tabela 'nome' não existe no schema 'ticket_system'"
   - NÃO tente criar a tabela
   
3. Se a tabela existir:
   - Use execute_query para buscar (SELECT)
   - Se retornar dados: Devolva em formato JSON legível
   - Se não retornar dados: "Nenhum registro encontrado na tabela 'nome'"

**REGRAS:**
- Nome de tabela: SEMPRE PRECISA SEM EM INGLES E NO PLURAL
- Schema: ticket_system
- Sempre adicione: id SERIAL PRIMARY KEY
- Crie tabelas SIMPLES (sem triggers complexos, sem updated_at)
- Infira tipos baseado no contexto semântico
- Use sua experiência como DBA
- Por padrão as colunas precisam ser em inglês
- Se a tabela não existir ou o dado não existir devolva a mensagem informando
- Sempre retorne respostas em formato JSON quando possível

**INFERÊNCIA DE TIPOS:**
- name, title, status, email -> VARCHAR(255)
- description, content, notes -> TEXT
- price, value, amount -> DECIMAL(10,2)
- quantity, age, count -> INTEGER
- created_at, updated_at -> TIMESTAMP
- active, published, available -> BOOLEAN

**CONTEXTO:**
{context if context else "Nenhum contexto adicional"}

Execute a operação solicitada usando as ferramentas disponíveis.""")

        # Adicionar mensagem do usuário
        agent_history.add_user_message(user_message)

        # Configurar function calling
        settings = self.kernel.get_prompt_execution_settings_from_service_id(self.service_id)
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto(
            filters={"included_plugins": ["DatabaseExecutor"]}
        )
        settings.max_tokens = 2000
        settings.temperature = 0.1

        try:
            # LLM vai decidir quais funções chamar
            chat_service = self.kernel.get_service(self.service_id)

            result = await chat_service.get_chat_message_contents(
                chat_history=agent_history,
                settings=settings,
                kernel=self.kernel
            )

            logger.info("## result" + str(result))

            if result and len(result) > 0:
                response = str(result[0].content)

                # Log do tipo de operação
                user_msg_upper = user_message.upper()
                if any(word in user_msg_upper for word in ["SELECT", "BUSCAR", "CONSULTAR", "LISTAR", "PREÇO", "VALOR"]):
                    logger.info("🔍 SELECT executado via plugins")
                elif any(word in user_msg_upper for word in ["INSERT", "INSERIR", "ADICIONAR", "CRIAR"]):
                    logger.info("✅ INSERT executado via plugins")
                else:
                    logger.info("✅ Operação executada via plugins")

                return response

            return "❌ Nenhuma resposta gerada"

        except Exception as e:
            logger.error(f"❌ Erro: {str(e)}", exc_info=True)
            return f"❌ Erro ao processar: {str(e)}"