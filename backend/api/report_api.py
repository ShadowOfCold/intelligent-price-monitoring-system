import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.database.dependencies import get_db
from backend.models.report import Report
from backend.schemas.report_schema import ReportRequest, ReportResponse
from backend.services.report_service import (
    delete_report,
    generate_excel_report,
    generate_pdf_report,
)

router = APIRouter(
    prefix="/reports",
    tags=["Отчёты"]
)


@router.get("/", response_model=list[ReportResponse])
def get_reports(db: Session = Depends(get_db)):
    return (
        db.query(Report)
        .order_by(Report.created_at.desc())
        .all()
    )


@router.post("/excel", response_model=ReportResponse)
def create_excel_report(
    data: ReportRequest,
    db: Session = Depends(get_db)
):
    try:
        return generate_excel_report(db, data.product_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))


@router.post("/pdf", response_model=ReportResponse)
def create_pdf_report(
    data: ReportRequest,
    db: Session = Depends(get_db)
):
    try:
        return generate_pdf_report(db, data.product_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))


@router.get("/download/{report_id}")
def download_report(
    report_id: int,
    db: Session = Depends(get_db)
):
    report = db.query(Report).filter(Report.id == report_id).first()

    if report is None:
        raise HTTPException(status_code=404, detail="Отчёт не найден")

    if not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Файл отчёта не найден")

    return FileResponse(
        path=report.file_path,
        filename=report.file_name
    )


@router.delete("/{report_id}")
def remove_report(
    report_id: int,
    db: Session = Depends(get_db)
):
    try:
        delete_report(db, report_id)
        return {"message": "Отчёт успешно удалён"}
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))