from sqlalchemy.orm import Session

from backend.models.price import Price
from backend.models.store_product import StoreProduct
from backend.parsers.parser_factory import get_parser
from backend.utils.datetime_utils import get_current_datetime

def get_store_product_label(store_product: StoreProduct) -> str:
    product_name = (
        store_product.product.name
        if store_product.product
        else f"Товар #{store_product.product_id}"
    )

    store_name = (
        store_product.store.name
        if store_product.store
        else f"Магазин #{store_product.store_id}"
    )

    return f"{product_name} — {store_name} (карточка #{store_product.id})"


def make_readable_parser_error(error: Exception) -> str:
    error_text = str(error).lower()

    if "timeout" in error_text:
        return "Страница товара не загрузилась за отведённое время"

    if "no such element" in error_text:
        return "На странице не найден элемент с ценой"

    if "price" in error_text or "цена" in error_text:
        return "Цена не найдена на странице товара"

    if "connection" in error_text or "max retries" in error_text:
        return "Не удалось подключиться к странице товара"

    if "parser" in error_text or "парсер" in error_text:
        return "Для данного магазина не найден подходящий парсер"

    return "Не удалось получить цену со страницы товара"


def serialize_price(price: Price) -> dict:
    return {
        "id": price.id,
        "product_id": price.product_id,
        "store_product_id": price.store_product_id,
        "document_id": price.document_id,
        "price": float(price.price),
        "checked_at": price.checked_at
    }


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

    try:
        parser = get_parser(store.name)
        parsed_price = parser.parse_price(store_product.product_url)
        if parsed_price is None:
            raise ValueError("Цена не найдена на странице товара")

        try:
            parsed_price = float(parsed_price)
        except Exception:
            raise ValueError("Получено некорректное значение цены")

        if parsed_price <= 0:
            raise ValueError("Получено некорректное значение цены")

    except Exception as error:
        raise ValueError(make_readable_parser_error(error))

    price = Price(
        product_id=store_product.product_id,
        store_product_id=store_product.id,
        document_id=None,
        price=parsed_price,
        checked_at=get_current_datetime()
    )

    db.add(price)
    db.commit()
    db.refresh(price)

    return price


def collect_prices_for_product(
    db: Session,
    product_id: int
) -> dict:
    store_products = db.query(StoreProduct).filter(
        StoreProduct.product_id == product_id
    ).all()

    if not store_products:
        raise ValueError("Для выбранного товара нет карточек в магазинах")

    result = {
        "collected": [],
        "errors": []
    }

    for store_product in store_products:
        try:
            price = collect_price_for_store_product(
                db=db,
                store_product_id=store_product.id
            )

            result["collected"].append(
                serialize_price(price)
            )

        except Exception as error:
            db.rollback()

            result["errors"].append(
                {
                    "store_product_id": store_product.id,
                    "label": get_store_product_label(store_product),
                    "message": str(error)
                }
            )

    return result


def collect_prices_for_all_store_products(
    db: Session
) -> dict:
    store_products = db.query(StoreProduct).all()

    if not store_products:
        raise ValueError("Карточки товаров отсутствуют")

    result = {
        "collected": [],
        "errors": []
    }

    for store_product in store_products:
        try:
            price = collect_price_for_store_product(
                db=db,
                store_product_id=store_product.id
            )

            result["collected"].append(
                serialize_price(price)
            )

        except Exception as error:
            db.rollback()

            result["errors"].append(
                {
                    "store_product_id": store_product.id,
                    "label": get_store_product_label(store_product),
                    "message": str(error)
                }
            )

    return result