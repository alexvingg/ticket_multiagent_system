"""
Gerenciador de conexão com PostgreSQL usando asyncpg
"""

import asyncpg
import os
from typing import Optional
from contextlib import asynccontextmanager
from config.logging_config import get_logger

logger = get_logger("database.connection")

class DatabaseManager:
    """Gerenciador de pool de conexões PostgreSQL"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.host = os.getenv("POSTGRES_HOST", "localhost")
        self.port = int(os.getenv("POSTGRES_PORT", 5432))
        self.user = os.getenv("POSTGRES_USER", "ticket_admin")
        self.password = os.getenv("POSTGRES_PASSWORD", "ticket_pass_2024")
        self.database = os.getenv("POSTGRES_DB", "ticket_system")
        self.min_size = int(os.getenv("DB_POOL_MIN_SIZE", 2))
        self.max_size = int(os.getenv("DB_POOL_MAX_SIZE", 10))
        self.timeout = int(os.getenv("DB_POOL_TIMEOUT", 30))

        logger.info(f"🐘 DatabaseManager configurado: {self.host}:{self.port}/{self.database}")

    async def connect(self):
        """Cria o pool de conexões"""
        try:
            logger.info("🔌 Conectando ao PostgreSQL...")

            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                min_size=self.min_size,
                max_size=self.max_size,
                command_timeout=self.timeout
            )

            # Testar conexão
            async with self.pool.acquire() as conn:
                version = await conn.fetchval('SELECT version()')
                logger.info(f"✅ Conectado ao PostgreSQL")
                logger.debug(f"📊 Versão: {version[:50]}...")

            return True

        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao PostgreSQL: {str(e)}", exc_info=True)
            raise

    async def disconnect(self):
        """Fecha o pool de conexões"""
        if self.pool:
            logger.info("🔌 Fechando conexões com PostgreSQL...")
            await self.pool.close()
            self.pool = None
            logger.info("✅ Conexões fechadas")

    @asynccontextmanager
    async def acquire(self):
        """Context manager para obter uma conexão do pool"""
        if not self.pool:
            raise RuntimeError("Pool de conexões não inicializado. Chame connect() primeiro.")

        async with self.pool.acquire() as connection:
            yield connection

    async def execute(self, query: str, *args):
        """Executa um query (INSERT, UPDATE, DELETE)"""
        async with self.acquire() as conn:
            logger.debug(f"📝 Executando query: {query[:100]}...")
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args):
        """Executa um query e retorna todos os resultados"""
        async with self.acquire() as conn:
            logger.debug(f"🔍 Fetch query: {query[:100]}...")
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """Executa um query e retorna apenas uma linha"""
        async with self.acquire() as conn:
            logger.debug(f"🔍 Fetchrow query: {query[:100]}...")
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        """Executa um query e retorna apenas um valor"""
        async with self.acquire() as conn:
            logger.debug(f"🔍 Fetchval query: {query[:100]}...")
            return await conn.fetchval(query, *args)

    async def table_exists(self, table_name: str, schema: str = "ticket_system") -> bool:
        """Verifica se uma tabela existe"""
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = $1 
                AND table_name = $2
            );
        """
        return await self.fetchval(query, schema, table_name)

    async def get_table_columns(self, table_name: str, schema: str = "ticket_system"):
        """Retorna as colunas de uma tabela"""
        query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position;
        """
        return await self.fetch(query, schema, table_name)

    async def log_operation(
            self,
            operation_type: str,
            table_name: str,
            description: str,
            status: str,
            error_message: str = None
    ):
        """Registra uma operação na tabela de logs"""
        query = """
            INSERT INTO ticket_system.operation_logs 
            (operation_type, table_name, description, status, error_message)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id;
        """
        try:
            log_id = await self.fetchval(
                query,
                operation_type,
                table_name,
                description,
                status,
                error_message
            )
            logger.debug(f"📝 Operação logada: {operation_type} - {table_name} (ID: {log_id})")
            return log_id
        except Exception as e:
            logger.error(f"❌ Erro ao logar operação: {str(e)}")
            return None

# Instância global
db_manager = DatabaseManager()