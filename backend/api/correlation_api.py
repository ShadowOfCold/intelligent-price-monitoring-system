from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.dependencies import get_db
from backend.models.product import Product
from backend.schemas.correlation_schema import (
    CorrelationAnalysisResponse,
    CorrelationAnalysisWithStoresResponse,
)
from backend.services.correlation_service import (
    analyze_correlations_for_product,
    delete_correlations_for_product,
    get_correlations_for_product,
)

router = APIRouter(
    prefix="/correlations",
    tags=["Корреляционный анализ"]
)


@router.post(
    "/analyze/product/{product_id}",
    response_model=list[CorrelationAnalysisResponse]
)
def analyze_product_correlations(
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
        return analyze_correlations_for_product(
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
    response_model=list[CorrelationAnalysisWithStoresResponse]
)
def get_product_correlations(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Товар не найден"
        )

    return get_correlations_for_product(
        db=db,
        product_id=product_id
    )


@router.delete("/product/{product_id}")
def delete_product_correlations(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Товар не найден"
        )

    deleted_count = delete_correlations_for_product(
        db=db,
        product_id=product_id
    )

    return {
        "message": f"Удалено результатов корреляционного анализа: {deleted_count}"
    }