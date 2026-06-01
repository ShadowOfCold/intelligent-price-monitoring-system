from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.database.database import SessionLocal
from backend.models.category_factor_weight import CategoryFactorWeight
from backend.models.correlation_analysis_result import CorrelationAnalysisResult
from backend.models.detected_anomaly import DetectedAnomaly
from backend.models.learned_factor_weight import LearnedFactorWeight
from backend.models.market_factor import MarketFactor
from backend.models.price import Price
from backend.models.price_forecast import PriceForecast
from backend.models.product import Product
from backend.models.report import Report
from backend.models.store import Store
from backend.models.store_product import StoreProduct


db: Session = SessionLocal()


def clear_database():
    db.query(DetectedAnomaly).delete()
    db.query(CorrelationAnalysisResult).delete()
    db.query(PriceForecast).delete()
    db.query(Report).delete()
    db.query(Price).delete()
    db.query(StoreProduct).delete()
    db.query(Store).delete()
    db.query(Product).delete()
    db.query(MarketFactor).delete()
    db.query(LearnedFactorWeight).delete()
    db.query(CategoryFactorWeight).delete()
    db.commit()


def create_factor_weights():
    weights = [
        # default — только универсальные факторы
        ("default", "usd_rate", 0.35),
        ("default", "eur_rate", 0.25),
        ("default", "oil_price", 0.25),
        ("default", "inflation_rate", 0.15),

        # Электроника
        ("Электроника", "usd_rate", 0.30),
        ("Электроника", "eur_rate", 0.15),
        ("Электроника", "oil_price", 0.10),
        ("Электроника", "inflation_rate", 0.05),
        ("Электроника", "electronics_index", 0.25),
        ("Электроника", "ai_demand_index", 0.15),

        # Бытовая техника
        ("Бытовая техника", "usd_rate", 0.25),
        ("Бытовая техника", "eur_rate", 0.20),
        ("Бытовая техника", "oil_price", 0.10),
        ("Бытовая техника", "inflation_rate", 0.30),
        ("Бытовая техника", "electronics_index", 0.15),

        # Продукты питания
        ("Продукты питания", "usd_rate", 0.10),
        ("Продукты питания", "eur_rate", 0.05),
        ("Продукты питания", "oil_price", 0.20),
        ("Продукты питания", "inflation_rate", 0.65),

        # Автотовары
        ("Автотовары", "usd_rate", 0.20),
        ("Автотовары", "eur_rate", 0.10),
        ("Автотовары", "oil_price", 0.45),
        ("Автотовары", "inflation_rate", 0.25),
    ]

    for category, factor_name, weight in weights:
        db.add(
            CategoryFactorWeight(
                category=category,
                factor_name=factor_name,
                weight=weight
            )
        )

    db.commit()


def create_market_factors(start_date: datetime, days_count: int):
    for index in range(days_count):
        factor_date = datetime(
            start_date.year,
            start_date.month,
            start_date.day
        ) + timedelta(days=index)

        usd_rate = 90 + index * 0.04
        eur_rate = 98 + index * 0.03
        oil_price = 75 + index * 0.02
        inflation_rate = 7.0 + index * 0.006
        electronics_index = 100 + index * 0.06
        ai_demand_index = 100 + index * 0.08

        # Внешний рыночный скачок
        if index == 20:
            usd_rate = 135
            eur_rate = 145
            oil_price = 95
            inflation_rate = 9.5
            electronics_index = 165
            ai_demand_index = 175

        factor_values = [
            ("usd_rate", "currency", usd_rate),
            ("eur_rate", "currency", eur_rate),
            ("oil_price", "commodity", oil_price),
            ("inflation_rate", "macro", inflation_rate),
            ("electronics_index", "industry", electronics_index),
            ("ai_demand_index", "industry", ai_demand_index),
        ]

        for factor_name, factor_type, value in factor_values:
            db.add(
                MarketFactor(
                    factor_name=factor_name,
                    factor_type=factor_type,
                    value=value,
                    measured_at=factor_date
                )
            )

    db.commit()


def create_products():
    products = [
        Product(name="Видеокарта RTX Demo", category="Электроника"),
        Product(name="Ноутбук Demo", category="Электроника"),
        Product(name="Холодильник Demo", category="Бытовая техника"),
        Product(name="Кофе Demo", category="Продукты питания"),
        Product(name="Моторное масло Demo", category="Автотовары"),
        Product(name="Товар без категории Demo", category=None),
    ]

    for product in products:
        db.add(product)

    db.commit()

    for product in products:
        db.refresh(product)

    return products


def create_stores():
    stores = [
        Store(name="Demo Market 1", base_url="https://demo-market-1.ru"),
        Store(name="Demo Market 2", base_url="https://demo-market-2.ru"),
        Store(name="Demo Market 3", base_url="https://demo-market-3.ru"),
        Store(name="Demo Market 4", base_url="https://demo-market-4.ru"),
    ]

    for store in stores:
        db.add(store)

    db.commit()

    for store in stores:
        db.refresh(store)

    return stores


def create_store_product(product: Product, store: Store, slug: str):
    store_product = StoreProduct(
        product_id=product.id,
        store_id=store.id,
        product_url=f"{store.base_url}/{slug}"
    )

    db.add(store_product)
    db.commit()
    db.refresh(store_product)

    return store_product


def add_prices(product: Product, store_product: StoreProduct, prices: list[float], start_date: datetime):
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


