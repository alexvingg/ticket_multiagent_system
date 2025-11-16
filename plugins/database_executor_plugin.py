"""
Database Executor Plugin - SIMPLES
Apenas executa SQL que a LLM gera
"""

from semantic_kernel.functions import kernel_function
from typing import Annotated
from config.logging_config import get_logger
from database import db_manager

logger = get_logger("plugins.database_executor")

class DatabaseExecutorPlugin:
    """
    Plugin SIMPLES que só executa SQL
    Não pensa, não decide, apenas executa
    """

    def __init__(self):
        logger.info("🔧 DatabaseExecutorPlugin inicializado (executor simples)")

    @kernel_function(
        name="execute_sql",
        description="Executa um comando SQL no PostgreSQL (CREATE TABLE, INSERT, etc)"
    )
    async def execute_sql(
            self,
            sql: Annotated[str, "Comando SQL a ser executado"]
    ) -> str:
        """Executa SQL e retorna resultado"""
        logger.info(f"⚡ Executando SQL...")
        logger.debug(f"📝 SQL: {sql[:200]}...")

        try:
            # Simplesmente executa o que foi pedido
            logger.info(f"🚀 Enviando SQL para execução... {sql}")
            await db_manager.execute(sql)

            logger.info("✅ SQL executado com sucesso")
            return f"✅ SQL executado com sucesso:\n{sql[:200]}..."

        except Exception as e:
            logger.error(f"❌ Erro ao executar SQL: {str(e)}")
            return f"❌ Erro ao executar SQL: {str(e)}"

    @kernel_function(
        name="execute_query",
        description="Executa uma query SQL e retorna os resultados (SELECT, INSERT RETURNING, etc)"
    )
    async def execute_query(
            self,
            sql: Annotated[str, "Query SQL a ser executada com retorno de dados"]
    ) -> str:
        """Executa query e retorna dados"""
        logger.info(f"🔍 Executando query...")
        logger.debug(f"📝 SQL: {sql}")

        try:
            # Executar e retornar resultado
            if 'SELECT' in sql.upper() or 'RETURNING' in sql.upper():
                results = await db_manager.fetch(sql)

                if not results:
                    return "✅ Query executada, mas não retornou dados."

                # Formatar resultados
                formatted = []
                for row in results:
                    row_dict = dict(row)
                    formatted.append(str(row_dict))

                logger.info(f"✅ Query executada: {len(results)} linha(s)")
                return f"✅ Query executada com sucesso!\n\nResultados ({len(results)} linha(s)):\n" + "\n".join(formatted[:10])
            else:
                await db_manager.execute(sql)
                return f"✅ Comando executado com sucesso"

        except Exception as e:
            logger.error(f"❌ Erro ao executar query: {str(e)}")
            return f"❌ Erro ao executar query: {str(e)}"

    @kernel_function(
        name="check_table_exists",
        description="Verifica se uma tabela existe no schema ticket_system"
    )
    async def check_table_exists(
            self,
            table_name: Annotated[str, "Nome da tabela a verificar"]
    ) -> str:
        """Verifica se tabela existe"""
        logger.info(f"🔍 Verificando se tabela {table_name} existe...")

        try:
            exists = await db_manager.table_exists(table_name)

            if exists:
                logger.info(f"✅ Tabela {table_name} existe")
                return f"✅ Tabela '{table_name}' existe"
            else:
                logger.info(f"❌ Tabela {table_name} não existe")
                return f"❌ Tabela '{table_name}' NÃO existe"

        except Exception as e:
            logger.error(f"❌ Erro ao verificar tabela: {str(e)}")
            return f"❌ Erro: {str(e)}"