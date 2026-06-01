import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from api_client import *
from utils import *


def render_price_history_module():
    st.header("История цен")

    products = get_products()

    if not products:
        st.info("Сначала добавьте товары")
        return

    product_map = {
        product["name"]: product["id"]
        for product in products
    }

    selected_product = st.selectbox(
        "Выберите товар",
        list(product_map.keys()),
        key="history_product_select"
    )

    product_id = product_map[selected_product]

    prices_response = requests.get(
        f"{API_URL}/prices/product/{product_id}"
    )

    if prices_response.status_code != 200:
        show_api_error(prices_response, "Не удалось получить историю цен")
        return

    prices = prices_response.json()

    if not prices:
        st.info("История цен отсутствует")
        return

    prices_df = pd.DataFrame(prices)
    prices_df = prepare_price_chart_dataframe(prices_df)

    store_products = get_store_products()

    product_store_products = [
        item for item in store_products
        if item["product_id"] == product_id
    ]

    store_product_options = {
        "Все карточки товара": None
    }

    for item in product_store_products:
        label = (
            f"{item.get('store_name', 'Магазин')} "
            f"(ID карточки: {item['id']})"
        )
        store_product_options[label] = item["id"]

    selected_store_product_label = st.selectbox(
        "Выберите карточку товара",
        list(store_product_options.keys()),
        key="history_store_product_select"
    )

    selected_store_product_id = store_product_options[selected_store_product_label]

    if selected_store_product_id is not None:
        prices_df = prices_df[
            prices_df["store_product_id"] == selected_store_product_id
        ]

    if prices_df.empty:
        st.info("История цен для выбранной карточки товара отсутствует")
        return

    chart_df = prices_df.copy()

    table_df = prices_df.rename(
        columns={
            "id": "ID",
            "product_id": "ID товара",
            "store_product_id": "ID карточки товара",
            "document_id": "ID документа",
            "price": "Цена",
            "checked_at": "Дата проверки"
        }
    )

    table_df["Дата проверки"] = (
        table_df["Дата проверки"]
        .dt.strftime("%d.%m.%Y %H:%M")
    )

    st.dataframe(table_df, width="stretch")

    st.divider()
    st.subheader("Удаление записей цен")

    delete_price_options = {}

    for _, row in table_df.iterrows():
        label = (
            f"{row['Дата проверки']} — "
            f"{row['Цена']} ₽ — "
            f"ID цены: {row['ID']}"
        )
        delete_price_options[label] = int(row["ID"])

    selected_price_labels = st.multiselect(
        "Выберите записи цен для удаления",
        list(delete_price_options.keys())
    )

    if st.button("Удалить выбранные записи цен"):
        if not selected_price_labels:
            st.warning("Выберите хотя бы одну запись цены")
        else:
            selected_price_ids = [
                delete_price_options[label]
                for label in selected_price_labels
            ]

            response = requests.post(
                f"{API_URL}/prices/delete-multiple",
                json={
                    "price_ids": selected_price_ids
                }
            )

            if response.status_code == 200:
                set_local_flash_message(
                    "price_delete",
                    "Выбранные записи цен успешно удалены"
                )
                st.rerun()
            else:
                set_api_error(
                    "price_api_delete",
                    response,
                    "Ошибка при удалении записей цен"
                )

                st.rerun()

    show_local_flash_message("price_api_delete")
    show_local_flash_message("price_delete")

    st.divider()

    if selected_store_product_id is None:
        chart_title = f"История цен: {selected_product}"
    else:
        chart_title = f"История цен: {selected_product} — {selected_store_product_label}"

    fig = px.line(
        chart_df,
        x="checked_at",
        y="price",
        markers=True,
        title=chart_title,
        labels={
            "checked_at": "Дата",
            "price": "Цена"
        }
    )

    fig.update_layout(
        xaxis_title="Дата",
        yaxis_title="Цена",
        hovermode="x unified"
    )

    fig.update_xaxes(
        tickformat="%d.%m.%Y %H:%M"
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config={
            "displaylogo": False,
            "locale": "ru"
        }
    )