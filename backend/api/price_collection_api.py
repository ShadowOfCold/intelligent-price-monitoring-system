from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.dependencies import get_db
from backend.services.price_collection_service import (
    collect_price_for_store_product,
    collect_prices_for_product,
    collect_prices_for_all_store_products,
    serialize_price
)


router = APIRouter(
    prefix="/price-collection",
    tags=["Сбор цен"]
)


class PriceCollectionRequest(BaseModel):
    store_product_id: int


@router.post("/")
def collect_price(
    data: PriceCollectionRequest,
    db: Session = Depends(get_db)
):
    try:
        price = collect_price_for_store_product(
            db=db,
            store_product_id=data.store_product_id
        )

        return serialize_price(price)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.post("/product/{product_id}")
def collect_prices_by_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    try:
        return collect_prices_for_product(
            db=db,
            product_id=product_id
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.post("/all")
def collect_all_prices(
    db: Session = Depends(get_db)
):
    try:
        return collect_prices_for_all_store_products(
            db=db
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )