import pandas as pd
from sqlalchemy.orm import Session

from backend.models.detected_anomaly import DetectedAnomaly
from backend.models.price import Price
from backend.models.product import Product
from backend.models.store_product import StoreProduct
from backend.services.market_factor_service import (
    ensure_actual_market_factors,
    get_factor_weights_for_category,
    get_market_factors_for_date,
)
from backend.utils.datetime_utils import get_current_datetime


MIN_POINTS_FOR_ANALYSIS = 5

Z_SCORE_THRESHOLD = 3.5
PRICE_CHANGE_THRESHOLD = 0.25
FIXATION_MIN_LENGTH = 5

FACTOR_EXPLANATION_THRESHOLD = 0.15
UNEXPLAINED_CHANGE_THRESHOLD = 0.15


def calculate_risk_level(anomaly_score: float) -> str:
    if anomaly_score >= 0.75:
        return "high"

    if anomaly_score >= 0.45:
        return "medium"

    return "low"


def add_anomaly(
    anomalies: dict,
    price_id: int,
    anomaly_type: str,
    anomaly_score: float
):
    key = (price_id, anomaly_type)
    anomaly_score = max(0.0, min(1.0, float(anomaly_score)))

    if key not in anomalies:
        anomalies[key] = anomaly_score
    else:
        anomalies[key] = max(anomalies[key], anomaly_score)


def build_price_dataframe(prices: list[Price]) -> pd.DataFrame:
    dataframe = pd.DataFrame(
        [
            {
                "price_id": price.id,
                "price": float(price.price),
                "checked_at": price.checked_at,
            }
            for price in prices
        ]
    )

    dataframe = dataframe.sort_values("checked_at").reset_index(drop=True)

    dataframe["price_diff"] = dataframe["price"].diff().fillna(0)
    dataframe["price_pct_change"] = (
        dataframe["price"]
        .pct_change()
        .replace([float("inf"), float("-inf")], 0)
        .fillna(0)
    )

    return dataframe


def get_product_category(db: Session, product_id: int) -> str | None:
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if product is None:
        return None

    return product.category


def calculate_factor_impact_for_row(
    db: Session,
    category: str | None,
    previous_date,
    current_date
) -> float:
    weights = get_factor_weights_for_category(
        db=db,
        category=category
    )

    if not weights:
        return 0.0

    previous_factors = get_market_factors_for_date(
        db=db,
        target_date=previous_date
    )

    current_factors = get_market_factors_for_date(
        db=db,
        target_date=current_date
    )

    factor_impact = 0.0

    for weight_item in weights:
        factor_name = weight_item.factor_name
        weight = float(weight_item.weight)

        previous_value = previous_factors.get(factor_name)
        current_value = current_factors.get(factor_name)

        if previous_value is None or current_value is None:
            continue

        if previous_value == 0:
            continue

        factor_change = abs(
            (current_value - previous_value) / previous_value
        )

        factor_impact += factor_change * weight

    return min(1.0, float(factor_impact))


def add_factor_features(
    db: Session,
    dataframe: pd.DataFrame,
    category: str | None
) -> pd.DataFrame:
    dataframe = dataframe.copy()

    dataframe["factor_impact"] = 0.0
    dataframe["unexplained_change"] = dataframe["price_pct_change"].abs()

    for index in range(1, len(dataframe)):
        previous_date = dataframe.loc[index - 1, "checked_at"]
        current_date = dataframe.loc[index, "checked_at"]

        factor_impact = calculate_factor_impact_for_row(
            db=db,
            category=category,
            previous_date=previous_date,
            current_date=current_date
        )

        price_change = abs(
            float(dataframe.loc[index, "price_pct_change"])
        )

        unexplained_change = max(
            0.0,
            price_change - factor_impact
        )

        dataframe.loc[index, "factor_impact"] = factor_impact
        dataframe.loc[index, "unexplained_change"] = unexplained_change

    return dataframe


