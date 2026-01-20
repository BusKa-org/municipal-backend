-- =========================================
--  BusKa Database Initialization Script
--  PostgreSQL + PostGIS
-- =========================================

DROP DATABASE IF EXISTS buska_db;
DROP ROLE IF EXISTS buska_user;

CREATE ROLE buska_user WITH LOGIN PASSWORD 'buska_pass';
CREATE DATABASE buska_db OWNER buska_user ENCODING 'UTF8' TEMPLATE template0;

\c buska_db;

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now() AT TIME ZONE 'UTC';
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TYPE dia_da_semana AS ENUM ('SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB', 'DOM');
CREATE TYPE sentido_viagem AS ENUM ('IDA', 'VOLTA', 'CIRCULAR');
CREATE TYPE status_viagem AS ENUM ('AGENDADA', 'EM_ANDAMENTO', 'FINALIZADA', 'CANCELADA');
CREATE TYPE user_role AS ENUM ('USER', 'ALUNO', 'MOTORISTA', 'GESTOR');
CREATE TYPE tipo_instituicao AS ENUM ('INSTITUTO_FEDERAL','UNIVERSIDADE_PUBLICA','UNIVERSIDADE_PRIVADA','ESCOLA_PUBLICA','ESCOLA_PRIVADA','ESCOLA_COMUNITARIA');

CREATE TABLE prefeitura (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nome VARCHAR(150) NOT NULL,
    estado VARCHAR(2) NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC')
);

CREATE TABLE ponto (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prefeitura_id UUID NOT NULL REFERENCES prefeitura(id) ON DELETE CASCADE,
    latitude NUMERIC(10, 8) NOT NULL,
    longitude NUMERIC(11, 8) NOT NULL,
    apelido VARCHAR(100),
    geom GEOMETRY(POINT, 4326) GENERATED ALWAYS AS (ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)) STORED,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC')
);
CREATE INDEX idx_ponto_geom ON ponto USING GIST (geom);

CREATE TABLE endereco (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    logradouro VARCHAR(150),
    numero VARCHAR(20),
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    cep VARCHAR(10),
    ponto_id UUID REFERENCES ponto(id) ON DELETE SET NULL
);

CREATE TABLE instituicao (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nome VARCHAR(150) NOT NULL,
    cnpj VARCHAR(20),
    tipo tipo_instituicao NOT NULL DEFAULT 'ESCOLA_PUBLICA',
    ponto_id UUID NOT NULL REFERENCES ponto(id) ON DELETE CASCADE
);

CREATE TABLE usuario (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),    
    prefeitura_id UUID NOT NULL REFERENCES prefeitura(id) ON DELETE CASCADE,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    telefone VARCHAR(20),
    cpf VARCHAR(14) NOT NULL UNIQUE,
    role user_role NOT NULL DEFAULT 'ALUNO',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC')
);
CREATE INDEX idx_usuario_prefeitura ON usuario(prefeitura_id);

