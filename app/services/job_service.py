import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.job import Job
from app.models.enums import JobStatus
from redis.asyncio import Redis
import aio_pika

class JobService:
    def __init__(self, db: AsyncSession, redis: Redis, mq_channel: aio_pika.Channel):
        self.db = db
        self.redis = redis
        self.mq_channel = mq_channel

    async def create_job(self, user_id: int, payload: str, idempotency_key: str):
        if idempotency_key:
            redis_key = f"idempotency:{user_id}:{idempotency_key}"
            cached_job = await self.redis.get(redis_key)
            if cached_job:
                return json.loads(cached_job)

        new_job = Job(user_id=user_id, status=JobStatus.PENDING, payload=payload)
        self.db.add(new_job)
        await self.db.commit()
        await self.db.refresh(new_job)

        msg = json.dumps({"job_id": new_job.id, "user_id": user_id}).encode()
        await self.mq_channel.default_exchange.publish(
            aio_pika.Message(body=msg), routing_key="job_queue"
        )

        job_dict = {
            "id": new_job.id,
            "user_id": new_job.user_id,
            "status": new_job.status.value,
            "payload": new_job.payload,
            "time_created": new_job.time_created.isoformat() if new_job.time_created else datetime.now(timezone.utc).isoformat(),
            "time_started": None,
            "time_done": None
        }

        if idempotency_key:
            await self.redis.set(redis_key, json.dumps(job_dict), ex=86400)
        
        await self.redis.delete(f"cache:jobs:user:{user_id}:first_page")
        
        return job_dict