def detect_anomalies_in_dataframe(dataframe: pd.DataFrame) -> dict:
    detected = {}

    explained_change_price_ids = set()
    unexplained_change_price_ids = set()

    explained_change_rows = dataframe[
        (
            dataframe["price_pct_change"].abs() >= PRICE_CHANGE_THRESHOLD
        )
        &
        (
            dataframe["factor_impact"] >= FACTOR_EXPLANATION_THRESHOLD
        )
        &
        (
            dataframe["unexplained_change"] < UNEXPLAINED_CHANGE_THRESHOLD
        )
    ]

    for _, row in explained_change_rows.iterrows():
        price_id = int(row["price_id"])
        explained_change_price_ids.add(price_id)

        add_anomaly(
            detected,
            price_id,
            "factor_explained_change",
            0.25
        )

    unexplained_spike_rows = dataframe[
        (
            dataframe["price_pct_change"] >= PRICE_CHANGE_THRESHOLD
        )
        &
        (
            dataframe["unexplained_change"] >= UNEXPLAINED_CHANGE_THRESHOLD
        )
    ]

    for _, row in unexplained_spike_rows.iterrows():
        price_id = int(row["price_id"])

        current_index = int(row.name)
        previous_index = current_index - 1

        previous_price_id = None

        if previous_index >= 0:
            previous_price_id = int(
                dataframe.loc[previous_index, "price_id"]
            )

        if previous_price_id in unexplained_change_price_ids:
            continue

        unexplained_change_price_ids.add(price_id)

        anomaly_score = min(
            1.0,
            float(row["unexplained_change"])
        )

        add_anomaly(
            detected,
            price_id,
            "unexplained_price_spike",
            anomaly_score
        )

    unexplained_drop_rows = dataframe[
        (
            dataframe["price_pct_change"] <= -PRICE_CHANGE_THRESHOLD
        )
        &
        (
            dataframe["unexplained_change"] >= UNEXPLAINED_CHANGE_THRESHOLD
        )
    ]

    for _, row in unexplained_drop_rows.iterrows():
        price_id = int(row["price_id"])

        current_index = int(row.name)
        previous_index = current_index - 1

        previous_price_id = None

        if previous_index >= 0:
            previous_price_id = int(
                dataframe.loc[previous_index, "price_id"]
            )

        if previous_price_id in unexplained_change_price_ids:
            continue

        unexplained_change_price_ids.add(price_id)

        anomaly_score = min(
            1.0,
            float(row["unexplained_change"])
        )

        add_anomaly(
            detected,
            price_id,
            "unexplained_price_drop",
            anomaly_score
        )

    mean_price = dataframe["price"].mean()
    std_price = dataframe["price"].std()

    if std_price and std_price > 0:
        dataframe["z_score"] = abs(
            (dataframe["price"] - mean_price) / std_price
        )

        z_anomalies = dataframe[
            dataframe["z_score"] >= Z_SCORE_THRESHOLD
        ]

        for _, row in z_anomalies.iterrows():
            price_id = int(row["price_id"])

            if (
                price_id in explained_change_price_ids
                or price_id in unexplained_change_price_ids
            ):
                continue

            anomaly_score = min(
                1.0,
                float(row["z_score"] / (Z_SCORE_THRESHOLD * 2))
            )

            add_anomaly(
                detected,
                price_id,
                "z_score_outlier",
                anomaly_score
            )

    dataframe["price_group"] = (
        dataframe["price"] != dataframe["price"].shift()
    ).cumsum()

    fixed_groups = dataframe.groupby("price_group")

    for _, group in fixed_groups:
        if len(group) >= FIXATION_MIN_LENGTH:
            last_row = group.iloc[-1]

            anomaly_score = min(
                1.0,
                len(group) / 10
            )

            add_anomaly(
                detected,
                int(last_row["price_id"]),
                "price_fixation",
                anomaly_score
            )

    return detected


def save_detected_anomalies(
    db: Session,
    detected: dict
) -> list[DetectedAnomaly]:
    detected_anomalies = []

    for (price_id, anomaly_type), anomaly_score in detected.items():
        anomaly = DetectedAnomaly(
            price_id=price_id,
            anomaly_type=anomaly_type,
            anomaly_score=anomaly_score,
            risk_level=calculate_risk_level(anomaly_score),
            detected_at=get_current_datetime()
        )

        db.add(anomaly)
        detected_anomalies.append(anomaly)

    db.commit()

    for anomaly in detected_anomalies:
        db.refresh(anomaly)

    return detected_anomalies


def detect_anomalies_for_prices(
    db: Session,
    prices: list[Price],
    product_id: int
) -> list[DetectedAnomaly]:
    if len(prices) < MIN_POINTS_FOR_ANALYSIS:
        raise ValueError(
            f"Недостаточно данных для анализа. Минимум: {MIN_POINTS_FOR_ANALYSIS}"
        )

    ensure_actual_market_factors(db=db)

    price_ids = [price.id for price in prices]

    db.query(DetectedAnomaly).filter(
        DetectedAnomaly.price_id.in_(price_ids)
    ).delete(synchronize_session=False)

    category = get_product_category(
        db=db,
        product_id=product_id
    )

    dataframe = build_price_dataframe(prices)

    dataframe = add_factor_features(
        db=db,
        dataframe=dataframe,
        category=category
    )

    detected = detect_anomalies_in_dataframe(dataframe)

    return save_detected_anomalies(
        db=db,
        detected=detected
    )


