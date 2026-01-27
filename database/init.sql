-- =========================================
--  BusKa Database Initialization
--  Creates role, database, and extensions
--  Run automatically by Docker on first start
-- =========================================

-- Create application user
CREATE ROLE buska_user WITH LOGIN PASSWORD 'buska_pass';

-- Create application database
CREATE DATABASE buska_db OWNER buska_user ENCODING 'UTF8';

-- Connect to the new database and set up extensions
\c buska_db;

-- Enable extensions (as superuser)
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant privileges to application user
GRANT ALL PRIVILEGES ON DATABASE buska_db TO buska_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO buska_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO buska_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO buska_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO buska_user;