def generate_smooth_growth(base: float, days: int, step: float):
    return [
        round(base + index * step + (step * 0.25 if index % 5 == 0 else 0), 2)
        for index in range(days)
    ]


def generate_correlated_growth(base_prices: list[float], offset: float):
    return [
        round(price + offset, 2)
        for price in base_prices
    ]


def generate_factor_explained_spike(base: float, days: int, step: float, spike_day: int, spike_multiplier: float):
    prices = []

    for index in range(days):
        if index < spike_day:
            price = base + index * step
        elif index == spike_day:
            price = (base + index * step) * spike_multiplier
        else:
            price = (base + spike_day * step) * spike_multiplier + (index - spike_day) * step * 1.2

        prices.append(round(price, 2))

    return prices


def generate_unexplained_spike(base: float, days: int, step: float, spike_day: int, spike_multiplier: float):
    prices = []

    for index in range(days):
        if index < spike_day:
            price = base + index * step
        elif index == spike_day:
            price = (base + index * step) * spike_multiplier
        else:
            price = base + index * step

        prices.append(round(price, 2))

    return prices


def generate_unexplained_drop(base: float, days: int, step: float, drop_day: int, drop_multiplier: float):
    prices = []

    for index in range(days):
        if index < drop_day:
            price = base + index * step
        elif index == drop_day:
            price = (base + index * step) * drop_multiplier
        else:
            price = base + index * step

        prices.append(round(price, 2))

    return prices


def generate_fixation(base: float, days: int, fixation_days: int, step: float):
    prices = []

    for index in range(days):
        if index < fixation_days:
            price = base
        else:
            price = base + (index - fixation_days + 1) * step

        prices.append(round(price, 2))

    return prices


def create_demo_prices(products: list[Product], stores: list[Store], start_date: datetime):
    days = 60

    # 1. Электроника: видеокарта
    gpu = products[0]

    gpu_smooth = generate_smooth_growth(50000, days, 120)
    gpu_corr = generate_correlated_growth(gpu_smooth, 500)
    gpu_factor_spike = generate_factor_explained_spike(50000, days, 100, 20, 1.35)
    gpu_unexplained_spike = generate_unexplained_spike(50000, days, 100, 35, 1.65)

    gpu_price_sets = [
        gpu_smooth,
        gpu_corr,
        gpu_factor_spike,
        gpu_unexplained_spike,
    ]

    for store, prices in zip(stores, gpu_price_sets):
        sp = create_store_product(gpu, store, "gpu-demo")
        add_prices(gpu, sp, prices, start_date)

    # 2. Электроника: ноутбук
    laptop = products[1]

    laptop_smooth = generate_smooth_growth(70000, days, 150)
    laptop_factor_spike = generate_factor_explained_spike(70000, days, 120, 20, 1.25)

    for store, prices in zip(stores[:2], [laptop_smooth, laptop_factor_spike]):
        sp = create_store_product(laptop, store, "laptop-demo")
        add_prices(laptop, sp, prices, start_date)

    # 3. Бытовая техника
    fridge = products[2]

    fridge_smooth = generate_smooth_growth(45000, days, 80)
    fridge_fixation = generate_fixation(46000, days, 18, 90)

    for store, prices in zip(stores[:2], [fridge_smooth, fridge_fixation]):
        sp = create_store_product(fridge, store, "fridge-demo")
        add_prices(fridge, sp, prices, start_date)

    # 4. Продукты питания
    coffee = products[3]

    coffee_smooth = generate_smooth_growth(900, days, 4)
    coffee_unexplained_spike = generate_unexplained_spike(900, days, 4, 30, 1.8)

    for store, prices in zip(stores[:2], [coffee_smooth, coffee_unexplained_spike]):
        sp = create_store_product(coffee, store, "coffee-demo")
        add_prices(coffee, sp, prices, start_date)

    # 5. Автотовары
    oil = products[4]

    oil_smooth = generate_smooth_growth(2500, days, 10)
    oil_unexplained_drop = generate_unexplained_drop(2500, days, 10, 32, 0.45)

    for store, prices in zip(stores[:2], [oil_smooth, oil_unexplained_drop]):
        sp = create_store_product(oil, store, "motor-oil-demo")
        add_prices(oil, sp, prices, start_date)

    # 6. Товар без категории
    no_category = products[5]

    default_smooth = generate_smooth_growth(1500, days, 6)
    default_drop = generate_unexplained_drop(1500, days, 6, 28, 0.5)

    for store, prices in zip(stores[:2], [default_smooth, default_drop]):
        sp = create_store_product(no_category, store, "default-demo")
        add_prices(no_category, sp, prices, start_date)


def main():
    clear_database()

    start_date = datetime(2026, 1, 1, 12, 0)

    create_factor_weights()
    create_market_factors(start_date=start_date, days_count=80)

    products = create_products()
    stores = create_stores()

    create_demo_prices(
        products=products,
        stores=stores,
        start_date=start_date
    )

    print("Демонстрационные тестовые данные успешно загружены")
    print("")
    print("Категории:")
    print("- Электроника")
    print("- Бытовая техника")
    print("- Продукты питания")
    print("- Автотовары")
    print("- Без категории / default")
    print("")
    print("Сценарии:")
    print("- плавный рост")
    print("- высокая корреляция между магазинами")
    print("- рост, объяснённый рыночными факторами")
    print("- необъяснённый рост")
    print("- необъяснённое падение")
    print("- длительная фиксация цены")
    print("- прогнозирование LSTM")


if __name__ == "__main__":
    try:
        main()
    finally:
        db.close()