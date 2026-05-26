from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.database.database import SessionLocal
from backend.models.price import Price
from backend.models.product import Product
from backend.models.store import Store
from backend.models.store_product import StoreProduct


db: Session = SessionLocal()

# ---------------------------------------------------
# Очистка старых тестовых данных
# ---------------------------------------------------

db.query(Price).delete()
db.query(StoreProduct).delete()
db.query(Store).delete()
db.query(Product).delete()

db.commit()

# ---------------------------------------------------
# Создание тестового товара
# ---------------------------------------------------

product = Product(
    name="Тестовый товар аналитики",
    category="Тест"
)

db.add(product)
db.commit()
db.refresh(product)

# ---------------------------------------------------
# Создание магазинов
# ---------------------------------------------------

stores = []

for index in range(1, 6):
    store = Store(
        name=f"Тест Магазин {index}",
        base_url=f"https://example{index}.com"
    )

    db.add(store)
    stores.append(store)

db.commit()

for store in stores:
    db.refresh(store)

# ---------------------------------------------------
# Создание карточек товаров
# ---------------------------------------------------

store_products = []

for index, store in enumerate(stores, start=1):
    store_product = StoreProduct(
        product_id=product.id,
        store_id=store.id,
        product_url=f"https://example{index}.com/product"
    )

    db.add(store_product)
    store_products.append(store_product)

db.commit()

for store_product in store_products:
    db.refresh(store_product)

# ---------------------------------------------------
# Начальная дата
# ---------------------------------------------------

start_date = datetime(2026, 1, 1, 12, 0)

# ---------------------------------------------------
# Карточка 1
# Плавный рост цен
# Для прогнозирования
# ---------------------------------------------------

forecast_prices = [
    1000, 1003, 1001, 1005, 1008,
    1010, 1009, 1012, 1015, 1017,
    1016, 1020, 1022, 1021, 1025,
    1027, 1026, 1030, 1033, 1035,
    1034, 1038, 1040, 1039, 1043,
    1045, 1047, 1046, 1050, 1052,
    1055, 1054, 1058, 1060, 1062,
    1061, 1065, 1067, 1069, 1070,
    1072, 1071, 1075, 1078, 1080,
    1082, 1081, 1085, 1087, 1089,
    1090, 1092, 1091, 1095, 1097,
    1100, 1102, 1101, 1104, 1106
]

# ---------------------------------------------------
# Карточка 2
# Высокая корреляция с карточкой 1
# ---------------------------------------------------

correlation_prices = [
    1002, 1004, 1003, 1007, 1009,
    1011, 1010, 1013, 1016, 1018,
    1017, 1021, 1023, 1022, 1026,
    1028, 1027, 1031, 1034, 1036,
    1035, 1039, 1041, 1040, 1044,
    1046, 1048, 1047, 1051, 1053,
    1056, 1055, 1059, 1061, 1063,
    1062, 1066, 1068, 1070, 1071,
    1073, 1072, 1076, 1079, 1081,
    1083, 1082, 1086, 1088, 1090,
    1091, 1093, 1092, 1096, 1098,
    1101, 1103, 1102, 1105, 1107
]

# ---------------------------------------------------
# Карточка 3
# Резкий скачок цены
# price_spike
# z_score_outlier
# price_outlier
# ---------------------------------------------------

spike_prices = [
    1000, 1002, 1001, 1003, 1004,
    1005, 1006, 1005, 1007, 1008,
    1010, 1012, 1011, 1013, 1014,
    2500,
    1015, 1016, 1017, 1018,
    1020, 1021, 1022, 1023, 1024,
    1025, 1026, 1027, 1028, 1030
]

# ---------------------------------------------------
# Карточка 4
# Резкое падение цены
# price_drop
# ---------------------------------------------------

drop_prices = [
    2000, 2002, 2004, 2005, 2007,
    2008, 2010, 2011, 2013, 2015,
    2016, 2018, 2020, 2021, 2023,
    500,
    2025, 2026, 2028, 2030,
    2031, 2033, 2035, 2036, 2038,
    2040, 2041, 2043, 2045, 2046
]

# ---------------------------------------------------
# Карточка 5
# Длительная фиксация цены
# price_fixation
# ---------------------------------------------------

fixation_prices = [
    1500, 1500, 1500, 1500, 1500,
    1500, 1500, 1500, 1500, 1500,
    1500, 1500, 1500, 1500, 1500,
    1500, 1500, 1500, 1500, 1500,
    1510, 1520, 1530, 1540, 1550,
    1560, 1570, 1580, 1590, 1600
]

all_price_sets = [
    forecast_prices,
    correlation_prices,
    spike_prices,
    drop_prices,
    fixation_prices
]

# ---------------------------------------------------
# Загрузка цен в БД
# ---------------------------------------------------

for store_product, prices in zip(store_products, all_price_sets):
    for index, price in enumerate(prices):
        db.add(
            Price(
                product_id=product.id,
                store_product_id=store_product.id,
                document_id=None,
                price=price,
                checked_at=start_date + timedelta(days=index)
            )
        )

db.commit()

db.close()

print("Тестовые данные успешно загружены")
print("")
print("Подготовлены сценарии:")
print("- Прогнозирование")
print("- Корреляционный анализ")
print("- Резкий скачок цены")
print("- Резкое падение цены")
print("- Длительная фиксация цены")
print("- Статистический выброс")
print("- Нетипичное значение цены")