import os
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.database.dependencies import get_db
from backend.models.price import Price
from backend.models.procurement_document import ProcurementDocument
from backend.schemas.document_schema import ProcurementDocumentResponse
from backend.services.document_service import (
    DOCUMENTS_DIRECTORY,
    parse_procurement_document,
)

router = APIRouter(
    prefix="/documents",
    tags=["Документы закупки"]
)

DOCUMENTS_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True
)


@router.post(
    "/upload",
    response_model=ProcurementDocumentResponse
)
async def upload_document(
    file: UploadFile = File(...),
    price_checked_at: datetime = Form(...),
    db: Session = Depends(get_db)
):
    allowed_extensions = [
        ".xlsx",
        ".xls",
        ".pdf",
    ]

    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Поддерживаются только файлы XLSX, XLS и PDF"
        )

    if file_extension == ".xlsx":
        file_type = "XLSX"
    elif file_extension == ".xls":
        file_type = "XLS"
    else:
        file_type = "PDF"

    original_file_name = Path(file.filename).name
    file_path = DOCUMENTS_DIRECTORY / original_file_name

    counter = 1

    while file_path.exists():
        file_path = (
            DOCUMENTS_DIRECTORY /
            f"{Path(original_file_name).stem}_{counter}{file_extension}"
        )

        counter += 1

    file_bytes = await file.read()

    with open(file_path, "wb") as saved_file:
        saved_file.write(file_bytes)

    document = ProcurementDocument(
        file_name=file.filename,
        file_type=file_type,
        file_path=str(file_path),
        uploaded_at=datetime.now(),
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        parse_procurement_document(
            db=db,
            file_path=str(file_path),
            file_type=file_type,
            document_id=document.id,
            price_checked_at=price_checked_at
        )

    except Exception as error:
        db.delete(document)
        db.commit()

        if file_path.exists():
            os.remove(file_path)

        raise HTTPException(
            status_code=400,
            detail=f"Ошибка обработки документа: {error}"
        )

    return document


@router.get(
    "/",
    response_model=list[ProcurementDocumentResponse]
)
def get_documents(
    db: Session = Depends(get_db)
):
    return (
        db.query(ProcurementDocument)
        .order_by(ProcurementDocument.uploaded_at.desc())
        .all()
    )


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    document = db.query(ProcurementDocument).filter(
        ProcurementDocument.id == document_id
    ).first()

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Документ не найден"
        )

    db.query(Price).filter(
        Price.document_id == document_id
    ).delete()

    if document.file_path and os.path.exists(document.file_path):
        os.remove(document.file_path)

    db.delete(document)
    db.commit()

    return {
        "message": "Документ успешно удалён"
    }