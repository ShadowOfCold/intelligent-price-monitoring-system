from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from api_client import *
from utils import *


def render_price_collection_module():
    st.header("Сбор цен")

    products = get_products()
    stores = get_stores()
    store_products = get_store_products()

    if not products:
        st.warning("Сначала добавьте товары")
    elif not stores:
        st.warning("Сначала добавьте магазины")
    elif not store_products:
        st.warning("Сначала добавьте карточки товаров в магазинах")
    else:
        st.subheader("Автоматический сбор цен по всем товарам")


        if st.button("Собрать цены по всем карточкам товаров"):
            clear_price_collection_results()
            response = requests.post(
                f"{API_URL}/price-collection/all"
            )

            if response.status_code == 200:
                set_local_result(
                    "price_collect_all",
                    response.json()
                )

                st.rerun()
            else:
                show_api_error(
                    response,
                    "Ошибка при сборе всех цен"
                )

        show_price_collection_result("price_collect_all")

        st.divider()

        product_map = {
            product["name"]: product["id"]
            for product in products
        }

        selected_product = st.selectbox(
            "Выберите товар",
            list(product_map.keys()),
            key="price_product_select"
        )

        product_id = product_map[selected_product]

        filtered_store_products = [
            item for item in store_products
            if item["product_id"] == product_id
        ]

        if not filtered_store_products:
            st.warning("Для выбранного товара нет карточек в магазинах")
        else:
            store_product_map = make_store_product_label_map(
                filtered_store_products,
                stores
            )

            st.subheader("Автоматический сбор цен по выбранному товару")

            if st.button("Собрать цены по выбранному товару"):
                clear_price_collection_results()
                response = requests.post(
                    f"{API_URL}/price-collection/product/{product_id}"
                )

                if response.status_code == 200:
                    set_local_result(
                        "price_collect_product",
                        response.json()
                    )

                    st.rerun()
                else:
                    show_api_error(
                        response,
                        "Ошибка при сборе цен по выбранному товару"
                    )

            show_price_collection_result("price_collect_product")

            st.divider()

            st.subheader("Автоматический сбор цены по конкретной карточке")

            selected_store_product_for_parser = st.selectbox(
                "Выберите карточку товара",
                list(store_product_map.keys()),
                key="parser_store_product_select"
            )

            if st.button("Собрать цену по выбранной карточке"):
                clear_price_collection_results()
                response = requests.post(
                    f"{API_URL}/price-collection/",
                    json={
                        "store_product_id": store_product_map[
                            selected_store_product_for_parser
                        ]
                    }
                )

                if response.status_code == 200:
                    collected_price = response.json()

                    set_local_flash_message(
                        "price_collect_store_product",
                        f"Цена успешно собрана: {collected_price['price']}"
                    )

                    st.rerun()
                else:
                    show_api_error(
                        response,
                        "Ошибка при автоматическом сборе цены"
                    )

            show_local_flash_message("price_collect_store_product")

            st.divider()

            st.subheader("Ручное добавление цены")

            with st.form("create_price_form"):
                selected_store_product = st.selectbox(
                    "Выберите карточку товара",
                    list(store_product_map.keys())
                )

                price_value = st.number_input(
                    "Цена",
                    min_value=0.0,
                    step=1.0
                )

                checked_date = st.date_input("Дата проверки")
                checked_time = st.time_input("Время проверки")

                submit = st.form_submit_button("Добавить цену вручную")

                if submit:
                    checked_at = datetime.combine(
                        checked_date,
                        checked_time
                    )

                    response = requests.post(
                        f"{API_URL}/prices/",
                        json={
                            "product_id": product_id,
                            "store_product_id": store_product_map[
                                selected_store_product
                            ],
                            "document_id": None,
                            "price": price_value,
                            "checked_at": checked_at.isoformat()
                        }
                    )

                    if response.status_code == 200:
                        set_local_flash_message("price_create_manual", "Цена успешно добавлена")
                        st.rerun()
                    else:
                        show_api_error(
                            response,
                            "Ошибка при добавлении цены"
                        )
            
            show_local_flash_message("price_create_manual")
