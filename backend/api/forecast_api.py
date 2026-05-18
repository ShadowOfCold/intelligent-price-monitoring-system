from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.dependencies import get_db
from backend.schemas.forecast_schema import (
    ForecastCreateRequest,
    ForecastGenerateResponse,
    PriceForecastResponse,
)
from backend.services.forecast_service import (
    delete_forecasts_for_store_product,
    generate_forecast_for_store_product,
    get_forecasts_for_store_product,
)

router = APIRouter(
    prefix="/forecasts",
    tags=["Прогнозирование цен"]
)


@router.post(
    "/generate",
    response_model=ForecastGenerateResponse
)
def generate_forecast(
    data: ForecastCreateRequest,
    db: Session = Depends(get_db)
):
    try:
        return generate_forecast_for_store_product(
            db=db,
            store_product_id=data.store_product_id,
            days_count=data.days_count
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.get(
    "/store-product/{store_product_id}",
    response_model=list[PriceForecastResponse]
)
def get_store_product_forecasts(
    store_product_id: int,
    db: Session = Depends(get_db)
):
    return get_forecasts_for_store_product(
        db=db,
        store_product_id=store_product_id
    )


@router.delete("/store-product/{store_product_id}")
def delete_store_product_forecasts(
    store_product_id: int,
    db: Session = Depends(get_db)
):
    deleted_count = delete_forecasts_for_store_product(
        db=db,
        store_product_id=store_product_id
    )

    return {
        "message": f"Удалено прогнозов: {deleted_count}"
    }