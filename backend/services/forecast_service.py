from datetime import timedelta

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import MinMaxScaler
from sqlalchemy.orm import Session
from tensorflow.keras.layers import Input, LSTM, Dense
from tensorflow.keras.models import Sequential

from backend.models.price import Price
from backend.models.price_forecast import PriceForecast
from backend.models.store_product import StoreProduct
from backend.utils.datetime_utils import get_current_datetime

MIN_POINTS_FOR_FORECAST = 20
WINDOW_SIZE = 7
EPOCHS = 40
BATCH_SIZE = 8
TEST_SIZE_RATIO = 0.2


def create_sequences(data, window_size: int):
    x = []
    y = []

    for index in range(window_size, len(data)):
        x.append(data[index - window_size:index])
        y.append(data[index])

    return np.array(x), np.array(y)


def build_lstm_model(window_size: int):
    model = Sequential()

    model.add(
        Input(shape=(window_size, 1))
    )

    model.add(
        LSTM(
            units=32,
            activation="tanh"
        )
    )

    model.add(Dense(1))

    model.compile(
        optimizer="adam",
        loss="mean_squared_error"
    )

    return model


def calculate_mape(y_true, y_pred):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    non_zero_mask = y_true != 0

    if not non_zero_mask.any():
        return 0.0

    return np.mean(
        np.abs(
            (y_true[non_zero_mask] - y_pred[non_zero_mask]) /
            y_true[non_zero_mask]
        )
    ) * 100


def generate_forecast_for_store_product(
    db: Session,
    store_product_id: int,
    days_count: int = 7
):
    store_product = db.query(StoreProduct).filter(
        StoreProduct.id == store_product_id
    ).first()

    if store_product is None:
        raise ValueError("Карточка товара не найдена")

    prices = (
        db.query(Price)
        .filter(Price.store_product_id == store_product_id)
        .order_by(Price.checked_at)
        .all()
    )

    if len(prices) < MIN_POINTS_FOR_FORECAST:
        raise ValueError(
            f"Недостаточно данных для прогнозирования. Минимум: {MIN_POINTS_FOR_FORECAST}"
        )

    dataframe = pd.DataFrame(
        [
            {
                "checked_at": price.checked_at,
                "price": float(price.price)
            }
            for price in prices
        ]
    )

    dataframe = dataframe.sort_values("checked_at")

    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_prices = scaler.fit_transform(dataframe[["price"]].values)

    x_all, y_all = create_sequences(
        scaled_prices,
        WINDOW_SIZE
    )

    if len(x_all) == 0:
        raise ValueError("Недостаточно данных для формирования обучающих последовательностей")

    test_size = max(1, int(len(x_all) * TEST_SIZE_RATIO))
    train_size = len(x_all) - test_size

    if train_size <= 0:
        raise ValueError("Недостаточно данных для разделения на обучающую и тестовую выборки")

    x_train = x_all[:train_size]
    y_train = y_all[:train_size]

    x_test = x_all[train_size:]
    y_test = y_all[train_size:]

    model = build_lstm_model(WINDOW_SIZE)

    model.fit(
        x_train,
        y_train,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        verbose=0
    )

    test_predictions_scaled = model.predict(
        x_test,
        verbose=0
    )

    y_test_real = scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()
    test_predictions_real = scaler.inverse_transform(
        test_predictions_scaled
    ).flatten()

    mae = mean_absolute_error(y_test_real, test_predictions_real)
    rmse = np.sqrt(mean_squared_error(y_test_real, test_predictions_real))
    mape = calculate_mape(y_test_real, test_predictions_real)

    db.query(PriceForecast).filter(
        PriceForecast.store_product_id == store_product_id
    ).delete(synchronize_session=False)

    last_window = scaled_prices[-WINDOW_SIZE:].reshape(1, WINDOW_SIZE, 1)

    last_date = dataframe["checked_at"].max()
    created_at = get_current_datetime()

    forecasts = []

    for step in range(1, days_count + 1):
        predicted_scaled = model.predict(
            last_window,
            verbose=0
        )

        predicted_price = scaler.inverse_transform(
            predicted_scaled
        )[0][0]

        predicted_price = max(0, round(float(predicted_price), 2))

        forecast_date = last_date + timedelta(days=step)

        forecast = PriceForecast(
            product_id=store_product.product_id,
            store_product_id=store_product_id,
            forecast_date=forecast_date,
            predicted_price=predicted_price,
            created_at=created_at
        )

        db.add(forecast)
        forecasts.append(forecast)

        last_window = np.append(
            last_window[:, 1:, :],
            predicted_scaled.reshape(1, 1, 1),
            axis=1
        )

    db.commit()

    for forecast in forecasts:
        db.refresh(forecast)

    return {
        "forecasts": forecasts,
        "metrics": {
            "mae": round(float(mae), 4),
            "rmse": round(float(rmse), 4),
            "mape": round(float(mape), 4)
        }
    }


def get_forecasts_for_store_product(
    db: Session,
    store_product_id: int
) -> list[PriceForecast]:
    return (
        db.query(PriceForecast)
        .filter(PriceForecast.store_product_id == store_product_id)
        .order_by(PriceForecast.forecast_date)
        .all()
    )


def delete_forecasts_for_store_product(
    db: Session,
    store_product_id: int
) -> int:
    deleted_count = (
        db.query(PriceForecast)
        .filter(PriceForecast.store_product_id == store_product_id)
        .delete(synchronize_session=False)
    )

    db.commit()

    return deleted_count