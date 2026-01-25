import chromadb
from chromadb.utils import embedding_functions
from fastapi import APIRouter, Depends, HTTPException,Request
ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(
    name="documents",
    embedding_function=ef
)

def get_current_user_id(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user_id