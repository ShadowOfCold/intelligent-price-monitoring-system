from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.dependencies import get_db
from backend.models.product import Product
from backend.models.store import Store
from backend.models.store_product import StoreProduct
from backend.schemas.store_product_schema import (
    StoreProductCreate,
    StoreProductResponse
)

from urllib.parse import urlparse


def is_valid_url(value: str) -> bool:
    try:
        result = urlparse(value)
        return result.scheme in ("http", "https") and bool(result.netloc)
    except Exception:
        return False

router = APIRouter(prefix="/store-products", tags=["Карточки товаров"])


@router.post("/", response_model=StoreProductResponse)
def create_store_product(
    data: StoreProductCreate,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == data.product_id).first()

    if product is None:
        raise HTTPException(status_code=404, detail="Товар не найден")

    store = db.query(Store).filter(Store.id == data.store_id).first()

    if store is None:
        raise HTTPException(status_code=404, detail="Магазин не найден")

    existing = db.query(StoreProduct).filter(
        StoreProduct.product_id == data.product_id,
        StoreProduct.store_id == data.store_id
    ).first()

    if existing is not None:
        raise HTTPException(
            status_code=400,
            detail="Карточка товара уже существует"
        )
    
    if not is_valid_url(data.product_url):
        raise HTTPException(
            status_code=400,
            detail="Введите корректную ссылку на страницу товара"
        )

    store_product = StoreProduct(
        product_id=data.product_id,
        store_id=data.store_id,
        product_url=data.product_url
    )

    db.add(store_product)
    db.commit()
    db.refresh(store_product)

    return store_product


@router.get("/", response_model=list[StoreProductResponse])
def get_store_products(db: Session = Depends(get_db)):
    return db.query(StoreProduct).order_by(StoreProduct.id).all()


@router.put("/{store_product_id}", response_model=StoreProductResponse)
def update_store_product(
    store_product_id: int,
    data: StoreProductCreate,
    db: Session = Depends(get_db)
):
    store_product = db.query(StoreProduct).filter(
        StoreProduct.id == store_product_id
    ).first()

    if store_product is None:
        raise HTTPException(status_code=404, detail="Карточка товара не найдена")

    product = db.query(Product).filter(Product.id == data.product_id).first()

    if product is None:
        raise HTTPException(status_code=404, detail="Товар не найден")

    store = db.query(Store).filter(Store.id == data.store_id).first()

    if store is None:
        raise HTTPException(status_code=404, detail="Магазин не найден")

    existing = db.query(StoreProduct).filter(
        StoreProduct.product_id == data.product_id,
        StoreProduct.store_id == data.store_id,
        StoreProduct.id != store_product_id
    ).first()

    if existing is not None:
        raise HTTPException(
            status_code=400,
            detail="Карточка товара для выбранного товара и магазина уже существует"
        )
    
    if not is_valid_url(data.product_url):
        raise HTTPException(
            status_code=400,
            detail="Введите корректную ссылку на страницу товара"
        )

    store_product.product_id = data.product_id
    store_product.store_id = data.store_id
    store_product.product_url = data.product_url

    db.commit()
    db.refresh(store_product)

    return store_product


@router.delete("/{store_product_id}")
def delete_store_product(
    store_product_id: int,
    db: Session = Depends(get_db)
):
    store_product = db.query(StoreProduct).filter(
        StoreProduct.id == store_product_id
    ).first()

    if store_product is None:
        raise HTTPException(status_code=404, detail="Карточка товара не найдена")

    db.delete(store_product)
    db.commit()

    return {"message": "Карточка товара успешно удалена"}