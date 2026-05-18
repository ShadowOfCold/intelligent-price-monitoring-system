from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from api_client import *
from utils import *


def render_store_products_module():
    st.header("Карточки товаров в магазинах")

    products = get_products()
    stores = get_stores()
    store_products = get_store_products()

    st.subheader("Список карточек товаров")

    if store_products:
        product_name_map = make_product_name_map(products)
        store_name_map = make_store_name_map(stores)

        store_products_df = pd.DataFrame(store_products)

        store_products_df["Товар"] = store_products_df["product_id"].map(product_name_map)
        store_products_df["Магазин"] = store_products_df["store_id"].map(store_name_map)

        store_products_table = store_products_df.rename(
            columns={
                "id": "ID",
                "product_url": "Ссылка на товар"
            }
        )

        store_products_table = store_products_table[
            ["ID", "Товар", "Магазин", "Ссылка на товар"]
        ]

        st.dataframe(store_products_table, width='stretch')
    else:
        st.info("Карточки товаров отсутствуют")

    st.divider()

    st.subheader("Добавление карточки товара")

    if not products:
        st.warning("Сначала добавьте товары")
    elif not stores:
        st.warning("Сначала добавьте магазины")
    else:
        product_map = {
            product["name"]: product["id"]
            for product in products
        }

        store_map = {
            store["name"]: store["id"]
            for store in stores
        }

        with st.form("create_store_product_form"):
            selected_product = st.selectbox(
                "Выберите товар",
                list(product_map.keys()),
                key="create_store_product_product"
            )

            selected_store = st.selectbox(
                "Выберите магазин",
                list(store_map.keys()),
                key="create_store_product_store"
            )

            product_url = st.text_input("Ссылка на страницу товара")

            submit = st.form_submit_button("Добавить карточку товара")

            if submit:
                if not product_url:
                    st.warning("Введите ссылку на страницу товара")
                else:
                    response = requests.post(
                        f"{API_URL}/store-products/",
                        json={
                            "product_id": product_map[selected_product],
                            "store_id": store_map[selected_store],
                            "product_url": product_url
                        }
                    )

                    if response.status_code == 200:
                        set_local_flash_message("store_product_create", "Карточка товара успешно добавлена")
                        st.rerun()
                    else:
                        show_api_error(
                            response,
                            "Ошибка при добавлении карточки товара"
                        )

        show_local_flash_message("store_product_create")

    if store_products and products and stores:
        product_name_map = make_product_name_map(products)
        store_name_map = make_store_name_map(stores)

        st.divider()

        st.subheader("Редактирование карточки товара")

        edit_store_product_options = {}

        for item in store_products:
            product_name = product_name_map.get(
                item["product_id"],
                f"Товар #{item['product_id']}"
            )

            store_name = store_name_map.get(
                item["store_id"],
                f"Магазин #{item['store_id']}"
            )

            label = f"{product_name} — {store_name} (ID: {item['id']})"
            edit_store_product_options[label] = item

        selected_edit_store_product_label = st.selectbox(
            "Выберите карточку товара для редактирования",
            list(edit_store_product_options.keys()),
            key="edit_store_product_select"
        )

        selected_edit_store_product = edit_store_product_options[
            selected_edit_store_product_label
        ]

        product_reverse_map = {
            product["name"]: product["id"]
            for product in products
        }

        store_reverse_map = {
            store["name"]: store["id"]
            for store in stores
        }

        product_names = list(product_reverse_map.keys())
        store_names = list(store_reverse_map.keys())

        current_product_name = product_name_map.get(
            selected_edit_store_product["product_id"]
        )

        current_store_name = store_name_map.get(
            selected_edit_store_product["store_id"]
        )

        current_product_index = product_names.index(current_product_name)
        current_store_index = store_names.index(current_store_name)

        with st.form(
            f"edit_store_product_form_{selected_edit_store_product['id']}"
        ):
            edited_product_name = st.selectbox(
                "Товар",
                product_names,
                index=current_product_index
            )

            edited_store_name = st.selectbox(
                "Магазин",
                store_names,
                index=current_store_index
            )

            edited_product_url = st.text_input(
                "Ссылка на страницу товара",
                value=selected_edit_store_product["product_url"]
            )

            update_submit = st.form_submit_button("Сохранить изменения")

            if update_submit:
                if not edited_product_url:
                    st.warning("Ссылка на товар не может быть пустой")
                else:
                    response = requests.put(
                        f"{API_URL}/store-products/{selected_edit_store_product['id']}",
                        json={
                            "product_id": product_reverse_map[edited_product_name],
                            "store_id": store_reverse_map[edited_store_name],
                            "product_url": edited_product_url
                        }
                    )

                    if response.status_code == 200:
                        set_local_flash_message("store_product_edit", "Карточка товара успешно обновлена")
                        st.rerun()
                    else:
                        show_api_error(
                            response,
                            "Ошибка при обновлении карточки товара"
                        )

        show_local_flash_message("store_product_edit")

        st.divider()

        st.subheader("Удаление карточки товара")

        delete_store_product_options = {}

        for item in store_products:
            product_name = product_name_map.get(
                item["product_id"],
                f"Товар #{item['product_id']}"
            )

            store_name = store_name_map.get(
                item["store_id"],
                f"Магазин #{item['store_id']}"
            )

            label = f"{product_name} — {store_name} (ID: {item['id']})"
            delete_store_product_options[label] = item

        selected_delete_store_product_label = st.selectbox(
            "Выберите карточку товара для удаления",
            list(delete_store_product_options.keys()),
            key="delete_store_product_select"
        )

        selected_delete_store_product = delete_store_product_options[
            selected_delete_store_product_label
        ]

        st.warning(
            "При удалении карточки товара будут удалены связанные с ней записи цен."
        )

        if st.button("Удалить выбранную карточку товара"):
            response = requests.delete(
                f"{API_URL}/store-products/{selected_delete_store_product['id']}"
            )

            if response.status_code == 200:
                set_local_flash_message("store_product_delete", "Карточка товара успешно удалена")
                st.rerun()
            else:
                show_api_error(
                    response,
                    "Ошибка при удалении карточки товара"
                )

        show_local_flash_message("store_product_delete")
