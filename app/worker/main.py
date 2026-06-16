import asyncio
import json
import traceback
from datetime import datetime, timezone
from sqlalchemy import select, func, update, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.job import Job
from app.models.enums import JobStatus
from app.core.config import async_session_maker, get_mq_connection, get_redis_client

MAX_CONCURRENT_JOBS = 3
MAX_RETRIES = 3

async def publish_status(redis, job_id: int, user_id: int, status: JobStatus):
    await redis.publish(f"job_updates:{job_id}", status.value)
    payload = json.dumps({"job_id": job_id, "status": status.value})
    await redis.publish(f"user_job_updates:{user_id}", payload)

async def process_job(message_body: bytes, db: AsyncSession, mq_channel, redis):
    data = json.loads(message_body)
    job_id = data['job_id']
    user_id = data['user_id']
    
    await db.execute(text("SELECT pg_advisory_xact_lock(:uid)"), {"uid": user_id})
    job = await db.get(Job, job_id)
    
    if not job or job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]: 
        return

    if job.status in [JobStatus.PENDING, JobStatus.QUEUED]:
        running_count = await db.scalar(
            select(func.count()).where(Job.user_id == user_id, Job.status == JobStatus.RUNNING)
        )

        if running_count >= MAX_CONCURRENT_JOBS:
            job.status = JobStatus.QUEUED
            await db.commit() 
            await publish_status(redis, job_id, user_id, JobStatus.QUEUED)
            return

        job.status = JobStatus.RUNNING
        job.time_started = datetime.now(timezone.utc)
        await db.commit() 
        await publish_status(redis, job_id, user_id, JobStatus.RUNNING)
    else:
        await db.commit()

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await asyncio.sleep(15)
            
            job.status = JobStatus.COMPLETED
            job.time_done = datetime.now(timezone.utc)
            await db.commit()
            await publish_status(redis, job_id, user_id, JobStatus.COMPLETED)
            break
        except Exception:
            if attempt == MAX_RETRIES:
                job.status = JobStatus.FAILED
                job.time_done = datetime.now(timezone.utc)
                await db.commit()
                await publish_status(redis, job_id, user_id, JobStatus.FAILED)
            else:
                await asyncio.sleep(2 ** attempt)

    subq = (
        select(Job.id)
        .where(Job.user_id == user_id, Job.status == JobStatus.QUEUED)
        .order_by(Job.id.asc())
        .limit(1)
        .with_for_update(skip_locked=True)
        .scalar_subquery()
    )

    update_stmt = (
        update(Job)
        .where(Job.id == subq)
        .values(status=JobStatus.PENDING)
        .returning(Job.id)
    )
    
    result = await db.execute(update_stmt)
    woken_job_id = result.scalar()
    await db.commit()
    
    if woken_job_id:
        msg = json.dumps({"job_id": woken_job_id, "user_id": user_id}).encode()
        import aio_pika
        await mq_channel.default_exchange.publish(aio_pika.Message(body=msg), routing_key="job_queue")


async def handle_message(message, mq_channel, redis):
    try:
        async with message.process():
            async with async_session_maker() as db:
                await process_job(message.body, db, mq_channel, redis)
    except Exception as e:
        print(f"\n🔥 ERROR: {e}\n")
        traceback.print_exc()

async def main():
    connection = await get_mq_connection()
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=50)
    
    queue = await channel.declare_queue("job_queue", durable=True)
    redis = await get_redis_client()
    
    print("Worker is listening concurrently...")

    async with queue.iterator() as q_iter:
        async for message in q_iter:
            asyncio.create_task(handle_message(message, channel, redis))

if __name__ == "__main__":
    asyncio.run(main())