def detect_anomalies_for_product(
    db: Session,
    product_id: int
) -> list[DetectedAnomaly]:
    store_products = (
        db.query(StoreProduct)
        .filter(StoreProduct.product_id == product_id)
        .order_by(StoreProduct.id)
        .all()
    )

    if not store_products:
        raise ValueError("Для выбранного товара нет карточек в магазинах")

    all_anomalies = []

    for store_product in store_products:
        prices = (
            db.query(Price)
            .filter(Price.store_product_id == store_product.id)
            .order_by(Price.checked_at)
            .all()
        )

        if len(prices) < MIN_POINTS_FOR_ANALYSIS:
            continue

        anomalies = detect_anomalies_for_prices(
            db=db,
            prices=prices,
            product_id=product_id
        )

        all_anomalies.extend(anomalies)

    if not all_anomalies:
        raise ValueError(
            f"Недостаточно данных для анализа. Минимум: {MIN_POINTS_FOR_ANALYSIS} цен по карточке товара"
        )

    return all_anomalies


def detect_anomalies_for_store_product(
    db: Session,
    store_product_id: int
) -> list[DetectedAnomaly]:
    prices = (
        db.query(Price)
        .filter(Price.store_product_id == store_product_id)
        .order_by(Price.checked_at)
        .all()
    )

    if not prices:
        raise ValueError("Для выбранной карточки товара нет цен")

    product_id = prices[0].product_id

    return detect_anomalies_for_prices(
        db=db,
        prices=prices,
        product_id=product_id
    )


def get_anomalies_for_product(
    db: Session,
    product_id: int
):
    anomalies = (
        db.query(DetectedAnomaly, Price)
        .join(Price, DetectedAnomaly.price_id == Price.id)
        .filter(Price.product_id == product_id)
        .order_by(Price.checked_at)
        .all()
    )

    result = []

    for anomaly, price in anomalies:
        result.append(
            {
                "id": anomaly.id,
                "price_id": anomaly.price_id,
                "product_id": price.product_id,
                "store_product_id": price.store_product_id,
                "price": price.price,
                "checked_at": price.checked_at,
                "anomaly_type": anomaly.anomaly_type,
                "anomaly_score": anomaly.anomaly_score,
                "risk_level": anomaly.risk_level,
                "detected_at": anomaly.detected_at,
            }
        )

    return result


def get_anomalies_for_store_product(
    db: Session,
    store_product_id: int
):
    anomalies = (
        db.query(DetectedAnomaly, Price)
        .join(Price, DetectedAnomaly.price_id == Price.id)
        .filter(Price.store_product_id == store_product_id)
        .order_by(Price.checked_at)
        .all()
    )

    result = []

    for anomaly, price in anomalies:
        result.append(
            {
                "id": anomaly.id,
                "price_id": anomaly.price_id,
                "product_id": price.product_id,
                "store_product_id": price.store_product_id,
                "price": price.price,
                "checked_at": price.checked_at,
                "anomaly_type": anomaly.anomaly_type,
                "anomaly_score": anomaly.anomaly_score,
                "risk_level": anomaly.risk_level,
                "detected_at": anomaly.detected_at,
            }
        )

    return result


def delete_anomalies_for_product(
    db: Session,
    product_id: int
) -> int:
    prices = (
        db.query(Price)
        .filter(Price.product_id == product_id)
        .all()
    )

    price_ids = [price.id for price in prices]

    if not price_ids:
        return 0

    deleted_count = (
        db.query(DetectedAnomaly)
        .filter(DetectedAnomaly.price_id.in_(price_ids))
        .delete(synchronize_session=False)
    )

    db.commit()

    return deleted_count


def delete_anomalies_for_store_product(
    db: Session,
    store_product_id: int
) -> int:
    prices = (
        db.query(Price)
        .filter(Price.store_product_id == store_product_id)
        .all()
    )

    price_ids = [price.id for price in prices]

    if not price_ids:
        return 0

    deleted_count = (
        db.query(DetectedAnomaly)
        .filter(DetectedAnomaly.price_id.in_(price_ids))
        .delete(synchronize_session=False)
    )

    db.commit()

    return deleted_count