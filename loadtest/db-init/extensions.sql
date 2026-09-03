-- Runs after database/init.sql inside docker-entrypoint-initdb.d (mounted
-- with a filename that sorts after it — see docker-compose.loadtest.yml).
--
-- database/init.sql's first statement (`CREATE ROLE buska_user ...`) fails
-- whenever POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB env vars already
-- pre-created that role (which both docker-compose.prod.yml and
-- docker-compose.loadtest.yml do), which aborts the rest of that script
-- under Postgres's default ON_ERROR_STOP behavior for init scripts — so
-- `uuid-ossp` (needed by every UUID-default-valued column, e.g.
-- prefeitura.id) never actually gets created. This is a real, observed gap
-- in database/init.sql, not specific to the load-test env — flagged in the
-- wrap-up report — but fixing it here rather than touching prod's init.sql
-- to keep this change scoped to load testing.
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
