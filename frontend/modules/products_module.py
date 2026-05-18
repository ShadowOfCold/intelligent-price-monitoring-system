from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from api_client import *
from utils import *


def render_products_module():
    st.header("Товары")

    products = get_products()
    existing_categories = get_existing_categories(products)

    st.subheader("Список товаров")

    if products:
        products_df = pd.DataFrame(products)
        products_df = products_df.rename(
            columns={
                "id": "ID",
                "name": "Название",
                "category": "Категория"
            }
        )

        st.dataframe(products_df, width='stretch')
    else:
        st.info("Товары отсутствуют")

    st.divider()

    st.subheader("Добавление товара")

    category_options = ["Без категории", "Новая категория"] + existing_categories

    name = st.text_input(
        "Название товара",
        key="create_product_name"
    )

    selected_category_option = st.selectbox(
        "Категория",
        category_options,
        key="create_product_category"
    )

    new_category = None

    if selected_category_option == "Новая категория":
        new_category = st.text_input(
            "Название новой категории",
            key="create_product_new_category"
        )

    if st.button("Добавить товар"):
        if not name:
            st.warning("Введите название товара")
        elif selected_category_option == "Новая категория" and not new_category:
            st.warning("Введите название новой категории")
        else:
            category = resolve_category(
                selected_category_option,
                new_category
            )

            response = requests.post(
                f"{API_URL}/products/",
                json={
                    "name": name,
                    "category": category
                }
            )

            if response.status_code == 200:
                set_local_flash_message("product_create", "Товар успешно добавлен")
                st.rerun()
            else:
                show_api_error(response, "Ошибка при добавлении товара")

    show_local_flash_message("product_create")

    if products:
        st.divider()

        st.subheader("Редактирование товара")

        edit_product_options = {
            f"{product['name']} (ID: {product['id']})": product
            for product in products
        }

        selected_edit_product_label = st.selectbox(
            "Выберите товар для редактирования",
            list(edit_product_options.keys()),
            key="edit_product_select"
        )

        selected_edit_product = edit_product_options[selected_edit_product_label]

        edited_name = st.text_input(
            "Новое название товара",
            value=selected_edit_product["name"],
            key=f"edit_product_name_{selected_edit_product['id']}"
        )

        edit_category_options = ["Без категории", "Новая категория"] + existing_categories

        current_category = selected_edit_product["category"]

        if current_category in edit_category_options:
            current_category_index = edit_category_options.index(current_category)
        else:
            current_category_index = 0

        edited_category_option = st.selectbox(
            "Категория",
            edit_category_options,
            index=current_category_index,
            key=f"edit_product_category_{selected_edit_product['id']}"
        )

        edited_new_category = None

        if edited_category_option == "Новая категория":
            edited_new_category = st.text_input(
                "Название новой категории",
                key=f"edit_product_new_category_{selected_edit_product['id']}"
            )

        if st.button("Сохранить изменения товара"):
            if not edited_name:
                st.warning("Название товара не может быть пустым")
            elif edited_category_option == "Новая категория" and not edited_new_category:
                st.warning("Введите название новой категории")
            else:
                edited_category = resolve_category(
                    edited_category_option,
                    edited_new_category
                )

                response = requests.put(
                    f"{API_URL}/products/{selected_edit_product['id']}",
                    json={
                        "name": edited_name,
                        "category": edited_category
                    }
                )

                if response.status_code == 200:
                    set_local_flash_message("product_edit", "Товар успешно обновлён")
                    st.rerun()
                else:
                    show_api_error(response, "Ошибка при обновлении товара")

        show_local_flash_message("product_edit")

        st.divider()

        st.subheader("Удаление товара")

        delete_product_options = {
            f"{product['name']} (ID: {product['id']})": product
            for product in products
        }

        selected_delete_product_label = st.selectbox(
            "Выберите товар для удаления",
            list(delete_product_options.keys()),
            key="delete_product_select"
        )

        selected_delete_product = delete_product_options[selected_delete_product_label]

        st.warning(
            "При удалении товара будут удалены связанные карточки товаров, цены, "
            "аномалии, прогнозы и результаты анализа."
        )

        if st.button("Удалить выбранный товар"):
            response = requests.delete(
                f"{API_URL}/products/{selected_delete_product['id']}"
            )

            if response.status_code == 200:
                set_local_flash_message("product_delete", "Товар успешно удалён")
                st.rerun()
            else:
                show_api_error(response, "Ошибка при удалении товара")

        show_local_flash_message("product_delete")
