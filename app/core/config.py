import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import redis.asyncio as redis
import aio_pika

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@db:5432/jobs_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

async def get_redis_client():
    return redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

async def get_mq_connection():
    for _ in range(10):
        try:
            return await aio_pika.connect_robust(RABBITMQ_URL)
        except Exception:
            print("RabbitMQ not fully ready yet. Waiting 3 seconds...")
            await asyncio.sleep(3)
    raise Exception("Could not connect to RabbitMQ after 30 seconds")
