from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.io as pio
import requests
import streamlit as st
import os

from dotenv import load_dotenv

load_dotenv()
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = os.getenv("API_PORT", "8000")

API_URL = f"http://{API_HOST}:{API_PORT}"

st.set_page_config(
    page_title="Система мониторинга цен",
    layout="wide"
)

pio.templates.default = "plotly_white"


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


def get_products():
    response = requests.get(f"{API_URL}/products/")
    if response.status_code == 200:
        return response.json()
    return []


def get_stores():
    response = requests.get(f"{API_URL}/stores/")
    if response.status_code == 200:
        return response.json()
    return []


def get_store_products():
    response = requests.get(f"{API_URL}/store-products/")
    if response.status_code == 200:
        return response.json()
    return []


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


st.title("Интеллектуальная система мониторинга цен")

tabs = st.tabs([
    "Товары",
    "Магазины",
    "Карточки товаров",
    "Сбор цен",
    "Документы закупки",
    "История цен"
])

with tabs[0]:
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
                st.success("Товар успешно добавлен")
                st.rerun()
            else:
                show_api_error(response, "Ошибка при добавлении товара")

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
                    st.success("Товар успешно обновлён")
                    st.rerun()
                else:
                    show_api_error(response, "Ошибка при обновлении товара")

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
                show_api_success(response, "Товар успешно удалён")
                st.rerun()
            else:
                show_api_error(response, "Ошибка при удалении товара")

with tabs[1]:
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
                    st.success("Магазин успешно добавлен")
                    st.rerun()
                else:
                    show_api_error(response, "Ошибка при добавлении магазина")

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
                        st.success("Магазин успешно обновлён")
                        st.rerun()
                    else:
                        show_api_error(response, "Ошибка при обновлении магазина")

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
                show_api_success(response, "Магазин успешно удалён")
                st.rerun()
            else:
                show_api_error(response, "Ошибка при удалении магазина")

with tabs[2]:
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
                        st.success("Карточка товара успешно добавлена")
                        st.rerun()
                    else:
                        show_api_error(
                            response,
                            "Ошибка при добавлении карточки товара"
                        )

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
                        st.success("Карточка товара успешно обновлена")
                        st.rerun()
                    else:
                        show_api_error(
                            response,
                            "Ошибка при обновлении карточки товара"
                        )

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
                show_api_success(response, "Карточка товара успешно удалена")
                st.rerun()
            else:
                show_api_error(
                    response,
                    "Ошибка при удалении карточки товара"
                )

with tabs[3]:
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
            response = requests.post(
                f"{API_URL}/price-collection/all"
            )

            if response.status_code == 200:
                collected_prices = response.json()

                st.success(
                    f"Сбор завершён. Получено цен: {len(collected_prices)}"
                )

                st.rerun()
            else:
                show_api_error(
                    response,
                    "Ошибка при сборе всех цен"
                )

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
                response = requests.post(
                    f"{API_URL}/price-collection/product/{product_id}"
                )

                if response.status_code == 200:
                    collected_prices = response.json()

                    st.success(
                        f"Сбор завершён. Получено цен: {len(collected_prices)}"
                    )

                    st.rerun()
                else:
                    show_api_error(
                        response,
                        "Ошибка при сборе цен по выбранному товару"
                    )

            st.divider()

            st.subheader("Автоматический сбор цены по конкретной карточке")

            selected_store_product_for_parser = st.selectbox(
                "Выберите карточку товара",
                list(store_product_map.keys()),
                key="parser_store_product_select"
            )

            if st.button("Собрать цену по выбранной карточке"):
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

                    st.success(
                        f"Цена успешно собрана: {collected_price['price']}"
                    )

                    st.rerun()
                else:
                    show_api_error(
                        response,
                        "Ошибка при автоматическом сборе цены"
                    )

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
                        st.success("Цена успешно добавлена")
                        st.rerun()
                    else:
                        show_api_error(
                            response,
                            "Ошибка при добавлении цены"
                        )

with tabs[4]:
    st.header("Документы закупки")

    uploaded_file = st.file_uploader(
        "Выберите файл документа закупки",
        type=["xlsx", "xls", "pdf"]
    )

    price_date = st.date_input(
        "Дата цен в документе",
        key="document_price_date"
    )

    price_time = st.time_input(
        "Время цен в документе",
        key="document_price_time"
    )

    if st.button("Загрузить документ"):
        if uploaded_file is None:
            st.warning("Выберите файл")
        else:
            price_checked_at = datetime.combine(
                price_date,
                price_time
            )

            response = requests.post(
                f"{API_URL}/documents/upload",
                files={
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        uploaded_file.type
                    )
                },
                data={
                    "price_checked_at": price_checked_at.isoformat()
                }
            )

            if response.status_code == 200:
                st.success("Документ успешно загружен и обработан")
                st.rerun()
            else:
                show_api_error(
                    response,
                    "Ошибка загрузки документа"
                )

    st.divider()

    documents_response = requests.get(
        f"{API_URL}/documents/"
    )

    if documents_response.status_code == 200:
        documents = documents_response.json()

        if documents:
            documents_df = pd.DataFrame(documents)

            documents_df = documents_df.rename(
                columns={
                    "id": "ID",
                    "file_name": "Имя файла",
                    "file_type": "Тип файла",
                    "file_path": "Путь к файлу",
                    "uploaded_at": "Дата загрузки"
                }
            )

            documents_df["Дата загрузки"] = pd.to_datetime(
                documents_df["Дата загрузки"]
            ).dt.strftime("%d.%m.%Y %H:%M")

            st.dataframe(
                documents_df[
                    [
                        "ID",
                        "Имя файла",
                        "Тип файла",
                        "Путь к файлу",
                        "Дата загрузки"
                    ]
                ],
                width='stretch'
            )

            st.divider()

            st.subheader("Удаление документа")

            delete_document_options = {
                f"{document['file_name']} (ID: {document['id']})": document
                for document in documents
            }

            selected_delete_document_label = st.selectbox(
                "Выберите документ для удаления",
                list(delete_document_options.keys()),
                key="delete_document_select"
            )

            selected_delete_document = delete_document_options[
                selected_delete_document_label
            ]

            st.warning(
                "При удалении документа будут удалены связанные с ним цены."
            )

            if st.button("Удалить выбранный документ"):
                response = requests.delete(
                    f"{API_URL}/documents/{selected_delete_document['id']}"
                )

                if response.status_code == 200:
                    show_api_success(
                        response,
                        "Документ успешно удалён"
                    )
                    st.rerun()
                else:
                    show_api_error(
                        response,
                        "Ошибка при удалении документа"
                    )
        else:
            st.info("Документы отсутствуют")
    else:
        st.error("Не удалось получить список документов")

with tabs[5]:
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

                prices_df["checked_at"] = pd.to_datetime(
                    prices_df["checked_at"],
                    format="ISO8601"
                )

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
                            show_api_success(
                                response,
                                "Выбранные записи цен успешно удалены"
                            )
                            st.rerun()
                        else:
                            show_api_error(
                                response,
                                "Ошибка при удалении записей цен"
                            )

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