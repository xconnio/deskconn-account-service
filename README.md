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
ACCOUNT_SERVICE_DB_USER=account-service-password
ACCOUNT_SERVICE_DB_PASSWORD=random
ROUTER_DB_USER=router
ROUTER_DB_PASSWORD=router-password
DESKCONN_DATABASE_URL="postgresql+asyncpg://${ACCOUNT_SERVICE_DB_USER}:${ACCOUNT_SERVICE_DB_PASSWORD}@localhost:5432/deskconn_account_service"
DESKCONN_ACCOUNT_AUTHID=deskconn-account-service
DESKCONN_ACCOUNT_PRIVATE_KEY=db3f6235591a98b704f87f46f66d74645864479f32446a32d95c4826a6791b0a
```

3. Start Postgres and apply migrations:

```shell
make db
```

## Running the Service

```shell
make run
```
