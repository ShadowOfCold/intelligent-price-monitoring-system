from datetime import datetime

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
    else:
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
        else:
            prices = prices_response.json()

            if not prices:
                st.info("История цен отсутствует")
            else:
                prices_df = pd.DataFrame(prices)

                prices_df = prepare_price_chart_dataframe(prices_df)

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

                st.dataframe(table_df, width='stretch')

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
                            show_api_error(
                                response,
                                "Ошибка при удалении записей цен"
                            )

                show_local_flash_message("price_delete")

                st.divider()

                fig = px.line(
                    chart_df,
                    x="checked_at",
                    y="price",
                    markers=True,
                    title=f"История цен: {selected_product}",
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
                    width='stretch',
                    config={
                        "displaylogo": False,
                        "locale": "ru"
                    }
                )
