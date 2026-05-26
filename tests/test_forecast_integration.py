from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import backend.models
from backend.database.database import Base
from backend.models.product import Product
from backend.models.store import Store
from backend.models.store_product import StoreProduct
from backend.models.price import Price
from backend.services.forecast_service import generate_forecast_for_store_product


class FakeModel:
    def fit(self, *args, **kwargs):
        return None

    def predict(self, data, verbose=0):
        return data[:, -1:, 0]


def test_generate_forecast_with_metrics(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    monkeypatch.setattr(
        "backend.services.forecast_service.build_lstm_model",
        lambda window_size: FakeModel()
    )

    product = Product(
        name="Тестовый товар",
        category="Тест"
    )

    store = Store(
        name="Тестовый магазин",
        base_url="https://example.com"
    )

    db.add(product)
    db.add(store)
    db.commit()
    db.refresh(product)
    db.refresh(store)

    store_product = StoreProduct(
        product_id=product.id,
        store_id=store.id,
        product_url="https://example.com/product"
    )

    db.add(store_product)
    db.commit()
    db.refresh(store_product)

    start_date = datetime(2026, 1, 1, 10, 0)

    for index in range(25):
        price = Price(
            product_id=product.id,
            store_product_id=store_product.id,
            document_id=None,
            price=1000 + index * 10,
            checked_at=start_date + timedelta(days=index)
        )
        db.add(price)

    db.commit()

    result = generate_forecast_for_store_product(
        db=db,
        store_product_id=store_product.id,
        days_count=3
    )

    assert len(result["forecasts"]) == 3

    metrics = result["metrics"]

    assert "mae" in metrics
    assert "rmse" in metrics
    assert "mape" in metrics

    assert metrics["mae"] >= 0
    assert metrics["rmse"] >= 0
    assert metrics["mape"] >= 0

    print("Метрики прогнозирования:")
    print(f"MAE: {metrics['mae']}")
    print(f"RMSE: {metrics['rmse']}")
    print(f"MAPE: {metrics['mape']}")

    db.close()