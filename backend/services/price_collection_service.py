from datetime import datetime

from sqlalchemy.orm import Session

from backend.models.price import Price
from backend.models.store_product import StoreProduct
from backend.parsers.parser_factory import get_parser


def collect_price_for_store_product(
    db: Session,
    store_product_id: int
) -> Price:
    store_product = db.query(StoreProduct).filter(
        StoreProduct.id == store_product_id
    ).first()

    if store_product is None:
        raise ValueError("Карточка товара не найдена")

    store = store_product.store

    if store is None:
        raise ValueError("Магазин для карточки товара не найден")

    parser = get_parser(store.name)

    parsed_price = parser.parse_price(store_product.product_url)

    price = Price(
        product_id=store_product.product_id,
        store_product_id=store_product.id,
        document_id=None,
        price=parsed_price,
        checked_at=datetime.now()
    )

    db.add(price)
    db.commit()
    db.refresh(price)

    return price


def collect_prices_for_product(
    db: Session,
    product_id: int
) -> list[Price]:
    store_products = db.query(StoreProduct).filter(
        StoreProduct.product_id == product_id
    ).all()

    if not store_products:
        raise ValueError("Для выбранного товара нет карточек в магазинах")

    collected_prices = []

    for store_product in store_products:
        price = collect_price_for_store_product(
            db=db,
            store_product_id=store_product.id
        )

        collected_prices.append(price)

    return collected_prices


def collect_prices_for_all_store_products(
    db: Session
) -> list[Price]:
    store_products = db.query(StoreProduct).all()

    if not store_products:
        raise ValueError("Карточки товаров отсутствуют")

    collected_prices = []

    for store_product in store_products:
        price = collect_price_for_store_product(
            db=db,
            store_product_id=store_product.id
        )

        collected_prices.append(price)

    return collected_prices