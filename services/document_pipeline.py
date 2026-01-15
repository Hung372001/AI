from sqlalchemy.ext.asyncio import AsyncSession
from models.document_chunk import DocumentChunk
from services.chroma_service import collection
from services.chunking import chunk_text
from services.document_loader import load_pdf, load_docx
import os

async def process_document(document, db: AsyncSession):
    path = document.file_path
    ext = os.path.splitext(path)[-1].lower()

    if ext == ".pdf":
        text = load_pdf(path)
    elif ext in [".doc", ".docx"]:
        text = load_docx(path)
    else:
        raise ValueError("Unsupported file type")

    chunks = chunk_text(text)

    chroma_ids = []
    chroma_texts = []
    metadatas = []

    for idx, content in enumerate(chunks):
        chunk = DocumentChunk(
            document_id=document.id,
            content=content,
            chunk_index=idx,
            token_count=len(content.split())
        )
        db.add(chunk)
        await db.flush()  # lấy chunk.id

        chroma_ids.append(str(chunk.id))
        chroma_texts.append(content)
        metadatas.append({
            "document_id": str(document.id),
            "grade": document.grade,
            "topic": document.topic
        })

    await db.commit()

    # Push vào Chroma
    collection.add(
        ids=chroma_ids,
        documents=chroma_texts,
        metadatas=metadatas
    )
