# import os
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel, Field
# import chromadb
# from chromadb.utils import embedding_functions
# from openai import OpenAI
#
# app = FastAPI()
#
# # ---------------------------------------------------------
# # 1. CẤU HÌNH CLIENT (Kết hợp Groq & Local)
# # ---------------------------------------------------------
#
# # A. Cấu hình Chat Client (Dùng Groq cho nhanh)
# # Lưu ý: Thay 'gsk_...' bằng Key thật của bạn
# GROQ_API_KEY = "gsk_..."
# client = OpenAI(
#     base_url="http://localhost:11434/v1",
#     api_key=GROQ_API_KEY
# )
#
# # B. Cấu hình Embedding (Dùng Local - Model MiniLM)
# # Đừng đổi tên model này, nó là model chuẩn để vector hóa
# ef = embedding_functions.SentenceTransformerEmbeddingFunction(
#     model_name="all-MiniLM-L6-v2"
# )
#
# # C. Cấu hình DB
# chroma_client = chromadb.Client()
# collection = chroma_client.get_or_create_collection(
#     name="math_knowledge",
#     embedding_function=ef
# )
#
# # ---------------------------------------------------------
# # 2. NẠP DỮ LIỆU MẪU
# # ---------------------------------------------------------
# if collection.count() == 0:
#     print(">>> Đang nạp dữ liệu mẫu...")
#     textbook_data = [
#         {"id": "doc1",
#          "content": "Định lý Pitago: Trong tam giác vuông, bình phương cạnh huyền bằng tổng bình phương hai cạnh góc vuông (c^2 = a^2 + b^2)."},
#         {"id": "doc2", "content": "Diện tích hình tròn: S = r^2 * 3.14 (với r là bán kính)."},
#     ]
#     collection.add(
#         documents=[item["content"] for item in textbook_data],
#         ids=[item["id"] for item in textbook_data]
#     )
#
#
# # ---------------------------------------------------------
# # 3. API
# # ---------------------------------------------------------
# class ChatRequest(BaseModel):
#     user_message: str
#     history: list = Field(default_factory=list)
#
#
# @app.post("/api/tutor-chat")
# async def chat_endpoint(request: ChatRequest):
#     try:
#         # Bước 1: Tìm kiếm Vector (Dùng model MiniLM chạy local)
#         results = collection.query(query_texts=[request.user_message], n_results=1)
#         knowledge = results['documents'][0][0] if results['documents'] else "Không có thông tin."
#
#         # Bước 2: Gọi Groq để trả lời (Dùng model Llama 3 trên Cloud)
#         system_prompt = f"""
#         Bạn là gia sư AI. Hãy trả lời ngắn gọn bằng tiếng Việt.
#         Kiến thức tham khảo: {knowledge}
#         """
#
#         messages = [{"role": "system", "content": system_prompt}]
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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers
# from api.lesson import router as lesson_router
from api.document import router as document_router
# from app.api.admin import router as admin_router  # learning_units

app = FastAPI(
    title="Tutor AI Backend",
    version="0.1.0"
)

# -----------------------------
# CORS (cho frontend sau này)
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# ROUTERS
# -----------------------------
# app.include_router(lesson_router)
app.include_router(document_router)
# app.include_router(admin_router)

# -----------------------------
# HEALTH CHECK
# -----------------------------
@app.get("/")
def root():
    return {"status": "ok"}
