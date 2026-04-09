#!/bin/sh
set -eu

ACCOUNT_SERVICE_DB_USER="${ACCOUNT_SERVICE_DB_USER:-account-service}"
ACCOUNT_SERVICE_DB_PASSWORD="${ACCOUNT_SERVICE_DB_PASSWORD:-account-service-password}"
ROUTER_DB_USER="${ROUTER_DB_USER:-router}"
ROUTER_DB_PASSWORD="${ROUTER_DB_PASSWORD:-router-password}"

psql \
    -v ON_ERROR_STOP=1 \
    --username "$POSTGRES_USER" \
    --dbname postgres \
    --set account_service_db_user="$ACCOUNT_SERVICE_DB_USER" \
    --set account_service_db_password="$ACCOUNT_SERVICE_DB_PASSWORD" \
    --set router_db_user="$ROUTER_DB_USER" \
    --set router_db_password="$ROUTER_DB_PASSWORD" <<'SQL'
SELECT format(
    'CREATE ROLE %I LOGIN PASSWORD %L',
    :'account_service_db_user',
    :'account_service_db_password'
)
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'account_service_db_user') \gexec

SELECT format(
    'ALTER ROLE %I WITH LOGIN PASSWORD %L',
    :'account_service_db_user',
    :'account_service_db_password'
)
WHERE EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'account_service_db_user') \gexec

SELECT format(
    'CREATE ROLE %I LOGIN PASSWORD %L',
    :'router_db_user',
    :'router_db_password'
)
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'router_db_user') \gexec

SELECT format(
    'ALTER ROLE %I WITH LOGIN PASSWORD %L',
    :'router_db_user',
    :'router_db_password'
)
WHERE EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'router_db_user') \gexec

SELECT format('CREATE DATABASE %I OWNER %I', 'deskconn_account_service', :'account_service_db_user')
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'deskconn_account_service') \gexec
SQL

psql \
    -v ON_ERROR_STOP=1 \
    --username "$POSTGRES_USER" \
    --dbname deskconn_account_service \
    --set account_service_db_user="$ACCOUNT_SERVICE_DB_USER" \
    --set router_db_user="$ROUTER_DB_USER" <<'SQL'
SELECT format('CREATE SCHEMA IF NOT EXISTS deskconn AUTHORIZATION %I', :'account_service_db_user') \gexec

SELECT format('GRANT CONNECT ON DATABASE %I TO %I', 'deskconn_account_service', :'account_service_db_user') \gexec
SELECT format('GRANT CREATE, TEMPORARY ON DATABASE %I TO %I', 'deskconn_account_service', :'account_service_db_user') \gexec

SELECT format('GRANT USAGE, CREATE ON SCHEMA %I TO %I', 'deskconn', :'account_service_db_user') \gexec
SELECT format('GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA %I TO %I', 'deskconn', :'account_service_db_user') \gexec
SELECT format('GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA %I TO %I', 'deskconn', :'account_service_db_user') \gexec
SELECT format(
    'ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA %I GRANT ALL PRIVILEGES ON TABLES TO %I',
    :'account_service_db_user',
    'deskconn',
    :'account_service_db_user'
) \gexec
SELECT format(
    'ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA %I GRANT ALL PRIVILEGES ON SEQUENCES TO %I',
    :'account_service_db_user',
    'deskconn',
    :'account_service_db_user'
) \gexec

SELECT format('GRANT CONNECT ON DATABASE %I TO %I', 'deskconn_account_service', :'router_db_user') \gexec
SELECT format('GRANT USAGE ON SCHEMA %I TO %I', 'deskconn', :'router_db_user') \gexec
SELECT format('GRANT SELECT ON ALL TABLES IN SCHEMA %I TO %I', 'deskconn', :'router_db_user') \gexec
SELECT format(
    'ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA %I GRANT SELECT ON TABLES TO %I',
    :'account_service_db_user',
    'deskconn',
    :'router_db_user'
) \gexec
SQL
