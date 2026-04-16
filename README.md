# Deskconn Account Service

Deskconn Account Service manages user accounts, devices, and desktop information.

## Getting Started

Before starting this service, make sure the [Deskconn Router](https://github.com/xconnio/deskconn-router) is running.

## Setup Instructions

1. Install dependencies:

```shell
make setup
```

2. Configure environment variables:

Create or edit the `.env` file with appropriate values:

```dotenv
ACCOUNT_SERVICE_DB_USER=account-service
ACCOUNT_SERVICE_DB_PASSWORD=account-service-password
ROUTER_DB_USER=router
ROUTER_DB_PASSWORD=router-password
DESKCONN_POSTGRES_HOST=localhost
DESKCONN_DATABASE_URL=postgresql+asyncpg://${ACCOUNT_SERVICE_DB_USER}:${ACCOUNT_SERVICE_DB_PASSWORD}@${DESKCONN_POSTGRES_HOST}:5432/deskconn_account_service
DESKCONN_ACCOUNT_AUTHID=deskconn-account-service
DESKCONN_ACCOUNT_PRIVATE_KEY=db3f6235591a98b704f87f46f66d74645864479f32446a32d95c4826a6791b0a
ROUTER_URL=ws://localhost:8080/ws
```

3. Start Postgres and apply migrations:

```shell
make db
```

## Running the Service

```shell
make run
```

## Running with Docker

Before running with Docker, make sure [Deskconn Router](https://github.com/xconnio/deskconn-router) is already running via its own `docker-compose.yml`.

Set these values in your `.env` for Docker:

```dotenv
# Use the container name for postgres (same docker-compose network)
DESKCONN_POSTGRES_HOST=deskconn-account-service-postgres

# Use host.docker.internal to reach the router running on the host
ROUTER_URL=ws://host.docker.internal:8080/ws
```

Then start the service:

```shell
make run-docker
```
