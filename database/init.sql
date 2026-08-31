CREATE ROLE buska_user WITH LOGIN PASSWORD 'buska_pass';

CREATE DATABASE buska_db OWNER buska_user ENCODING 'UTF8';

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
CREATE DATABASE buska_test OWNER buska_user ENCODING 'UTF8';

\c buska_test;

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

GRANT ALL PRIVILEGES ON DATABASE buska_test TO buska_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO buska_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO buska_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO buska_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO buska_user;
