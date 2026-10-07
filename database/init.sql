-- Este script é idempotente e roda em dois cenários (ver docker-compose.prod.yml
-- e infra/database.yml):
--
--   * dev:  POSTGRES_USER=postgres, sem POSTGRES_DB. Aqui o script cria o papel
--           buska_user e os bancos buska_db e buska_test.
--   * prod: POSTGRES_USER=buska_user, POSTGRES_DB=buska_db. A imagem do Postgres
--           já criou o papel e o banco antes de rodar este script.
--
-- O docker-entrypoint executa este arquivo com ON_ERROR_STOP. Um único
-- "already exists" derruba o script inteiro, e as extensões (uuid-ossp,
-- postgis) nunca são criadas: a primeira migração falha com
-- `function uuid_generate_v4() does not exist`. Por isso nada aqui pode falhar
-- só porque o papel ou o banco já existem.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'buska_user') THEN
        CREATE ROLE buska_user WITH LOGIN PASSWORD 'buska_pass';
    END IF;
END
$$;

-- CREATE DATABASE não roda dentro de DO/transação, então o comando é gerado
-- condicionalmente e executado pelo \gexec do psql.
SELECT 'CREATE DATABASE buska_db OWNER buska_user ENCODING ''UTF8'''
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'buska_db')\gexec

\c buska_db;

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

GRANT ALL PRIVILEGES ON DATABASE buska_db TO buska_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO buska_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO buska_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO buska_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO buska_user;

-- Banco separado para a suíte de testes. O fixture `_db` roda `drop_all()` no
-- fim de cada teste, então o alvo precisa ser um banco descartável. Enquanto a
-- suíte apontava para `buska_db`, cada rodada apagava o banco de desenvolvimento.
SELECT 'CREATE DATABASE buska_test OWNER buska_user ENCODING ''UTF8'''
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'buska_test')\gexec

\c buska_test;

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

GRANT ALL PRIVILEGES ON DATABASE buska_test TO buska_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO buska_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO buska_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO buska_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO buska_user;
