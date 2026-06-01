from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from api_client import *
from utils import *


def render_stores_module():
    st.header("Магазины")

    stores = get_stores()

    st.subheader("Список магазинов")

    if stores:
        stores_df = pd.DataFrame(stores)
        stores_df = stores_df.rename(
            columns={
                "id": "ID",
                "name": "Название",
                "base_url": "Сайт"
            }
        )

        st.dataframe(stores_df, width='stretch')
    else:
        st.info("Магазины отсутствуют")

    st.divider()

    st.subheader("Добавление магазина")

    with st.form("create_store_form"):
        store_name = st.text_input("Название магазина")
        base_url = st.text_input("Основной адрес сайта")

        submit = st.form_submit_button("Добавить магазин")

        if submit:
            if not store_name or not base_url:
                st.warning("Введите название магазина и адрес сайта")
            else:
                response = requests.post(
                    f"{API_URL}/stores/",
                    json={
                        "name": store_name,
                        "base_url": base_url
                    }
                )

                if response.status_code == 200:
                    set_local_flash_message("store_create", "Магазин успешно добавлен")
                    st.rerun()
                else:
                    set_api_error("store_api_create", response, "Ошибка при добавлении магазина")
                    st.rerun()

    show_local_flash_message("store_api_create")
    show_local_flash_message("store_create")

    if stores:
        st.divider()

        st.subheader("Редактирование магазина")

        edit_store_options = {
            f"{store['name']} (ID: {store['id']})": store
            for store in stores
        }

        selected_edit_store_label = st.selectbox(
            "Выберите магазин для редактирования",
            list(edit_store_options.keys()),
            key="edit_store_select"
        )

        selected_edit_store = edit_store_options[selected_edit_store_label]

        with st.form("edit_store_form"):
            edited_store_name = st.text_input(
                "Новое название магазина",
                value=selected_edit_store["name"]
            )

            edited_base_url = st.text_input(
                "Новый основной адрес сайта",
                value=selected_edit_store["base_url"]
            )

            update_submit = st.form_submit_button("Сохранить изменения")

            if update_submit:
                if not edited_store_name or not edited_base_url:
                    st.warning("Название магазина и адрес сайта не могут быть пустыми")
                else:
                    response = requests.put(
                        f"{API_URL}/stores/{selected_edit_store['id']}",
                        json={
                            "name": edited_store_name,
                            "base_url": edited_base_url
                        }
                    )

                    if response.status_code == 200:
                        set_local_flash_message("store_edit", "Магазин успешно обновлён")
                        st.rerun()
                    else:
                        set_api_error("store_api_edit", response, "Ошибка при обновлении магазина")
                        st.rerun()

        show_local_flash_message("store_api_edit")
        show_local_flash_message("store_edit")

        st.divider()

        st.subheader("Удаление магазина")

        delete_store_options = {
            f"{store['name']} (ID: {store['id']})": store
            for store in stores
        }

        selected_delete_store_label = st.selectbox(
            "Выберите магазин для удаления",
            list(delete_store_options.keys()),
            key="delete_store_select"
        )

        selected_delete_store = delete_store_options[selected_delete_store_label]

        st.warning(
            "При удалении магазина будут удалены связанные карточки товаров "
            "и связанные с ними записи цен."
        )

        if st.button("Удалить выбранный магазин"):
            response = requests.delete(
                f"{API_URL}/stores/{selected_delete_store['id']}"
            )

            if response.status_code == 200:
                set_local_flash_message("store_delete", "Магазин успешно удалён")
                st.rerun()
            else:
                set_api_error("store_api_delete", response, "Ошибка при удалении магазина")
                st.rerun()

        show_local_flash_message("store_api_delete")
        show_local_flash_message("store_delete")
