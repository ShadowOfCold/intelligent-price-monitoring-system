import pandas as pd
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session

from backend.models.detected_anomaly import DetectedAnomaly
from backend.models.price import Price
from backend.utils.datetime_utils import get_current_datetime


MIN_POINTS_FOR_ANALYSIS = 5

Z_SCORE_THRESHOLD = 2.5
PRICE_CHANGE_THRESHOLD = 0.25
FIXATION_MIN_LENGTH = 5


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


def detect_anomalies_for_product(
    db: Session,
    product_id: int
) -> list[DetectedAnomaly]:
    prices = (
        db.query(Price)
        .filter(Price.product_id == product_id)
        .order_by(Price.checked_at)
        .all()
    )

    if len(prices) < MIN_POINTS_FOR_ANALYSIS:
        raise ValueError(
            f"Недостаточно данных для анализа. Минимум: {MIN_POINTS_FOR_ANALYSIS}"
        )

    price_ids = [price.id for price in prices]

    db.query(DetectedAnomaly).filter(
        DetectedAnomaly.price_id.in_(price_ids)
    ).delete(synchronize_session=False)

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

    dataframe["price_diff"] = dataframe["price"].diff().fillna(0)
    dataframe["price_pct_change"] = (
        dataframe["price"]
        .pct_change()
        .replace([float("inf"), float("-inf")], 0)
        .fillna(0)
    )

    detected = {}

    # 1. Isolation Forest — нетипичное значение цены
    features = dataframe[
        [
            "price",
            "price_diff",
            "price_pct_change",
        ]
    ]

    model = IsolationForest(
        n_estimators=100,
        contamination="auto",
        random_state=42
    )

    predictions = model.fit_predict(features)
    raw_scores = model.decision_function(features)

    dataframe["iforest_prediction"] = predictions
    dataframe["iforest_raw_score"] = raw_scores

    min_score = dataframe["iforest_raw_score"].min()
    max_score = dataframe["iforest_raw_score"].max()

    if max_score == min_score:
        dataframe["iforest_anomaly_score"] = 0.0
    else:
        dataframe["iforest_anomaly_score"] = (
            (max_score - dataframe["iforest_raw_score"]) /
            (max_score - min_score)
        )

    for _, row in dataframe[dataframe["iforest_prediction"] == -1].iterrows():
        add_anomaly(
            detected,
            int(row["price_id"]),
            "price_outlier",
            float(row["iforest_anomaly_score"])
        )

    # 2. Z-score — статистический выброс
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
            anomaly_score = min(
                1.0,
                float(row["z_score"] / (Z_SCORE_THRESHOLD * 2))
            )

            add_anomaly(
                detected,
                int(row["price_id"]),
                "z_score_outlier",
                anomaly_score
            )

    # 3. Резкий скачок цены
    spike_rows = dataframe[
        dataframe["price_pct_change"] >= PRICE_CHANGE_THRESHOLD
    ]

    for _, row in spike_rows.iterrows():
        anomaly_score = min(
            1.0,
            abs(float(row["price_pct_change"]))
        )

        add_anomaly(
            detected,
            int(row["price_id"]),
            "price_spike",
            anomaly_score
        )

    # 4. Резкое падение цены
    drop_rows = dataframe[
        dataframe["price_pct_change"] <= -PRICE_CHANGE_THRESHOLD
    ]

    for _, row in drop_rows.iterrows():
        anomaly_score = min(
            1.0,
            abs(float(row["price_pct_change"]))
        )

        add_anomaly(
            detected,
            int(row["price_id"]),
            "price_drop",
            anomaly_score
        )

    # 5. Длительная фиксация цены
    dataframe["price_group"] = (
        dataframe["price"] != dataframe["price"].shift()
    ).cumsum()

    fixed_groups = dataframe.groupby("price_group")

    for _, group in fixed_groups:
        if len(group) >= FIXATION_MIN_LENGTH:
            anomaly_score = min(
                1.0,
                len(group) / 10
            )

            for _, row in group.iterrows():
                add_anomaly(
                    detected,
                    int(row["price_id"]),
                    "price_fixation",
                    anomaly_score
                )

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