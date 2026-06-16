import json
import asyncio
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Header, Request, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.api.dependencies import get_db, get_redis, get_current_user, rate_limiter
from app.schemas.job import JobCreate, JobResponse, PaginatedJobResponse
from app.models.job import Job
from app.models.enums import JobStatus
from app.services.job_service import JobService
from app.core.config import get_mq_connection

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("", response_model=JobResponse, dependencies=[Depends(rate_limiter)])
async def create_job(
    job_in: JobCreate,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    mq_conn = await get_mq_connection()
    mq_channel = await mq_conn.channel()
    
    job_service = JobService(db, redis, mq_channel)
    result = await job_service.create_job(user.id, job_in.payload, idempotency_key)
    
    await mq_channel.close()
    await mq_conn.close()
    return result


@router.get("", response_model=PaginatedJobResponse)
async def list_jobs(
    cursor: Optional[int] = None,
    limit: int = 10,
    force_refresh: bool = False,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    cache_key = f"cache:jobs:user:{user.id}:first_page"
    
    if not cursor and not force_refresh:
        cached_data = await redis.get(cache_key)
        if cached_data:
            return json.loads(cached_data)

    query = select(Job).where(Job.user_id == user.id)
    if cursor:
        query = query.where(Job.id < cursor)
        
    query = query.order_by(Job.id.desc()).limit(limit + 1)
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    next_cursor = None
    if len(jobs) > limit:
        next_cursor = jobs[-2].id
        jobs = jobs[:-1]
        
    response_data = {
        "data": [job for job in jobs], 
        "next_cursor": next_cursor,
        "fetched_at": datetime.now(timezone.utc).isoformat()
    }
    
    if not cursor:
        cache_payload = PaginatedJobResponse(**response_data).model_dump_json()
        await redis.set(cache_key, cache_payload, ex=300)

    return response_data


@router.get("/stream")
async def stream_all_jobs_status(request: Request, user=Depends(get_current_user), redis: Redis = Depends(get_redis)):
    async def event_generator():
        pubsub = redis.pubsub()
        channel_name = f"user_job_updates:{user.id}"
        await pubsub.subscribe(channel_name)
        try:
            while True:
                if await request.is_disconnected():
                    break
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    status_data = message["data"]
                    yield f"data: {status_data}\n\n"
                await asyncio.sleep(0.5)
        finally:
            await pubsub.unsubscribe(channel_name)
            await pubsub.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{id}", response_model=JobResponse)
async def get_job(id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    job = await db.get(Job, id)
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/{id}/cancel")
async def cancel_job(id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    job = await db.get(Job, id)
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Cannot cancel a finished job")
        
    job.status = JobStatus.CANCELLED
    await db.commit()
    return {"message": "Job cancelled successfully"}


@router.get("/{id}/stream")
async def stream_single_job_status(
    id: int, 
    request: Request, 
    user=Depends(get_current_user),
    redis: Redis = Depends(get_redis)
):    
    async def event_generator():
        pubsub = redis.pubsub()
        channel_name = f"job_updates:{id}"
        await pubsub.subscribe(channel_name)
        try:
            while True:
                if await request.is_disconnected():
                    break
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    status_data = message["data"].decode("utf-8")
                    yield f"data: {status_data}\n\n"
                await asyncio.sleep(0.5)
        finally:
            await pubsub.unsubscribe(channel_name)
            await pubsub.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")