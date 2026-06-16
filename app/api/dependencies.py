from fastapi import Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
import jwt
from app.core.config import async_session_maker, get_redis_client
from app.core.security import SECRET_KEY, ALGORITHM
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

async def get_db():
    async with async_session_maker() as session:
        yield session

async def get_redis():
    client = await get_redis_client()
    try:
        yield client
    finally:
        await client.close()

class AuthenticatedUser:
    def __init__(self, id: int, role: str):
        self.id = id
        self.role = role

async def get_current_user(
    header_token: str = Depends(oauth2_scheme),
    query_token: str = Query(None, alias="token")
):
    token = header_token or query_token
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return AuthenticatedUser(id=int(user_id), role=role)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def rate_limiter(user=Depends(get_current_user), redis: Redis = Depends(get_redis)):
    key = f"rate_limit:user:{user.id}:jobs"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 60)
    if count > 10:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Max 10 per minute.")
    return True