"""
Configuração centralizada de logging para o sistema multi-agente
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from pythonjsonlogger import jsonlogger
from typing import Optional

# Criar diretório de logs se não existir
LOG_DIR = os.getenv("LOG_DIR", "logs")
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

# Configurações
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 10485760))  # 10MB
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 5))

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Formatador JSON customizado com campos adicionais"""

    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno

def setup_logging(name: str = "ticket_system") -> logging.Logger:
    """
    Configura o sistema de logging com múltiplos handlers

    Args:
        name: Nome do logger

    Returns:
        Logger configurado
    """

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))

    # Evitar duplicação de handlers
    if logger.handlers:
        return logger

    # 1️⃣ Console Handler (formato legível)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)

    # 2️⃣ File Handler - Arquivo geral (texto)
    general_log_path = os.path.join(LOG_DIR, 'application.log')
    file_handler = logging.handlers.RotatingFileHandler(
        general_log_path,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)

    # 3️⃣ JSON Handler - Logs em JSON para análise
    json_log_path = os.path.join(LOG_DIR, 'application.json.log')
    json_handler = logging.handlers.RotatingFileHandler(
        json_log_path,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    json_handler.setLevel(logging.DEBUG)
    json_format = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    json_handler.setFormatter(json_format)

    # 4️⃣ Error Handler - Apenas erros
    error_log_path = os.path.join(LOG_DIR, 'errors.log')
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_path,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_format)

    # 5️⃣ Agent Handler - Logs específicos de agentes
    agent_log_path = os.path.join(LOG_DIR, 'agents.log')
    agent_handler = logging.handlers.RotatingFileHandler(
        agent_log_path,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    agent_handler.setLevel(logging.INFO)
    agent_handler.setFormatter(file_format)
    agent_handler.addFilter(AgentLogFilter())

    # 6️⃣ MCP Handler - Logs do MCP
    mcp_log_path = os.path.join(LOG_DIR, 'mcp.log')
    mcp_handler = logging.handlers.RotatingFileHandler(
        mcp_log_path,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    mcp_handler.setLevel(logging.DEBUG)
    mcp_handler.setFormatter(file_format)
    mcp_handler.addFilter(MCPLogFilter())

    # Adicionar handlers ao logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(json_handler)
    logger.addHandler(error_handler)
    logger.addHandler(agent_handler)
    logger.addHandler(mcp_handler)

    return logger

class AgentLogFilter(logging.Filter):
    """Filtro para logs de agentes"""
    def filter(self, record):
        return 'agent' in record.name.lower() or 'Agent' in record.getMessage()

class MCPLogFilter(logging.Filter):
    """Filtro para logs do MCP"""
    def filter(self, record):
        return 'mcp' in record.name.lower() or 'MCP' in record.getMessage()

def get_logger(name: str) -> logging.Logger:
    """
    Obtém um logger específico

    Args:
        name: Nome do módulo/componente

    Returns:
        Logger configurado
    """
    return logging.getLogger(f"ticket_system.{name}")

# Configurar logging na importação
setup_logging()