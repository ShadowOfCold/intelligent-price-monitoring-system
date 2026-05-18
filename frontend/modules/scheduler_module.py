from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from api_client import *
from utils import *


def render_scheduler_module():
    st.header("Автоматизация мониторинга")

    collect_prices_option = st.checkbox(
        "Собирать цены",
        value=True,
        key="scheduler_collect_prices"
    )

    detect_anomalies_option = st.checkbox(
        "Выявлять аномалии",
        value=True,
        key="scheduler_detect_anomalies"
    )

    analyze_correlations_option = st.checkbox(
        "Выполнять корреляционный анализ",
        value=True,
        key="scheduler_analyze_correlations"
    )

    generate_forecasts_option = st.checkbox(
        "Формировать прогнозы",
        value=True,
        key="scheduler_generate_forecasts"
    )

    forecast_days_count = 7

    if generate_forecasts_option:
        forecast_days_count = st.number_input(
            "Количество дней прогноза",
            min_value=1,
            max_value=30,
            value=7,
            step=1,
            key="scheduler_forecast_days_count"
        )

    generate_reports_option = st.checkbox(
        "Формировать отчёты",
        value=True,
        key="scheduler_generate_reports"
    )

    report_format = "Excel и PDF"

    if generate_reports_option:
        report_format = st.selectbox(
            "Формат отчётов",
            [
                "Excel и PDF",
                "Только Excel",
                "Только PDF"
            ],
            key="scheduler_report_format"
        )

    report_format_map = {
        "Excel и PDF": "both",
        "Только Excel": "excel",
        "Только PDF": "pdf"
    }

    st.divider()

    if st.button(
        "Запустить полный цикл мониторинга",
        width="stretch"
    ):
        st.session_state["last_scheduler_success"] = False

        with st.spinner("Выполняется автоматический цикл мониторинга..."):
            response = requests.post(
                f"{API_URL}/scheduler/run-full-cycle",
                json={
                    "collect_prices": collect_prices_option,
                    "detect_anomalies": detect_anomalies_option,
                    "analyze_correlations": analyze_correlations_option,
                    "generate_forecasts": generate_forecasts_option,
                    "generate_reports": generate_reports_option,
                    "forecast_days_count": int(forecast_days_count),
                    "report_format": report_format_map.get(
                        report_format,
                        "both"
                    )
                }
            )

        if response.status_code == 200:
            result = response.json()["result"]

            st.session_state["last_scheduler_result"] = result
            st.session_state["last_scheduler_success"] = True
            st.rerun()
        else:
            show_api_error(
                response,
                "Ошибка выполнения автоматического цикла"
            )

    if st.session_state.get("last_scheduler_success"):
        st.success("Полный цикл мониторинга успешно завершён")

    if "last_scheduler_result" in st.session_state:
        result = st.session_state["last_scheduler_result"]

        st.subheader("Результаты последнего цикла")

        metrics_df = pd.DataFrame(
            [
                {"Показатель": "Всего товаров", "Значение": result["products_total"]},
                {"Показатель": "Всего карточек товаров", "Значение": result["store_products_total"]},
                {"Показатель": "Собрано цен", "Значение": result["prices_collected"]},
                {"Показатель": "Товаров проверено на аномалии", "Значение": result["products_analyzed_for_anomalies"]},
                {"Показатель": "Выявлено аномалий", "Значение": result["anomalies_detected"]},
                {"Показатель": "Товаров проверено на корреляции", "Значение": result["products_analyzed_for_correlations"]},
                {"Показатель": "Построено корреляций", "Значение": result["correlations_built"]},
                {"Показатель": "Карточек проверено для прогноза", "Значение": result["store_products_analyzed_for_forecasts"]},
                {"Показатель": "Товаров с прогнозом", "Значение": result["products_with_forecasts"]},
                {"Показатель": "Создано точек прогноза", "Значение": result["forecast_points_created"]},
                {"Показатель": "Сформировано отчётов", "Значение": result["reports_created"]},
            ]
        )

        st.dataframe(
            metrics_df,
            width="stretch"
        )

        if result["errors"]:
            st.warning("Во время выполнения возникли ошибки")

            for error in result["errors"]:
                st.error(error)

    st.divider()
    st.subheader("Настройка автоматического запуска")

    config_response = requests.get(
        f"{API_URL}/scheduler/config"
    )

    scheduler_config = {}

    if config_response.status_code == 200:
        scheduler_config = config_response.json()

    schedule_enabled = st.checkbox(
        "Включить автоматический запуск",
        value=scheduler_config.get("enabled", False),
        key="schedule_enabled"
    )

    run_times_text = st.text_input(
        "Время запуска через запятую",
        value=", ".join(scheduler_config.get("run_times", ["09:00"])),
        key="schedule_run_times"
    )

    schedule_collect_prices = st.checkbox(
        "Собирать цены по расписанию",
        value=scheduler_config.get("collect_prices", True),
        key="schedule_collect_prices"
    )

    schedule_detect_anomalies = st.checkbox(
        "Выявлять аномалии по расписанию",
        value=scheduler_config.get("detect_anomalies", True),
        key="schedule_detect_anomalies"
    )

    schedule_analyze_correlations = st.checkbox(
        "Выполнять корреляционный анализ по расписанию",
        value=scheduler_config.get("analyze_correlations", True),
        key="schedule_analyze_correlations"
    )

    schedule_generate_forecasts = st.checkbox(
        "Формировать прогнозы по расписанию",
        value=scheduler_config.get("generate_forecasts", True),
        key="schedule_generate_forecasts"
    )

    schedule_forecast_days_count = 7

    if schedule_generate_forecasts:
        schedule_forecast_days_count = st.number_input(
            "Количество дней прогноза по расписанию",
            min_value=1,
            max_value=30,
            value=int(scheduler_config.get("forecast_days_count", 7)),
            step=1,
            key="schedule_forecast_days_count"
        )

    schedule_generate_reports = st.checkbox(
        "Формировать отчёты по расписанию",
        value=scheduler_config.get("generate_reports", True),
        key="schedule_generate_reports"
    )

    schedule_report_format = "Excel и PDF"

    if scheduler_config.get("report_format") == "excel":
        schedule_report_format = "Только Excel"
    elif scheduler_config.get("report_format") == "pdf":
        schedule_report_format = "Только PDF"

    if schedule_generate_reports:
        schedule_report_format = st.selectbox(
            "Формат отчётов по расписанию",
            ["Excel и PDF", "Только Excel", "Только PDF"],
            index=["Excel и PDF", "Только Excel", "Только PDF"].index(
                schedule_report_format
            ),
            key="schedule_report_format"
        )

    if st.button("Сохранить расписание", width="stretch"):
        run_times = [
            item.strip()
            for item in run_times_text.split(",")
            if item.strip()
        ]

        invalid_times = [
            item for item in run_times
            if len(item.split(":")) != 2
        ]

        if invalid_times:
            st.warning("Введите время в формате ЧЧ:ММ, например 09:00, 15:30")
        else:
            response = requests.post(
                f"{API_URL}/scheduler/config",
                json={
                    "enabled": schedule_enabled,
                    "run_times": run_times,
                    "collect_prices": schedule_collect_prices,
                    "detect_anomalies": schedule_detect_anomalies,
                    "analyze_correlations": schedule_analyze_correlations,
                    "generate_forecasts": schedule_generate_forecasts,
                    "generate_reports": schedule_generate_reports,
                    "forecast_days_count": int(schedule_forecast_days_count),
                    "report_format": report_format_map.get(
                        schedule_report_format,
                        "both"
                    )
                }
            )

            if response.status_code == 200:
                st.success("Расписание успешно сохранено")
            else:
                show_api_error(response, "Ошибка при сохранении расписания")

    if scheduler_config.get("last_run_at"):
        st.info(
            f"Последний автоматический запуск: "
            f"{pd.to_datetime(scheduler_config['last_run_at']).strftime('%d.%m.%Y %H:%M')}"
        )

    last_result = scheduler_config.get("last_result")

    if last_result:
        st.divider()

        st.subheader("Результаты последнего автоматического запуска")

        metrics_df = pd.DataFrame(
            [
                {"Показатель": "Всего товаров", "Значение": last_result["products_total"]},
                {"Показатель": "Всего карточек товаров", "Значение": last_result["store_products_total"]},
                {"Показатель": "Собрано цен", "Значение": last_result["prices_collected"]},
                {"Показатель": "Товаров проверено на аномалии", "Значение": last_result["products_analyzed_for_anomalies"]},
                {"Показатель": "Выявлено аномалий", "Значение": last_result["anomalies_detected"]},
                {"Показатель": "Товаров проверено на корреляции", "Значение": last_result["products_analyzed_for_correlations"]},
                {"Показатель": "Построено корреляций", "Значение": last_result["correlations_built"]},
                {"Показатель": "Карточек проверено для прогноза", "Значение": last_result["store_products_analyzed_for_forecasts"]},
                {"Показатель": "Товаров с прогнозом", "Значение": last_result["products_with_forecasts"]},
                {"Показатель": "Создано точек прогноза", "Значение": last_result["forecast_points_created"]},
                {"Показатель": "Сформировано отчётов", "Значение": last_result["reports_created"]},
            ]
        )

        st.dataframe(metrics_df, width="stretch")

        if last_result["errors"]:
            st.warning("Во время автоматического запуска возникли ошибки")

            for error in last_result["errors"]:
                st.error(error)
        else:
            st.success("Автоматический запуск завершён без ошибок")
