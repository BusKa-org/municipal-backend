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
CREATE TYPE dia_da_semana AS ENUM (
    'SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB', 'DOM'
);

CREATE TYPE sentido_viagem AS ENUM (
    'LEVAR', -- Levar para Instituição
    'BUSCAR', -- Buscar para Casa
    'LEVAR_E_TRAZER' -- Circular
);

CREATE TYPE status_viagem AS ENUM (
    'AGENDADA',
    'EM_ANDAMENTO',
    'FINALIZADA',
    'CANCELADA'
);

-- --------- Tables ----------

-- Users
CREATE TABLE usuario (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    telefone VARCHAR(20),
    cpf VARCHAR(14) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC')
);

CREATE TABLE aluno (
    usuario_id INTEGER PRIMARY KEY REFERENCES usuario(id) ON DELETE CASCADE,
    matricula VARCHAR(50),
    nome_pai VARCHAR(100),
    nome_mae VARCHAR(100)
);

-- Perfil: Motorista
CREATE TABLE motorista (
    usuario_id INTEGER PRIMARY KEY REFERENCES usuario(id) ON DELETE CASCADE,
    cnh VARCHAR(20) NOT NULL UNIQUE
);

-- Perfil: Gestor
CREATE TABLE gestor (
    usuario_id INTEGER PRIMARY KEY REFERENCES usuario(id) ON DELETE CASCADE,
    matricula VARCHAR(50),
    salario NUMERIC(10, 2)
);

-- Pontos (pickup points) - use PostGIS geometry POINT
CREATE TABLE ponto (
    id SERIAL PRIMARY KEY,
    latitude NUMERIC(10, 8) NOT NULL,
    longitude NUMERIC(11, 8) NOT NULL,
    apelido VARCHAR(100),
    geom GEOMETRY(POINT, 4326) GENERATED ALWAYS AS (ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)) STORED,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC')
);
CREATE INDEX idx_ponto_geom ON ponto USING GIST (geom);

CREATE TABLE endereco (
    id SERIAL PRIMARY KEY,
    logradouro VARCHAR(150),
    numero VARCHAR(20),
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    cep VARCHAR(10),
    ponto_id INTEGER REFERENCES ponto(id) ON DELETE SET NULL
);

CREATE TABLE instituicao (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    cnpj VARCHAR(20) NOT NULL UNIQUE,
    ponto_id INTEGER NOT NULL REFERENCES ponto(id) ON DELETE RESTRICT
);

CREATE TABLE onibus (
    id SERIAL PRIMARY KEY,
    placa VARCHAR(10) NOT NULL UNIQUE,
    modelo VARCHAR(50),
    capacidade INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC')
);

CREATE TABLE rota (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    motorista_padrao_id INTEGER REFERENCES motorista(usuario_id) ON DELETE SET NULL,
    veiculo_padrao_id INTEGER REFERENCES onibus(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC')
);

CREATE TABLE rota_ponto (
    rota_id INTEGER REFERENCES rota(id) ON DELETE CASCADE,
    ponto_id INTEGER REFERENCES ponto(id) ON DELETE RESTRICT,
    ordem INTEGER NOT NULL,
    PRIMARY KEY (rota_id, ponto_id)
);

CREATE TABLE horario_rota (
    id SERIAL PRIMARY KEY,
    rota_id INTEGER NOT NULL REFERENCES rota(id) ON DELETE CASCADE,
    horario_saida TIME NOT NULL,
    sentido sentido_viagem NOT NULL
);

CREATE TABLE dias_operacao (
    id SERIAL PRIMARY KEY,
    horario_rota_id INTEGER NOT NULL REFERENCES horario_rota(id) ON DELETE CASCADE,
    dia dia_da_semana NOT NULL
);

-- Viagens (trips)
CREATE TABLE viagem (
    id SERIAL PRIMARY KEY,
    data DATE NOT NULL,
    
    -- Origem do agendamento
    horario_rota_id INTEGER REFERENCES horario_rota(id) ON DELETE SET NULL,
    
    motorista_id INTEGER REFERENCES motorista(usuario_id) ON DELETE RESTRICT,
    veiculo_id INTEGER REFERENCES onibus(id) ON DELETE RESTRICT,
    
    status status_viagem DEFAULT 'AGENDADA',
    inicio_real TIMESTAMP WITH TIME ZONE,
    fim_real TIMESTAMP WITH TIME ZONE,
    km_real NUMERIC(10, 2),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC')
);

CREATE TABLE viagem_ponto (
    viagem_id INTEGER REFERENCES viagem(id) ON DELETE CASCADE,
    ponto_id INTEGER REFERENCES ponto(id) ON DELETE RESTRICT,
    ordem INTEGER NOT NULL,
    visitado BOOLEAN DEFAULT FALSE,
    chegada_estimada TIMESTAMP WITH TIME ZONE,
    chegada_real TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (viagem_id, ponto_id)
);

-- Presencas (attendance/confirmation)
CREATE TABLE alunos_confirmados (
    viagem_id INTEGER REFERENCES viagem(id) ON DELETE CASCADE,
    aluno_id INTEGER REFERENCES aluno(usuario_id) ON DELETE CASCADE,
    confirmacao BOOLEAN DEFAULT TRUE,
    ponto_embarque_id INTEGER REFERENCES ponto(id),
    ponto_destino_id INTEGER REFERENCES ponto(id),
    PRIMARY KEY (viagem_id, aluno_id)
);

-- Notificacoes
CREATE TABLE IF NOT EXISTS notificacoes (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuario (id) ON DELETE CASCADE, 
    titulo VARCHAR(120) NOT NULL,
    mensagem TEXT NOT NULL,
    enviada BOOLEAN DEFAULT FALSE,
    data_envio TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_notificacoes_usuario ON notificacoes (usuario_id);

-- --------- Triggers to update updated_at ----------
CREATE TRIGGER set_timestamp_usuario BEFORE UPDATE ON usuario FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();
CREATE TRIGGER set_timestamp_rota BEFORE UPDATE ON rota FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();
CREATE TRIGGER set_timestamp_viagem BEFORE UPDATE ON viagem FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();

-- --------- Grants ----------
GRANT ALL PRIVILEGES ON DATABASE buska_db TO buska_user;
GRANT USAGE, SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON ALL TABLES IN SCHEMA public TO buska_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO buska_user;

