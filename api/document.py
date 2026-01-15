from fastapi import APIRouter, UploadFile, File, Form, Depends

from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models.documents import Documents
from services.document_pipeline import process_document
from sqlalchemy import select
from uuid import uuid4, UUID
import shutil

router = APIRouter(prefix="/api/admin", tags=["Documents"])
@router.post("/documents")
async def upload_document(
    file: UploadFile = File(...),
    grade: int = Form(None),
    topic: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    file_id = str(uuid4())
    file_path = f"uploads/{file_id}_{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    doc = Documents(
        title=file.filename,
        doc_type=file.filename.split(".")[-1],
        file_path=file_path,
        grade=grade,
        topic=topic
    )

    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc

@router.post("/documents/{document_id}/process")
async def process_uploaded_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Documents).where(Documents.id == document_id)
    )
    document = result.scalar_one_or_none()
    if not document:
        return {"error": "Document not found"}

    await process_document(document, db)
    return {"status": "processed"}
