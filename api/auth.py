from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import generate_token, hash_password, verify_password
from models.user import User

router = APIRouter(prefix="/api/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str | None = None
    password: str = Field(..., min_length=8)


class RegisterResponse(BaseModel):
    id: str
    email: EmailStr
    name: str | None
    role: str
    created_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


@router.post("/register", response_model=RegisterResponse)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=payload.email,
        name=payload.name,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return RegisterResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        created_at=user.created_at,
    )


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    return LoginResponse(access_token=generate_token())
