-- =========================================
--  BusKa Database Initialization Script
--  PostgreSQL + PostGIS
-- =========================================

DROP DATABASE IF EXISTS buska_db;
DROP ROLE IF EXISTS buska_user;

CREATE ROLE buska_user WITH LOGIN PASSWORD 'buska_pass';
CREATE DATABASE buska_db OWNER buska_user ENCODING 'UTF8' TEMPLATE template0;

-- Connect to the new database (psql meta-command; works in docker-entrypoint-initdb.d)
\c buska_db;

-- --------- Enable required extensions ----------
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- --------- Create helper function for updated_at trigger ----------
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now() AT TIME ZONE 'UTC';
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- --------- Custom enum type for viagens ----------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_viagem') THEN
        CREATE TYPE tipo_viagem AS ENUM ('IDA', 'VOLTA');
    END IF;
END$$;

-- --------- Tables ----------

-- Municipios
CREATE TABLE IF NOT EXISTS municipios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL UNIQUE,
    uf CHAR(2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_municipios_nome ON municipios (nome);

-- Users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    senha_hash VARCHAR(200) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('aluno','motorista','gestor')),
    municipio_id INTEGER REFERENCES municipios (id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_municipio ON users (municipio_id);

-- Rotas
CREATE TABLE IF NOT EXISTS rotas (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    municipio_id INTEGER NOT NULL REFERENCES municipios (id) ON DELETE CASCADE,
    motorista_id INTEGER NOT NULL REFERENCES users (id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_rotas_municipio ON rotas (municipio_id);
CREATE INDEX IF NOT EXISTS idx_rotas_motorista ON rotas (motorista_id);

CREATE TABLE rotas_alunos (
    id SERIAL PRIMARY KEY,
    aluno_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rota_id INTEGER NOT NULL REFERENCES rotas(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC'),
    CONSTRAINT uq_aluno_rota UNIQUE (aluno_id, rota_id)
);

-- Pontos (pickup points) - use PostGIS geometry POINT
CREATE TABLE IF NOT EXISTS pontos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    -- store as geography/geometry; using geometry POINT with SRID 4326
    localizacao GEOMETRY(POINT,4326) NOT NULL,
    rota_id INTEGER NOT NULL REFERENCES rotas (id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC')
);

-- Create a spatial index for pontos.localizacao
CREATE INDEX IF NOT EXISTS idx_pontos_localizacao ON pontos USING GIST (localizacao);

-- Viagens (trips)
CREATE TABLE IF NOT EXISTS viagens (
    id SERIAL PRIMARY KEY,
    data DATE NOT NULL,
    horario_inicio TIMESTAMP WITH TIME ZONE,  -- set when driver starts (UTC)
    horario_fim TIMESTAMP WITH TIME ZONE,     -- set when driver finishes (UTC)
    tipo tipo_viagem NOT NULL,
    rota_id INTEGER NOT NULL REFERENCES rotas (id) ON DELETE CASCADE,
    motorista_id INTEGER NOT NULL REFERENCES users (id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_viagens_rota ON viagens (rota_id);
CREATE INDEX IF NOT EXISTS idx_viagens_motorista ON viagens (motorista_id);
CREATE INDEX IF NOT EXISTS idx_viagens_data ON viagens (data);

-- Presencas (attendance/confirmation)
CREATE TABLE IF NOT EXISTS viagens_alunos (
    id SERIAL PRIMARY KEY,
    aluno_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    viagem_id INTEGER NOT NULL REFERENCES viagens (id) ON DELETE CASCADE,
    confirmada BOOLEAN DEFAULT FALSE,
    cancelada BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC'),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC'),
    UNIQUE (aluno_id, viagem_id)
);

CREATE INDEX IF NOT EXISTS idx_viagens_alunos_viagem ON viagens_alunos (viagem_id);
CREATE INDEX IF NOT EXISTS idx_viagens_alunos_aluno ON viagens_alunos (aluno_id);

-- Notificacoes
CREATE TABLE IF NOT EXISTS notificacoes (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    titulo VARCHAR(120) NOT NULL,
    mensagem TEXT NOT NULL,
    enviada BOOLEAN DEFAULT FALSE,
    data_envio TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_notificacoes_usuario ON notificacoes (usuario_id);

-- --------- Triggers to update updated_at ----------
CREATE TRIGGER set_timestamp_municipios
BEFORE UPDATE ON municipios
FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();

CREATE TRIGGER set_timestamp_users
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();

CREATE TRIGGER set_timestamp_rotas
BEFORE UPDATE ON rotas
FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();

CREATE TRIGGER set_timestamp_pontos
BEFORE UPDATE ON pontos
FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();

CREATE TRIGGER set_timestamp_viagens
BEFORE UPDATE ON viagens
FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();

CREATE TRIGGER set_timestamp_viagens_alunos
BEFORE UPDATE ON viagens_alunos 
FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();

CREATE TRIGGER set_timestamp_notificacoes
BEFORE UPDATE ON notificacoes
FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();

-- --------- Grants ----------
GRANT ALL PRIVILEGES ON DATABASE buska_db TO buska_user;
GRANT USAGE, SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON ALL TABLES IN SCHEMA public TO buska_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO buska_user;

-- Ensure future tables and sequences are accessible
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO buska_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE ON SEQUENCES TO buska_user;

