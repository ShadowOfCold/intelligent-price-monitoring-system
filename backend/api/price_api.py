from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.dependencies import get_db
from backend.models.product import Product
from backend.models.store_product import StoreProduct
from backend.models.procurement_document import ProcurementDocument
from backend.models.price import Price
from backend.models.detected_anomaly import DetectedAnomaly
from backend.schemas.price_schema import PriceCreate, PriceResponse
from backend.schemas.price_delete_schema import PriceDeleteMultipleRequest

router = APIRouter(prefix="/prices", tags=["Цены"])


@router.post("/", response_model=PriceResponse)
def create_price(data: PriceCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == data.product_id).first()

    if product is None:
        raise HTTPException(status_code=404, detail="Товар не найден")

    if (data.store_product_id is None and data.document_id is None) or (
        data.store_product_id is not None and data.document_id is not None
    ):
        raise HTTPException(
            status_code=400,
            detail="Необходимо указать ровно один источник цены: карточку товара или документ"
        )

    if data.store_product_id is not None:
        store_product = db.query(StoreProduct).filter(
            StoreProduct.id == data.store_product_id
        ).first()

        if store_product is None:
            raise HTTPException(
                status_code=404,
                detail="Карточка товара не найдена"
            )

        if store_product.product_id != data.product_id:
            raise HTTPException(
                status_code=400,
                detail="Карточка товара не соответствует указанному товару"
            )

    if data.document_id is not None:
        document = db.query(ProcurementDocument).filter(
            ProcurementDocument.id == data.document_id
        ).first()

        if document is None:
            raise HTTPException(status_code=404, detail="Документ не найден")

    price = Price(
        product_id=data.product_id,
        store_product_id=data.store_product_id,
        document_id=data.document_id,
        price=data.price,
        checked_at=data.checked_at,
    )

    db.add(price)
    db.commit()
    db.refresh(price)

    return price


@router.get("/", response_model=list[PriceResponse])
def get_prices(db: Session = Depends(get_db)):
    return db.query(Price).order_by(Price.checked_at.desc()).all()


@router.get("/product/{product_id}", response_model=list[PriceResponse])
def get_product_prices(product_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Price)
        .filter(Price.product_id == product_id)
        .order_by(Price.checked_at)
        .all()
    )


@router.delete("/{price_id}")
def delete_price(price_id: int, db: Session = Depends(get_db)):
    price = db.query(Price).filter(Price.id == price_id).first()

    if price is None:
        raise HTTPException(status_code=404, detail="Цена не найдена")

    db.delete(price)
    db.commit()

    return {"message": "Цена успешно удалена"}


@router.post("/delete-multiple")
def delete_multiple_prices(
    data: PriceDeleteMultipleRequest,
    db: Session = Depends(get_db)
):
    if not data.price_ids:
        raise HTTPException(
            status_code=400,
            detail="Не выбраны записи цен для удаления"
        )

    prices = db.query(Price).filter(Price.id.in_(data.price_ids)).all()

    if not prices:
        raise HTTPException(
            status_code=404,
            detail="Выбранные записи цен не найдены"
        )

    for price in prices:
        db.delete(price)

    db.commit()

    return {
        "message": f"Удалено записей цен: {len(prices)}"
    }