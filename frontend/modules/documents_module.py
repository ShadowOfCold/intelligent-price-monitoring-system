from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from api_client import *
from utils import *


def render_documents_module():
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
        value=datetime.now(ZoneInfo("Asia/Irkutsk")).time(),
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
                set_local_flash_message("document_upload", "Документ успешно загружен и обработан")
                st.rerun()
            else:
                set_api_error(
                    "document_api_upload",
                    response,
                    "Ошибка загрузки документа"
                )

                st.rerun()

    show_local_flash_message("document_api_upload")
    show_local_flash_message("document_upload")

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

            st.subheader("Скачивание документа")

            download_document_options = {
                f"{document['file_name']} (ID: {document['id']})": document
                for document in documents
            }

            selected_download_document_label = st.selectbox(
                "Выберите документ для скачивания",
                list(download_document_options.keys()),
                key="download_document_select"
            )

            selected_download_document = download_document_options[
                selected_download_document_label
            ]

            download_response = requests.get(
                f"{API_URL}/documents/download/{selected_download_document['id']}"
            )

            if download_response.status_code == 200:
                st.download_button(
                    label="Скачать выбранный документ",
                    data=download_response.content,
                    file_name=selected_download_document["file_name"],
                    mime="application/octet-stream"
                )
            else:
                st.warning("Не удалось подготовить документ для скачивания")

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
                    set_local_flash_message(
                        "document_delete",
                        "Документ успешно удалён"
                    )
                    st.rerun()
                else:
                    set_api_error(
                        "document_api_delete",
                        response,
                        "Ошибка при удалении документа"
                    )

                    st.rerun()

            show_local_flash_message("document_api_delete")
            show_local_flash_message("document_delete")
        else:
            st.info("Документы отсутствуют")
    else:
        st.error("Не удалось получить список документов")
