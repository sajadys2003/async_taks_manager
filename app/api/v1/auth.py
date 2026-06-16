
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import create_access_token
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    username: str
    password: str

@router.post("/register")
async def register(user_in: RegisterRequest):
    return {"message": f"User {user_in.username} registered successfully"}

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    access_token = create_access_token(
        data={"sub": "1", "role": "user"}
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer"
    }

