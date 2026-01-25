
#         messages.extend(request.history)
#         messages.append({"role": "user", "content": request.user_message})
#
#         response = client.chat.completions.create(
#             # Tên model trên Groq (Khác với tên model embedding nhé!)
#             model="qwen2.5:7b",
#             messages=messages,
#             temperature=0.7
#         )
#
#         return {
#             "reply": response.choices[0].message.content,
#             "context": knowledge
#         }
#
#     except Exception as e:
#         print(f"Lỗi: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from sqlalchemy import select
from fastapi.middleware.cors import CORSMiddleware
# Routers
# from api.lesson import router as lesson_router
from api.document import router as document_router
from api.tutor import router as tutor_router
from api.auth import router as auth_router
from api.progress import router as progress_router
from api.assignments import router as assignments_router
from api.lessons import router as lessons_router
# from app.api.admin import router as admin_router  # learning_units
from fastapi import FastAPI, Request
import time
import uuid

from core.database import AsyncSessionLocal
from models import User

app = FastAPI(
    title="Tutor AI Backend",
    version="0.1.0"
)
EXEMPT_PATHS = {"/api/auth/register", "/api/auth/login"}

@app.middleware("http")
async def require_authentication(request: Request, call_next):
    path = request.url.path

    # Chỉ bảo vệ /api/*
    if not path.startswith("/api/"):
        return await call_next(request)

    # Bỏ qua các endpoint public
    if path in EXEMPT_PATHS:
        return await call_next(request)

    # Lấy Bearer token
    auth = request.headers.get("Authorization", "")
    if not auth.lower().startswith("bearer "):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    token = auth.split(" ", 1)[1].strip()
    if not token:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    # Verify JWT
    try:
        payload = jwt.decode(token, "MySecret", algorithms="HS256")
        user_id = payload.get("sub")
        role = payload.get("role")

        if not user_id:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        request.state.user_id = str(user_id)


    except JWTError:
        return JSONResponse(status_code=401, content={"detail": "Invalid token"})

    return await call_next(request)


@app.middleware("http")
async def add_request_metadata(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = str(uuid.uuid4())
    response.headers["X-Process-Time"] = f"{time.perf_counter() - start_time:.4f}"
    return response

# -----------------------------
# CORS (cho frontend sau này)
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Session-Id"],

)

# -----------------------------
# ROUTERS
# -----------------------------
# app.include_router(lesson_router)
app.include_router(document_router)
app.include_router(tutor_router)
app.include_router(auth_router)
app.include_router(progress_router)
app.include_router(assignments_router)
app.include_router(lessons_router)
# app.include_router(admin_router)

# -----------------------------
# HEALTH CHECK
# -----------------------------
@app.get("/")
def root():
    return {"status": "ok"}