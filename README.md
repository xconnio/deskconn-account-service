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
DESKCONN_DBPATH=deskconn.db
DESKCONN_ACCOUNT_AUTHID=deskconn-account-service
DESKCONN_ACCOUNT_PRIVATE_KEY=db3f6235591a98b704f87f46f66d74645864479f32446a32d95c4826a6791b0a
DESKCONN_EMAIL=email
DESKCONN_PASSWORD=password
```

## Running the Service

```shell
make run
```
