from datetime import timedelta

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import MinMaxScaler
from sqlalchemy.orm import Session
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from tensorflow.keras.models import Sequential

from backend.models.price import Price
from backend.models.price_forecast import PriceForecast
from backend.models.store_product import StoreProduct
from backend.services.market_factor_service import (
    ensure_actual_market_factors,
    get_market_factors_for_date,
)
from backend.utils.datetime_utils import get_current_datetime

MIN_POINTS_FOR_FORECAST = 20
WINDOW_SIZE = 7
EPOCHS = 80
BATCH_SIZE = 8
TEST_SIZE_RATIO = 0.2

MAX_MAPE_FOR_RELIABLE_FORECAST = 50
MAX_VOLATILITY_RATIO = 0.35

FACTOR_COLUMNS = [
    "usd_rate",
    "eur_rate",
    "oil_price",
    "inflation_rate",
    "electronics_index",
    "ai_demand_index",
]

FEATURE_COLUMNS = [
    "price",
    *FACTOR_COLUMNS,
]


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

def validate_price_series_quality(dataframe: pd.DataFrame):
    prices = dataframe["price"].values

    mean_price = np.mean(prices)
    std_price = np.std(prices)

    if mean_price == 0:
        raise ValueError(
            "Невозможно построить прогноз: средняя цена равна нулю"
        )

    volatility_ratio = std_price / mean_price

    if volatility_ratio > MAX_VOLATILITY_RATIO:
        raise ValueError(
            "Временной ряд слишком нестабилен для достоверного прогнозирования. "
            "Рекомендуется сначала проанализировать аномалии или увеличить объём данных."
        )


def create_sequences(data, window_size: int):
    x = []
    y = []

    for index in range(window_size, len(data)):
        x.append(
            data[index - window_size:index]
        )
        y.append(
            data[index, 0]
        )

    return np.array(x), np.array(y)


def build_lstm_model(
    window_size: int,
    features_count: int
):
    model = Sequential()

    model.add(
        Input(
            shape=(
                window_size,
                features_count
            )
        )
    )

    model.add(
        LSTM(
            units=64,
            activation="tanh",
            return_sequences=False
        )
    )

    model.add(
        Dropout(
            0.15
        )
    )

    model.add(
        Dense(
            32,
            activation="relu"
        )
    )

    model.add(
        Dense(
            1
        )
    )

    model.compile(
        optimizer="adam",
        loss="mean_squared_error"
    )

    return model


def get_price_dataframe(
    prices: list[Price]
) -> pd.DataFrame:
    dataframe = pd.DataFrame(
        [
            {
                "checked_at": price.checked_at,
                "price": float(price.price),
            }
            for price in prices
        ]
    )

    dataframe = dataframe.sort_values(
        "checked_at"
    ).reset_index(
        drop=True
    )

    return dataframe


def add_market_factors(
    db: Session,
    dataframe: pd.DataFrame
) -> pd.DataFrame:
    dataframe = dataframe.copy()

    for column in FACTOR_COLUMNS:
        dataframe[column] = 0.0

    for index, row in dataframe.iterrows():
        factors = get_market_factors_for_date(
            db=db,
            target_date=row["checked_at"]
        )

        for factor_name in FACTOR_COLUMNS:
            dataframe.loc[index, factor_name] = float(
                factors.get(
                    factor_name,
                    0.0
                )
            )

    return dataframe


def build_forecast_dataframe(
    db: Session,
    prices: list[Price]
) -> pd.DataFrame:
    dataframe = get_price_dataframe(
        prices
    )

    dataframe = add_market_factors(
        db=db,
        dataframe=dataframe
    )

    dataframe = dataframe.dropna(
        subset=FEATURE_COLUMNS
    ).reset_index(
        drop=True
    )

    return dataframe


def inverse_price_transform(
    price_scaled_values,
    scaler: MinMaxScaler,
    features_count: int
):
    helper = np.zeros(
        (
            len(price_scaled_values),
            features_count
        )
    )

    helper[:, 0] = price_scaled_values

    restored = scaler.inverse_transform(
        helper
    )

    return restored[:, 0]


def get_future_factor_row(
    db: Session,
    forecast_date,
) -> dict[str, float]:
    factors = get_market_factors_for_date(
        db=db,
        target_date=forecast_date
    )

    return {
        factor_name: float(
            factors.get(
                factor_name,
                0.0
            )
        )
        for factor_name in FACTOR_COLUMNS
    }


