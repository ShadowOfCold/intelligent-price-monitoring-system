from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.dependencies import get_db
from backend.schemas.price_collection_schema import PriceCollectionRequest
from backend.schemas.price_schema import PriceResponse
from backend.services.price_collection_service import (
    collect_price_for_store_product,
    collect_prices_for_product,
    collect_prices_for_all_store_products
)

router = APIRouter(
    prefix="/price-collection",
    tags=["Сбор цен"]
)


@router.post("/", response_model=PriceResponse)
def collect_price(
    data: PriceCollectionRequest,
    db: Session = Depends(get_db)
):
    try:
        return collect_price_for_store_product(
            db=db,
            store_product_id=data.store_product_id
        )

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при сборе цены: {str(error)}"
        )


@router.post("/product/{product_id}", response_model=list[PriceResponse])
def collect_product_prices(
    product_id: int,
    db: Session = Depends(get_db)
):
    try:
        return collect_prices_for_product(
            db=db,
            product_id=product_id
        )

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при сборе цен товара: {str(error)}"
        )


@router.post("/all", response_model=list[PriceResponse])
def collect_all_prices(
    db: Session = Depends(get_db)
):
    try:
        return collect_prices_for_all_store_products(db=db)

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при сборе всех цен: {str(error)}"
        )