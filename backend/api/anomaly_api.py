from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.dependencies import get_db
from backend.models.product import Product
from backend.schemas.anomaly_schema import (
    AnomalyWithPriceResponse,
    DetectedAnomalyResponse,
)
from backend.services.anomaly_service import (
    delete_anomalies_for_product,
    detect_anomalies_for_product,
    get_anomalies_for_product,
)

router = APIRouter(
    prefix="/anomalies",
    tags=["Аномалии"]
)


@router.post(
    "/detect/product/{product_id}",
    response_model=list[DetectedAnomalyResponse]
)
def detect_product_anomalies(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Товар не найден"
        )

    try:
        return detect_anomalies_for_product(
            db=db,
            product_id=product_id
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.get(
    "/product/{product_id}",
    response_model=list[AnomalyWithPriceResponse]
)
def get_product_anomalies(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Товар не найден"
        )

    return get_anomalies_for_product(
        db=db,
        product_id=product_id
    )


@router.delete("/product/{product_id}")
def delete_product_anomalies(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Товар не найден"
        )

    deleted_count = delete_anomalies_for_product(
        db=db,
        product_id=product_id
    )

    return {
        "message": f"Удалено аномалий: {deleted_count}"
    }