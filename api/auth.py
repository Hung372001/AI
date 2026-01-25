from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException,Request
from grpc.beta.implementations import access_token_call_credentials
from psutil import users
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import generate_token, hash_password, verify_password, create_access_token
from models import UserProfile
from models.user import User
from services.chroma_service import get_current_user_id

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
    accessToken: str
    token_type: str = "bearer"
    expires_in: int = 3600


class ProfileResponse(BaseModel):
    id: str
    email: EmailStr
    name: str | None
    role: str
    grade_level: int | None = None
    learning_goals: str | None = None
    preferred_style: str | None = None


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
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        data={
            "sub": str(user.id),  # subject (user id)
            "email": user.email,
            "role": user.role
        },
        expires_delta=timedelta(hours=24),
    )
    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    return LoginResponse(accessToken=access_token, token_type="bearer", expires_in=3600)


@router.get("/profile" ,response_model=ProfileResponse)
async def get_profile( db: AsyncSession = Depends(get_db),user_id: str = Depends( get_current_user_id)):
    userID = user_id
    print(userID)
    user_result = await db.execute(select(User).where(User.id == userID))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == userID)
    )
    profile = profile_result.scalar_one_or_none()

    return ProfileResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        grade_level=profile.grade_level if profile else None,
        learning_goals=profile.learning_goals if profile else None,
        preferred_style=profile.preferred_style if profile else None,
    )