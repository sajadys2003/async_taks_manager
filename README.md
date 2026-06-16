# Modern Async Task Management API

A distributed, asynchronous API for managing and executing background jobs. Built with FastAPI, asynchronous PostgreSQL (asyncpg), Redis, and RabbitMQ.

Technical Detail:
Web Framework: FastAPI (Python 3.11)
Database: PostgreSQL with SQLAlchemy 2.0 (Async)
Message Broker: RabbitMQ (aio-pika)
Caching & Rate Limiting: Redis
DB Migrations: Alembic
Containerization: Docker & Docker Compose

Quick Deployment & Use:

1. Clone or extract the repository.
2. Ensure Docker and Docker Compose are installed.
3. Run the following command in the root directory:
   docker-compose up -d --build
