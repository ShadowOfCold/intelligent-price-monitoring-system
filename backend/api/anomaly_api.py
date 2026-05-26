from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.dependencies import get_db
from backend.models.store_product import  StoreProduct
from backend.models.product import Product
from backend.schemas.anomaly_schema import (
    AnomalyWithPriceResponse,
    DetectedAnomalyResponse,
)
from backend.services.anomaly_service import (
    delete_anomalies_for_product,
    delete_anomalies_for_store_product,
    detect_anomalies_for_product,
    detect_anomalies_for_store_product,
    get_anomalies_for_product,
    get_anomalies_for_store_product,
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

@router.post(
    "/detect/store-product/{store_product_id}",
    response_model=list[DetectedAnomalyResponse]
)
def detect_store_product_anomalies(
    store_product_id: int,
    db: Session = Depends(get_db)
):
    store_product = (
        db.query(StoreProduct)
        .filter(StoreProduct.id == store_product_id)
        .first()
    )

    if store_product is None:
        raise HTTPException(
            status_code=404,
            detail="Карточка товара не найдена"
        )

    try:
        return detect_anomalies_for_store_product(
            db=db,
            store_product_id=store_product_id
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.get(
    "/store-product/{store_product_id}",
    response_model=list[AnomalyWithPriceResponse]
)
def get_store_product_anomalies(
    store_product_id: int,
    db: Session = Depends(get_db)
):
    store_product = (
        db.query(StoreProduct)
        .filter(StoreProduct.id == store_product_id)
        .first()
    )

    if store_product is None:
        raise HTTPException(
            status_code=404,
            detail="Карточка товара не найдена"
        )

    return get_anomalies_for_store_product(
        db=db,
        store_product_id=store_product_id
    )


@router.delete("/store-product/{store_product_id}")
def delete_store_product_anomalies(
    store_product_id: int,
    db: Session = Depends(get_db)
):
    store_product = (
        db.query(StoreProduct)
        .filter(StoreProduct.id == store_product_id)
        .first()
    )

    if store_product is None:
        raise HTTPException(
            status_code=404,
            detail="Карточка товара не найдена"
        )

    deleted_count = delete_anomalies_for_store_product(
        db=db,
        store_product_id=store_product_id
    )

    return {
        "message": f"Удалено аномалий: {deleted_count}"
    }