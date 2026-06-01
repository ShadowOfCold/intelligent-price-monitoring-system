from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.dependencies import get_db
from backend.models.category_factor_weight import CategoryFactorWeight
from backend.schemas.market_factor_schema import (
    CategoryFactorWeightCreate,
    CategoryFactorWeightResponse,
    MarketFactorCreate,
    MarketFactorResponse,
)
from backend.services.market_factor_service import (
    update_market_factors_from_external_sources,
    create_or_update_category_factor_weight,
    create_or_update_market_factor,
    get_factor_weights_for_category,
    get_market_factors,
    get_market_factors_for_date,
    initialize_default_factor_weights,
)

router = APIRouter(
    prefix="/market-factors",
    tags=["Рыночные факторы"]
)


@router.post("/", response_model=MarketFactorResponse)
def create_market_factor(
    data: MarketFactorCreate,
    db: Session = Depends(get_db)
):
    try:
        return create_or_update_market_factor(
            db=db,
            factor_name=data.factor_name,
            factor_type=data.factor_type,
            value=data.value,
            measured_at=data.measured_at,
        )
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.get("/", response_model=list[MarketFactorResponse])
def read_market_factors(
    db: Session = Depends(get_db)
):
    return get_market_factors(db=db)


@router.get("/date/{target_datetime}")
def read_market_factors_for_date(
    target_datetime: datetime,
    db: Session = Depends(get_db)
):
    return get_market_factors_for_date(
        db=db,
        target_date=target_datetime,
    )


@router.post(
    "/weights",
    response_model=CategoryFactorWeightResponse
)
def create_factor_weight(
    data: CategoryFactorWeightCreate,
    db: Session = Depends(get_db)
):
    try:
        return create_or_update_category_factor_weight(
            db=db,
            category=data.category,
            factor_name=data.factor_name,
            weight=data.weight,
        )
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.get(
    "/weights/{category}",
    response_model=list[CategoryFactorWeightResponse]
)
def read_factor_weights_for_category(
    category: str,
    db: Session = Depends(get_db)
):
    return get_factor_weights_for_category(
        db=db,
        category=category,
    )


@router.get(
    "/weights",
    response_model=list[CategoryFactorWeightResponse]
)
def read_all_factor_weights(
    db: Session = Depends(get_db)
):
    return (
        db.query(CategoryFactorWeight)
        .order_by(CategoryFactorWeight.category, CategoryFactorWeight.factor_name)
        .all()
    )

@router.post("/update-external")
def update_external_market_factors(
    db: Session = Depends(get_db)
):
    result = update_market_factors_from_external_sources(db=db)

    return {
        "message": "Обновление рыночных факторов выполнено",
        "result": result,
    }

@router.post("/weights/initialize")
def initialize_weights(
    db: Session = Depends(get_db)
):
    result = initialize_default_factor_weights(db=db)

    return {
        "message": "Базовые веса факторов созданы или обновлены",
        "count": result["count"]
    }
    