CREATE TABLE motorista (
    usuario_id UUID PRIMARY KEY REFERENCES usuario(id) ON DELETE CASCADE,
    cnh VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE gestor (
    usuario_id UUID PRIMARY KEY REFERENCES usuario(id) ON DELETE CASCADE,
    matricula VARCHAR(50),
    salario NUMERIC(10, 2)
);

CREATE TABLE aluno (
    usuario_id UUID PRIMARY KEY REFERENCES usuario(id) ON DELETE CASCADE,
    matricula VARCHAR(50),
    nome_pai VARCHAR(100),
    cpf_pai VARCHAR(14),
    nome_mae VARCHAR(100),
    cpf_mae VARCHAR(14),
    instituicao_id UUID REFERENCES instituicao(id),
    ponto_casa_id UUID REFERENCES ponto(id)
);

CREATE TABLE onibus (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prefeitura_id UUID NOT NULL REFERENCES prefeitura(id) ON DELETE CASCADE,
    placa VARCHAR(10) NOT NULL UNIQUE,
    modelo VARCHAR(50),
    capacidade INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC')
);

CREATE TABLE rota (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prefeitura_id UUID NOT NULL REFERENCES prefeitura(id) ON DELETE CASCADE,    
    nome VARCHAR(100) NOT NULL,
    motorista_padrao_id UUID REFERENCES motorista(usuario_id) ON DELETE SET NULL,
    veiculo_padrao_id UUID REFERENCES onibus(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC')
);

CREATE TABLE rota_ponto (
    rota_id UUID REFERENCES rota(id) ON DELETE CASCADE,
    ponto_id UUID REFERENCES ponto(id) ON DELETE RESTRICT,
    ordem INTEGER NOT NULL,
    PRIMARY KEY (rota_id, ponto_id)
);

CREATE TABLE rota_aluno (
    rota_id UUID REFERENCES rota(id) ON DELETE CASCADE,
    aluno_id UUID REFERENCES aluno(usuario_id) ON DELETE CASCADE,
    data_inscricao TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (rota_id, aluno_id)
);

CREATE TABLE horario_rota (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rota_id UUID NOT NULL REFERENCES rota(id) ON DELETE CASCADE,
    horario_saida TIME NOT NULL,
    sentido sentido_viagem NOT NULL
);

CREATE TABLE dias_operacao (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    horario_rota_id UUID NOT NULL REFERENCES horario_rota(id) ON DELETE CASCADE,
    dia dia_da_semana NOT NULL
);

CREATE TABLE viagem (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    data DATE NOT NULL,
    horario_rota_id UUID REFERENCES horario_rota(id) ON DELETE SET NULL,
    motorista_id UUID REFERENCES motorista(usuario_id) ON DELETE RESTRICT,
    veiculo_id UUID REFERENCES onibus(id) ON DELETE RESTRICT,
    status status_viagem DEFAULT 'AGENDADA',
    inicio_real TIMESTAMP WITH TIME ZONE,
    fim_real TIMESTAMP WITH TIME ZONE,
    km_real NUMERIC(10, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC')
);

CREATE TABLE viagem_ponto (
    viagem_id UUID REFERENCES viagem(id) ON DELETE CASCADE,
    ponto_id UUID REFERENCES ponto(id) ON DELETE RESTRICT,
    ordem INTEGER NOT NULL,
    visitado BOOLEAN DEFAULT FALSE,
    chegada_estimada TIMESTAMP WITH TIME ZONE,
    chegada_real TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (viagem_id, ponto_id)
);

CREATE TABLE alunos_confirmados (
    viagem_id UUID REFERENCES viagem(id) ON DELETE CASCADE,
    aluno_id UUID REFERENCES aluno(usuario_id) ON DELETE CASCADE,
    confirmacao BOOLEAN DEFAULT TRUE,
    ponto_embarque_id UUID REFERENCES ponto(id),
    ponto_destino_id UUID REFERENCES ponto(id),
    PRIMARY KEY (viagem_id, aluno_id)
);

-- 6. EXTRAS & TRIGGERS
CREATE TABLE notificacoes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    titulo VARCHAR(120) NOT NULL,
    mensagem TEXT NOT NULL,
    enviada BOOLEAN DEFAULT FALSE,
    data_envio TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (now() AT TIME ZONE 'UTC')
);
CREATE INDEX idx_notificacoes_usuario ON notificacoes (usuario_id);

CREATE TRIGGER set_timestamp_usuario BEFORE UPDATE ON usuario FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();
CREATE TRIGGER set_timestamp_rota BEFORE UPDATE ON rota FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();
CREATE TRIGGER set_timestamp_viagem BEFORE UPDATE ON viagem FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();

GRANT ALL PRIVILEGES ON DATABASE buska_db TO buska_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO buska_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO buska_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO buska_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO buska_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO buska_user;

ALTER TABLE prefeitura OWNER TO buska_user;
ALTER TABLE usuario OWNER TO buska_user;
ALTER TABLE aluno OWNER TO buska_user;
ALTER TABLE motorista OWNER TO buska_user;
ALTER TABLE gestor OWNER TO buska_user;
ALTER TABLE ponto OWNER TO buska_user;
ALTER TABLE endereco OWNER TO buska_user;
ALTER TABLE instituicao OWNER TO buska_user;
ALTER TABLE onibus OWNER TO buska_user;
ALTER TABLE rota OWNER TO buska_user;
ALTER TABLE rota_ponto OWNER TO buska_user;
ALTER TABLE rota_aluno OWNER TO buska_user;
ALTER TABLE horario_rota OWNER TO buska_user;
ALTER TABLE dias_operacao OWNER TO buska_user;
ALTER TABLE viagem OWNER TO buska_user;
ALTER TABLE viagem_ponto OWNER TO buska_user;
ALTER TABLE alunos_confirmados OWNER TO buska_user;
ALTER TABLE ocorrencia OWNER TO buska_user;
ALTER TABLE notificacoes OWNER TO buska_user;