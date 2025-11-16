-- Script de inicialização mínimo do banco de dados
-- Os agentes criarão todas as tabelas dinamicamente

-- Extensões úteis
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Schema para o sistema de tickets
CREATE SCHEMA IF NOT EXISTS ticket_system;

-- Função para atualizar updated_at automaticamente
-- (usada por todas as tabelas que os agentes criarem)
CREATE OR REPLACE FUNCTION ticket_system.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Grants
GRANT ALL PRIVILEGES ON SCHEMA ticket_system TO ticket_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ticket_system TO ticket_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ticket_system TO ticket_admin;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA ticket_system TO ticket_admin;

-- Mensagem de sucesso
DO $$
BEGIN
    RAISE NOTICE '✅ Database initialized successfully!';
    RAISE NOTICE '📊 Schema: ticket_system created';
    RAISE NOTICE '🤖 Ready for agents to create tables';
END $$;