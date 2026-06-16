from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.api.dependencies import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.models.enums import UserRole

router = APIRouter(prefix="/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    username: str
    password: str

@router.post("/register")
async def register(user_in: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Registers a new standard user in the database."""
    # 1. Check if username already exists
    result = await db.execute(select(User).where(User.username == user_in.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # 2. Hash the password and save the user
    hashed_pw = get_password_hash(user_in.password)
    new_user = User(username=user_in.username, hashed_password=hashed_pw, role=UserRole.USER)
    
    db.add(new_user)
    await db.commit()
    return {"message": f"User {user_in.username} registered successfully"}

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Verifies credentials and returns a real JWT token."""
    # 1. Find user in the database
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    
    # 2. Verify password
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect username or password"
        )
    
    # 3. Generate JWT containing their REAL database ID and Role
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}