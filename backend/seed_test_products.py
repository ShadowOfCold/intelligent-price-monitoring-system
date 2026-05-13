from backend.database.database import SessionLocal

from backend.models.product import Product
from backend.models.store import Store
from backend.models.store_product import StoreProduct


TEST_DATA = [
    {
        "product_name": "Кофемашина DeLonghi ECAM 450.55.S",
        "category": "Кофемашины",
        "store_name": "М.Видео",
        "base_url": "https://www.mvideo.ru",
        "product_url": "https://www.mvideo.ru/products/kofemashina-avtomaticheskaya-delonghi-ecam-45055s-4208372"
    },
    {
        "product_name": "Кофемашина DeLonghi ECAM 450.55.S",
        "category": "Кофемашины",
        "store_name": "Ситилинк",
        "base_url": "https://www.citilink.ru",
        "product_url": "https://www.citilink.ru/product/kofemashina-delonghi-ecam220-31-sb-1450vt-chernyi-serebristyi-1974017/?text=Кофемашина+DeLonghi+ECAM+450.55.S"
    },
    {
        "product_name": "Кофемашина DeLonghi ECAM 450.55.S",
        "category": "Кофемашины",
        "store_name": "Яндекс.Маркет",
        "base_url": "https://market.yandex.ru",
        "product_url": "https://market.yandex.ru/card/kofemashina-delonghi-ecam-45055-s/102725236810?do-waremd5=WlMi_XCGlwHt7oo-66nLXQ&sponsored=1&cpc=35XEfJH9cfowJ3omtrgvQUB2vTIkpmnsoQsFiaEh7_T9XPOoCbjC2zQG7Qiw70L6IN2hmtTkxWwiysXl1fJE2uB9cxn18ulbSBkg0k3sAfswfXenHkrXMKdW9aQUncG28rjE0BMUeUe5FQWhkD4JcSxuCLgZ_h5tXW1Z7CPLd5zjQW0iY1TpxOBT3sIynChbTD7Fh-Dl10S3KN3LJLFd6URXy-o02grLvJ5Ou_ca9ijebzRKNGH4i7RTTZleqiTdkzoz336MjjQRzIVQl3XqMCLlNXODjzmWt8pPsTrD3pJGH7mA0RfJPmlVS49gbqH2dFp8j8ugW-8eNq06R6FCBorP0v8IBlUICOkbMrBtJCs1-A9e2d9xtqZJ8lKxq5_JcMWJRPYgio0M777poH84nusFoeI-ZeiZEn8jlRhGSXw%2C&nid=74714680&ogV=-12"
    },
    {
        "product_name": "Смартфон Xiaomi Redmi Note 13",
        "category": "Смартфоны",
        "store_name": "М.Видео",
        "base_url": "https://www.mvideo.ru",
        "product_url": "https://www.mvideo.ru/products/smartfon-xiaomi-redmi-note-13-pro-8-256gb-forest-green-400257985"
    },
    {
        "product_name": "Смартфон Xiaomi Redmi Note 13",
        "category": "Смартфоны",
        "store_name": "Ситилинк",
        "base_url": "https://www.citilink.ru",
        "product_url": "https://www.citilink.ru/product/zaschitnoe-steklo-dlya-ekrana-pero-pgfgp-xrn13p4g-prozrachnyi-dlya-xia-2059835/"
    },
    {
        "product_name": "Смартфон Xiaomi Redmi Note 13",
        "category": "Смартфоны",
        "store_name": "Яндекс.Маркет",
        "base_url": "https://market.yandex.ru",
        "product_url": "https://market.yandex.ru/card/smartfon-xiaomi-redmi-15-8256gb-midnight-black/4944237885?do-waremd5=NAPm5A90dKbViUKgdRvTFw&sponsored=1&cpc=nxxlCY6mgKbak50vQsC48wmKWbQxaFQ95ANpg5-ah7ZC8qcSpnKhP0RX2w0JY_6m8nAp_jWSzWwG0SEpCFQzKT-Q-zSXw7-iR_M_3_YGSAvGMxKsxmA8Oo1qNIRIXD4CmavOAsp2k0MoMEIBIJDGSfbEHCZ6EGeR5oUhQCy2Gr8CoGZHSi5qcR2unXu9rVxB8CaE6CFj1oxc_-vYeYOEX9iDUKltx0mhXZe5eHByjbwfPNJXBe7axM-IkGPnChMV8QOtkQ6SLBprBDR-AoYukyba3GOiqLo7JphhJ0gj0MVD8snKkkg04DXPbXGunwr7vKAcyQYu5hcEZACZuD5-iqa_sxX90ZH5GHL7XB274Lk_yVmQLGSydEQm9At7cWjU5fAATQOFloveB7jjww4eTAmBhjmHOEqjK08UKldfjNgmW0FXF36BQQ%2C%2C&cc=CiAxYjkyNjQyOThiOTRlNGY0N2NjZWY1MjRmYjFiMjFiOBCAAoB95u0G&resale_goods=resale_new&hid=91491&nid=34512430&show-uid=17786703245996259583206001&showUid=17786703245996259583206001&from-show-uid=17786703245996259583206001&cpa=1&cpm-adv=1&from=premiumOffers"
    },
]


def get_or_create_product(db, name: str, category: str | None):
    product = db.query(Product).filter(Product.name == name).first()

    if product is not None:
        return product

    product = Product(
        name=name,
        category=category
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


def get_or_create_store(db, name: str, base_url: str):
    store = db.query(Store).filter(Store.name == name).first()

    if store is not None:
        return store

    store = Store(
        name=name,
        base_url=base_url
    )

    db.add(store)
    db.commit()
    db.refresh(store)

    return store


def get_or_create_store_product(db, product_id: int, store_id: int, product_url: str):
    store_product = db.query(StoreProduct).filter(
        StoreProduct.product_id == product_id,
        StoreProduct.store_id == store_id
    ).first()

    if store_product is not None:
        store_product.product_url = product_url
        db.commit()
        db.refresh(store_product)
        return store_product

    store_product = StoreProduct(
        product_id=product_id,
        store_id=store_id,
        product_url=product_url
    )

    db.add(store_product)
    db.commit()
    db.refresh(store_product)

    return store_product


def seed_test_products():
    db = SessionLocal()

    try:
        for item in TEST_DATA:
            if item["product_url"].startswith("ВСТАВЬ_ССЫЛКУ"):
                print(
                    f"Пропущено: {item['product_name']} — {item['store_name']} "
                    f"(не указана ссылка)"
                )
                continue

            product = get_or_create_product(
                db=db,
                name=item["product_name"],
                category=item["category"]
            )

            store = get_or_create_store(
                db=db,
                name=item["store_name"],
                base_url=item["base_url"]
            )

            store_product = get_or_create_store_product(
                db=db,
                product_id=product.id,
                store_id=store.id,
                product_url=item["product_url"]
            )

            print(
                f"Добавлено/обновлено: {product.name} — "
                f"{store.name} — карточка #{store_product.id}"
            )

        print("Тестовые данные успешно загружены")

    except Exception as error:
        db.rollback()
        print(f"Ошибка при загрузке тестовых данных: {error}")

    finally:
        db.close()


if __name__ == "__main__":
    seed_test_products()