from urllib.parse import urlparse

import pandas as pd
import streamlit as st


def is_valid_url(value: str) -> bool:
    try:
        result = urlparse(value)
        return result.scheme in ("http", "https") and bool(result.netloc)
    except Exception:
        return False

def show_api_error(response, default_message: str):
    try:
        error_detail = response.json().get("detail", default_message)
        st.error(error_detail)
    except Exception:
        st.error(default_message)


def show_api_success(response, default_message: str):
    try:
        message = response.json().get("message", default_message)
        st.success(message)
    except Exception:
        st.success(default_message)

def set_api_error(key: str, response, default_message: str):
    try:
        error_detail = response.json().get("detail", default_message)
    except Exception:
        error_detail = default_message

    set_local_flash_message(
        key=key,
        message=error_detail,
        message_type="error"
    )


def set_api_success(key: str, response, default_message: str):
    try:
        message = response.json().get("message", default_message)
    except Exception:
        message = default_message

    set_local_flash_message(
        key=key,
        message=message,
        message_type="success"
    )

def set_local_flash_message(key: str, message: str, message_type: str = "success"):
    st.session_state[f"{key}_message"] = message
    st.session_state[f"{key}_message_type"] = message_type


def show_local_flash_message(key: str):
    message = st.session_state.pop(f"{key}_message", None)
    message_type = st.session_state.pop(f"{key}_message_type", "success")

    if not message:
        return

    if message_type == "success":
        st.success(message)
    elif message_type == "warning":
        st.warning(message)
    elif message_type == "error":
        st.error(message)
    else:
        st.info(message)


PRICE_COLLECTION_RESULT_KEYS = [
    "price_collect_all",
    "price_collect_product",
    "price_collect_store_product"
]


def clear_price_collection_results():
    for key in PRICE_COLLECTION_RESULT_KEYS:
        st.session_state.pop(f"{key}_result", None)


def set_local_result(key: str, result: dict):
    clear_price_collection_results()
    st.session_state[f"{key}_result"] = result


def show_price_collection_result(key: str):
    result = st.session_state.pop(f"{key}_result", None)

    if not result:
        return

    collected = result.get("collected", [])
    errors = result.get("errors", [])

    st.success(
        f"Сбор завершён. Получено цен: {len(collected)}"
    )

    if errors:
        st.warning(
            f"Во время сбора возникло ошибок: {len(errors)}"
        )

        for error in errors:
            st.error(
                f"{error.get('label', 'Карточка товара')}: "
                f"{error.get('message', 'ошибка сбора цены')}"
            )


def get_existing_categories(products):
    return sorted(
        {
            product["category"]
            for product in products
            if product.get("category")
        }
    )


def make_product_name_map(products):
    return {product["id"]: product["name"] for product in products}


def make_store_name_map(stores):
    return {store["id"]: store["name"] for store in stores}


def make_store_product_label_map(store_products, stores):
    store_name_map = make_store_name_map(stores)
    result = {}

    for item in store_products:
        store_name = store_name_map.get(
            item["store_id"],
            f"Магазин #{item['store_id']}"
        )

        label = f"{store_name} (карточка #{item['id']})"
        result[label] = item["id"]

    return result


def resolve_category(selected_option: str, new_category: str | None):
    if selected_option == "Без категории":
        return None

    if selected_option == "Новая категория":
        return new_category if new_category else None

    return selected_option


def prepare_price_chart_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    chart_dataframe = dataframe.copy()

    if "price" in chart_dataframe.columns:
        chart_dataframe["price"] = pd.to_numeric(
            chart_dataframe["price"],
            errors="coerce"
        )

    if "predicted_price" in chart_dataframe.columns:
        chart_dataframe["predicted_price"] = pd.to_numeric(
            chart_dataframe["predicted_price"],
            errors="coerce"
        )

    if "correlation_value" in chart_dataframe.columns:
        chart_dataframe["correlation_value"] = pd.to_numeric(
            chart_dataframe["correlation_value"],
            errors="coerce"
        )

    if "checked_at" in chart_dataframe.columns:
        chart_dataframe["checked_at"] = pd.to_datetime(
            chart_dataframe["checked_at"],
            format="ISO8601",
            errors="coerce",
            utc=False
        )

    if "forecast_date" in chart_dataframe.columns:
        chart_dataframe["forecast_date"] = pd.to_datetime(
            chart_dataframe["forecast_date"],
            format="ISO8601",
            errors="coerce",
            utc=False
        )

    chart_dataframe = chart_dataframe.dropna(
        subset=[
            column for column in [
                "price",
                "predicted_price",
                "checked_at",
                "forecast_date"
            ]
            if column in chart_dataframe.columns
        ]
    )

    if "checked_at" in chart_dataframe.columns:
        chart_dataframe = chart_dataframe.sort_values("checked_at")

    if "forecast_date" in chart_dataframe.columns:
        chart_dataframe = chart_dataframe.sort_values("forecast_date")

    return chart_dataframe
