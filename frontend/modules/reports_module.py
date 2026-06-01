from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from api_client import *
from utils import *


def render_reports_module():
    st.header("Отчёты")

    products = get_products()

    if not products:
        st.info("Сначала добавьте товары")
    else:
        product_map = {
            product["name"]: product["id"]
            for product in products
        }

        selected_product = st.selectbox(
            "Выберите товар для формирования отчёта",
            list(product_map.keys()),
            key="report_product_select"
        )

        product_id = product_map[selected_product]

        col1, col2, _ = st.columns([1, 1, 4])

        with col1:
            if st.button("Сформировать Excel", width="stretch"):
                response = requests.post(
                    f"{API_URL}/reports/excel",
                    json={"product_id": product_id}
                )

                if response.status_code == 200:
                    set_local_flash_message("report_create", "Excel-отчёт успешно сформирован")
                    st.rerun()
                else:
                    set_api_error("report_api_create", response, "Ошибка при формировании Excel-отчёта")
                    st.rerun()

        show_local_flash_message("report_api_create")
        show_local_flash_message("report_create")

        with col2:
            if st.button("Сформировать PDF", width="stretch"):
                response = requests.post(
                    f"{API_URL}/reports/pdf",
                    json={"product_id": product_id}
                )

                if response.status_code == 200:
                    set_local_flash_message("report_create", "PDF-отчёт успешно сформирован")
                    st.rerun()
                else:
                    set_api_error("report_api_delete", response, "Ошибка при формировании PDF-отчёта")
                    st.rerun()

        show_local_flash_message("report_api_delete")
        show_local_flash_message("report_delete")

    st.divider()

    st.subheader("Список отчётов")

    reports = get_reports()

    if not reports:
        st.info("Отчёты отсутствуют")
    else:
        reports_df = pd.DataFrame(reports)

        reports_df["created_at"] = pd.to_datetime(
            reports_df["created_at"],
            format="ISO8601"
        )

        reports_df["period_start"] = pd.to_datetime(
            reports_df["period_start"],
            format="ISO8601"
        )

        reports_df["period_end"] = pd.to_datetime(
            reports_df["period_end"],
            format="ISO8601"
        )

        table_reports = reports_df.rename(
            columns={
                "id": "ID",
                "file_name": "Имя файла",
                "file_path": "Путь к файлу",
                "created_at": "Дата формирования",
                "period_start": "Начало периода",
                "period_end": "Конец периода"
            }
        )

        table_reports["Дата формирования"] = (
            table_reports["Дата формирования"]
            .dt.strftime("%d.%m.%Y %H:%M")
        )

        table_reports["Начало периода"] = (
            table_reports["Начало периода"]
            .dt.strftime("%d.%m.%Y %H:%M")
        )

        table_reports["Конец периода"] = (
            table_reports["Конец периода"]
            .dt.strftime("%d.%m.%Y %H:%M")
        )

        st.dataframe(
            table_reports[
                [
                    "ID",
                    "Имя файла",
                    "Путь к файлу",
                    "Дата формирования",
                    "Начало периода",
                    "Конец периода"
                ]
            ],
            width="stretch"
        )

        st.divider()

        st.subheader("Скачивание отчёта")

        report_options = {
            f"{report['file_name']} (ID: {report['id']})": report
            for report in reports
        }

        selected_report_label = st.selectbox(
            "Выберите отчёт",
            list(report_options.keys()),
            key="download_report_select"
        )

        selected_report = report_options[selected_report_label]

        download_response = requests.get(
            f"{API_URL}/reports/download/{selected_report['id']}"
        )

        if download_response.status_code == 200:
            st.download_button(
                label="Скачать выбранный отчёт",
                data=download_response.content,
                file_name=selected_report["file_name"],
                mime="application/octet-stream"
            )
        else:
            st.warning("Не удалось подготовить файл для скачивания")

        st.divider()

        st.subheader("Удаление отчёта")

        delete_report_label = st.selectbox(
            "Выберите отчёт для удаления",
            list(report_options.keys()),
            key="delete_report_select"
        )

        selected_delete_report = report_options[delete_report_label]

        st.warning("При удалении отчёта будет удалён файл отчёта и запись о нём.")

        if st.button("Удалить выбранный отчёт"):
            response = requests.delete(
                f"{API_URL}/reports/{selected_delete_report['id']}"
            )

            if response.status_code == 200:
                set_local_flash_message("report_delete", "Отчёт успешно удалён")
                st.rerun()
            else:
                set_api_error("report_api_delete", response, "Ошибка при удалении отчёта")

                st.rerun()

        show_local_flash_message("report_api_delete")
        show_local_flash_message("report_delete")