def generate_forecast_for_store_product(
    db: Session,
    store_product_id: int,
    days_count: int = 7
):
    store_product = (
        db.query(StoreProduct)
        .filter(
            StoreProduct.id == store_product_id
        )
        .first()
    )

    if store_product is None:
        raise ValueError(
            "Карточка товара не найдена"
        )

    prices = (
        db.query(Price)
        .filter(
            Price.store_product_id == store_product_id
        )
        .order_by(
            Price.checked_at
        )
        .all()
    )

    if len(prices) < MIN_POINTS_FOR_FORECAST:
        raise ValueError(
            f"Недостаточно данных для прогнозирования. Минимум: {MIN_POINTS_FOR_FORECAST}"
        )

    ensure_actual_market_factors(
        db=db
    )

    dataframe = build_forecast_dataframe(
        db=db,
        prices=prices
    )

    if len(dataframe) < MIN_POINTS_FOR_FORECAST:
        raise ValueError(
            "Недостаточно данных после добавления рыночных факторов"
        )

    validate_price_series_quality(
        dataframe=dataframe
    )

    values = dataframe[FEATURE_COLUMNS].values

    scaler = MinMaxScaler(
        feature_range=(0, 1)
    )

    scaled_values = scaler.fit_transform(
        values
    )

    x_all, y_all = create_sequences(
        data=scaled_values,
        window_size=WINDOW_SIZE
    )

    if len(x_all) == 0:
        raise ValueError(
            "Недостаточно данных для формирования обучающих последовательностей"
        )

    test_size = max(
        1,
        int(
            len(x_all) * TEST_SIZE_RATIO
        )
    )

    train_size = len(x_all) - test_size

    if train_size <= 0:
        raise ValueError(
            "Недостаточно данных для разделения на обучающую и тестовую выборки"
        )

    x_train = x_all[:train_size]
    y_train = y_all[:train_size]

    x_test = x_all[train_size:]
    y_test = y_all[train_size:]

    model = build_lstm_model(
        window_size=WINDOW_SIZE,
        features_count=len(FEATURE_COLUMNS)
    )

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
    ).flatten()

    y_test_real = inverse_price_transform(
        price_scaled_values=y_test,
        scaler=scaler,
        features_count=len(FEATURE_COLUMNS)
    )

    test_predictions_real = inverse_price_transform(
        price_scaled_values=test_predictions_scaled,
        scaler=scaler,
        features_count=len(FEATURE_COLUMNS)
    )

    mae = mean_absolute_error(
        y_test_real,
        test_predictions_real
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_test_real,
            test_predictions_real
        )
    )

    mape = calculate_mape(
        y_test_real,
        test_predictions_real
    )

    if mape > MAX_MAPE_FOR_RELIABLE_FORECAST:
        raise ValueError(
            f"Качество прогноза недостаточно высокое: MAPE = {round(float(mape), 2)}%. "
            "Ряд содержит слишком резкие или хаотичные изменения."
        )

    db.query(PriceForecast).filter(
        PriceForecast.store_product_id == store_product_id
    ).delete(
        synchronize_session=False
    )

    last_window = scaled_values[-WINDOW_SIZE:].copy()

    last_date = dataframe["checked_at"].max()
    created_at = get_current_datetime()

    forecasts = []

    for step in range(1, days_count + 1):
        forecast_date = last_date + timedelta(
            days=step
        )

        model_input = last_window.reshape(
            1,
            WINDOW_SIZE,
            len(FEATURE_COLUMNS)
        )

        predicted_scaled_price = model.predict(
            model_input,
            verbose=0
        )[0][0]

        predicted_price = inverse_price_transform(
            price_scaled_values=np.array(
                [predicted_scaled_price]
            ),
            scaler=scaler,
            features_count=len(FEATURE_COLUMNS)
        )[0]

        predicted_price = max(
            0,
            round(
                float(predicted_price),
                2
            )
        )

        future_factors = get_future_factor_row(
            db=db,
            forecast_date=forecast_date
        )

        next_row_real = {
            "price": predicted_price,
            **future_factors,
        }

        next_row_dataframe = pd.DataFrame(
            [next_row_real],
            columns=FEATURE_COLUMNS
        )

        next_row_scaled = scaler.transform(
            next_row_dataframe.values
        )[0]

        last_window = np.vstack(
            [
                last_window[1:],
                next_row_scaled
            ]
        )

        forecast = PriceForecast(
            product_id=store_product.product_id,
            store_product_id=store_product_id,
            forecast_date=forecast_date,
            predicted_price=predicted_price,
            created_at=created_at
        )

        db.add(
            forecast
        )

        forecasts.append(
            forecast
        )

    db.commit()

    for forecast in forecasts:
        db.refresh(
            forecast
        )

    return {
        "forecasts": forecasts,
        "metrics": {
            "mae": round(
                float(mae),
                4
            ),
            "rmse": round(
                float(rmse),
                4
            ),
            "mape": round(
                float(mape),
                4
            ),
        }
    }


def get_forecasts_for_store_product(
    db: Session,
    store_product_id: int
) -> list[PriceForecast]:
    return (
        db.query(PriceForecast)
        .filter(
            PriceForecast.store_product_id == store_product_id
        )
        .order_by(
            PriceForecast.forecast_date
        )
        .all()
    )


def delete_forecasts_for_store_product(
    db: Session,
    store_product_id: int
) -> int:
    deleted_count = (
        db.query(PriceForecast)
        .filter(
            PriceForecast.store_product_id == store_product_id
        )
        .delete(
            synchronize_session=False
        )
    )

    db.commit()

    return deleted_count