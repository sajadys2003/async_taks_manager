from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import select

from app.api.v1 import auth, jobs
from app.core.config import async_session_maker
from app.models.user import User
from app.models.enums import UserRole
from app.core.security import get_password_hash

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Executes on server startup to ensure the permanent Admin exists."""
    print("Starting up: Checking for default Admin user...")
    async with async_session_maker() as db:
        result = await db.execute(select(User).where(User.username == "admin"))
        admin = result.scalar_one_or_none()
        
        if not admin:
            print("Admin not found. Creating permanent 'admin' user...")
            hashed_pw = get_password_hash("admin123")
            new_admin = User(username="admin", hashed_password=hashed_pw, role=UserRole.ADMIN)
            db.add(new_admin)
            await db.commit()
    yield

app = FastAPI(title="Cloud Resource Management API", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(jobs.router)

@app.get("/")
def root():
    return {"message": "API is running"}