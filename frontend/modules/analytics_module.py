import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from api_client import *
from utils import *


def render_analytics_module():
    st.header("Аналитика")

    products = get_products()

    if not products:
        st.info("Сначала добавьте товары")
        return

    product_map = {
        product["name"]: product["id"]
        for product in products
    }

    selected_product = st.selectbox(
        "Выберите товар для анализа",
        list(product_map.keys()),
        key="analytics_product_select"
    )

    product_id = product_map[selected_product]

    st.subheader("Обнаружение аномалий")

    stores = get_stores()
    store_products = get_store_products()

    filtered_store_products = [
        item for item in store_products
        if item["product_id"] == product_id
    ]

    anomaly_mode = st.radio(
        "Режим обнаружения аномалий",
        [
            "По товару",
            "По карточке товара"
        ],
        horizontal=True,
        key="anomaly_mode_radio"
    )

    selected_anomaly_store_product_id = None
    selected_anomaly_store_product_label = None

    if anomaly_mode == "По карточке товара":
        if not filtered_store_products:
            st.info("Для выбранного товара нет карточек в магазинах")
        else:
            anomaly_store_product_map = make_store_product_label_map(
                filtered_store_products,
                stores
            )

            selected_anomaly_store_product_label = st.selectbox(
                "Выберите карточку товара для поиска аномалий",
                list(anomaly_store_product_map.keys()),
                key="anomaly_store_product_select"
            )

            selected_anomaly_store_product_id = anomaly_store_product_map[
                selected_anomaly_store_product_label
            ]

    col1, col2, _ = st.columns([1, 1, 4])

    with col1:
        if st.button("Выявить аномалии", width="stretch"):
            if anomaly_mode == "По товару":
                response = requests.post(
                    f"{API_URL}/anomalies/detect/product/{product_id}"
                )
            else:
                if selected_anomaly_store_product_id is None:
                    st.warning("Выберите карточку товара")
                    response = None
                else:
                    response = requests.post(
                        f"{API_URL}/anomalies/detect/store-product/"
                        f"{selected_anomaly_store_product_id}"
                    )

            if response is not None:
                if response.status_code == 200:
                    anomalies = response.json()
                    set_local_flash_message(
                        "anomaly_detect",
                        f"Анализ завершён. Найдено аномалий: {len(anomalies)}"
                    )
                    st.rerun()
                else:
                    show_api_error(
                        response,
                        "Ошибка при выявлении аномалий"
                    )

    show_local_flash_message("anomaly_detect")

    with col2:
        if st.button("Удалить аномалии", width="stretch"):
            if anomaly_mode == "По товару":
                response = requests.delete(
                    f"{API_URL}/anomalies/product/{product_id}"
                )
            else:
                if selected_anomaly_store_product_id is None:
                    st.warning("Выберите карточку товара")
                    response = None
                else:
                    response = requests.delete(
                        f"{API_URL}/anomalies/store-product/"
                        f"{selected_anomaly_store_product_id}"
                    )

            if response is not None:
                if response.status_code == 200:
                    set_local_flash_message(
                        "anomaly_delete",
                        "Аномалии успешно удалены"
                    )
                    st.rerun()
                else:
                    show_api_error(
                        response,
                        "Ошибка при удалении аномалий"
                    )

    show_local_flash_message("anomaly_delete")

    st.divider()

    prices = get_product_prices(product_id)

    if anomaly_mode == "По товару":
        anomalies = get_product_anomalies(product_id)
    else:
        if selected_anomaly_store_product_id is None:
            anomalies = []
        else:
            anomalies_response = requests.get(
                f"{API_URL}/anomalies/store-product/"
                f"{selected_anomaly_store_product_id}"
            )

            if anomalies_response.status_code == 200:
                anomalies = anomalies_response.json()
            else:
                show_api_error(
                    anomalies_response,
                    "Не удалось получить аномалии по карточке товара"
                )
                anomalies = []

    if not prices:
        st.info("Для выбранного товара отсутствует история цен")
    else:
        prices_df = pd.DataFrame(prices)

        if anomaly_mode == "По карточке товара":
            if selected_anomaly_store_product_id is not None:
                prices_df = prices_df[
                    prices_df["store_product_id"]
                    == selected_anomaly_store_product_id
                ]

        if prices_df.empty:
            st.info("Для выбранной карточки товара отсутствует история цен")
        else:
            prices_df = prepare_price_chart_dataframe(prices_df)

            if anomaly_mode == "По товару":
                chart_title = f"Анализ цен: {selected_product}"
            else:
                chart_title = (
                    f"Анализ цен: {selected_product} — "
                    f"{selected_anomaly_store_product_label}"
                )

            fig = px.line(
                prices_df,
                x="checked_at",
                y="price",
                markers=True,
                title=chart_title,
                labels={
                    "checked_at": "Дата",
                    "price": "Цена"
                }
            )

            if anomalies:
                anomalies_df = pd.DataFrame(anomalies)

                if not anomalies_df.empty:
                    anomalies_df = prepare_price_chart_dataframe(anomalies_df)

                    anomaly_type_map = {
                        "price_outlier": "Нетипичное значение цены",
                        "z_score_outlier": "Статистический выброс",
                        "price_spike": "Резкий рост цены",
                        "price_drop": "Резкое падение цены",
                        "price_fixation": "Длительная фиксация цены",
                        "synchronized_change": "Синхронное изменение цены"
                    }

                    risk_level_map = {
                        "low": "Низкий",
                        "medium": "Средний",
                        "high": "Высокий"
                    }

                    risk_color_map = {
                        "low": "yellow",
                        "medium": "orange",
                        "high": "red"
                    }

                    for risk_level, risk_name in risk_level_map.items():
                        risk_df = anomalies_df[
                            anomalies_df["risk_level"] == risk_level
                        ]

                        if not risk_df.empty:
                            fig.add_scatter(
                                x=risk_df["checked_at"],
                                y=risk_df["price"],
                                mode="markers",
                                name=f"Аномалии: {risk_name} риск",
                                marker={
                                    "size": 13,
                                    "symbol": "x",
                                    "color": risk_color_map[risk_level]
                                }
                            )

                    table_anomalies = anomalies_df.rename(
                        columns={
                            "id": "ID",
                            "price_id": "ID цены",
                            "product_id": "ID товара",
                            "store_product_id": "ID карточки товара",
                            "price": "Цена",
                            "checked_at": "Дата цены",
                            "anomaly_type": "Тип аномалии",
                            "anomaly_score": "Оценка аномальности",
                            "risk_level": "Уровень риска",
                            "detected_at": "Дата выявления"
                        }
                    )

                    table_anomalies["Тип аномалии"] = (
                        table_anomalies["Тип аномалии"]
                        .map(anomaly_type_map)
                        .fillna(table_anomalies["Тип аномалии"])
                    )

                    table_anomalies["Уровень риска"] = (
                        table_anomalies["Уровень риска"]
                        .map(risk_level_map)
                        .fillna(table_anomalies["Уровень риска"])
                    )

                    table_anomalies["Оценка аномальности"] = (
                        table_anomalies["Оценка аномальности"]
                        .round(4)
                    )

                    table_anomalies["Дата цены"] = (
                        table_anomalies["Дата цены"]
                        .dt.strftime("%d.%m.%Y %H:%M")
                    )

                    table_anomalies["Дата выявления"] = pd.to_datetime(
                        table_anomalies["Дата выявления"],
                        format="ISO8601"
                    ).dt.strftime("%d.%m.%Y %H:%M")

                    st.subheader("Выявленные аномалии")

                    anomaly_columns = [
                        "ID",
                        "ID цены",
                        "Цена",
                        "Дата цены",
                        "Тип аномалии",
                        "Оценка аномальности",
                        "Уровень риска",
                        "Дата выявления"
                    ]

                    st.dataframe(
                        table_anomalies[anomaly_columns],
                        width="stretch"
                    )
                else:
                    st.info("Аномалии для выбранной карточки товара отсутствуют")
            else:
                if anomaly_mode == "По товару":
                    st.info("Аномалии для выбранного товара отсутствуют")
                else:
                    st.info("Аномалии для выбранной карточки товара отсутствуют")

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

    st.divider()

    st.subheader("Корреляционный анализ между магазинами")

    col1, col2, _ = st.columns([1, 1, 4])

    with col1:
        if st.button("Выполнить анализ", width="stretch"):
            response = requests.post(
                f"{API_URL}/correlations/analyze/product/{product_id}"
            )

            if response.status_code == 200:
                correlations = response.json()

                if len(correlations) == 0:
                    set_local_flash_message(
                        "correlation_analyze",
                        "Корреляционный анализ выполнен, но результатов нет. Проверьте, что минимум у двух карточек товара есть достаточная история цен за общие даты.",
                        "warning"
                    )
                else:
                    set_local_flash_message(
                        "correlation_analyze",
                        f"Анализ завершён. Получено результатов: {len(correlations)}"
                    )

                st.rerun()
            else:
                show_api_error(
                    response,
                    "Ошибка при выполнении корреляционного анализа"
                )

    show_local_flash_message("correlation_analyze")

    with col2:
        if st.button("Удалить результаты", width="stretch"):
            response = requests.delete(
                f"{API_URL}/correlations/product/{product_id}"
            )

            if response.status_code == 200:
                set_local_flash_message(
                    "correlation_delete",
                    "Результаты корреляционного анализа удалены"
                )
                st.rerun()
            else:
                show_api_error(
                    response,
                    "Ошибка при удалении результатов корреляционного анализа"
                )

    show_local_flash_message("correlation_delete")

    correlations = get_product_correlations(product_id)

    if correlations:
        correlations_df = pd.DataFrame(correlations)

        risk_level_map = {
            "low": "Низкий",
            "medium": "Средний",
            "high": "Высокий"
        }

        correlations_table = correlations_df.rename(
            columns={
                "id": "ID",
                "product_id": "ID товара",
                "first_store_product_id": "ID первой карточки",
                "second_store_product_id": "ID второй карточки",
                "first_store_name": "Первый магазин",
                "second_store_name": "Второй магазин",
                "correlation_value": "Коэффициент корреляции",
                "period_start": "Начало периода",
                "period_end": "Конец периода",
                "risk_level": "Уровень риска",
                "created_at": "Дата анализа"
            }
        )

        correlations_table["Коэффициент корреляции"] = (
            correlations_table["Коэффициент корреляции"].round(4)
        )

        correlations_table["Уровень риска"] = (
            correlations_table["Уровень риска"]
            .map(risk_level_map)
            .fillna(correlations_table["Уровень риска"])
        )

        correlations_table["Начало периода"] = pd.to_datetime(
            correlations_table["Начало периода"],
            format="ISO8601"
        ).dt.strftime("%d.%m.%Y")

        correlations_table["Конец периода"] = pd.to_datetime(
            correlations_table["Конец периода"],
            format="ISO8601"
        ).dt.strftime("%d.%m.%Y")

        correlations_table["Дата анализа"] = pd.to_datetime(
            correlations_table["Дата анализа"],
            format="ISO8601"
        ).dt.strftime("%d.%m.%Y %H:%M")

        st.dataframe(
            correlations_table[
                [
                    "ID",
                    "Первый магазин",
                    "Второй магазин",
                    "Коэффициент корреляции",
                    "Уровень риска",
                    "Начало периода",
                    "Конец периода",
                    "Дата анализа"
                ]
            ],
            width="stretch"
        )

        heatmap_df = correlations_df.copy()

        stores_names = sorted(
            set(heatmap_df["first_store_name"].tolist())
            |
            set(heatmap_df["second_store_name"].tolist())
        )

        matrix = pd.DataFrame(
            1.0,
            index=stores_names,
            columns=stores_names
        )

        for _, row in heatmap_df.iterrows():
            first_store = row["first_store_name"]
            second_store = row["second_store_name"]
            correlation_value = row["correlation_value"]

            matrix.loc[first_store, second_store] = correlation_value
            matrix.loc[second_store, first_store] = correlation_value

        fig_corr = px.imshow(
            matrix,
            text_auto=True,
            title=f"Матрица корреляции цен: {selected_product}",
            labels={
                "x": "Магазин",
                "y": "Магазин",
                "color": "Корреляция"
            },
            zmin=-1,
            zmax=1
        )

        st.plotly_chart(
            fig_corr,
            width="stretch",
            config={
                "displaylogo": False,
                "locale": "ru"
            }
        )

    else:
        st.info("Результаты корреляционного анализа отсутствуют")

    st.divider()

    st.subheader("Прогнозирование цен")

    filtered_store_products = [
        item for item in store_products
        if item["product_id"] == product_id
    ]

    if not filtered_store_products:
        st.info("Для выбранного товара нет карточек в магазинах")
    else:
        store_product_map = make_store_product_label_map(
            filtered_store_products,
            stores
        )

        selected_forecast_store_product = st.selectbox(
            "Выберите карточку товара для прогнозирования",
            list(store_product_map.keys()),
            key="forecast_store_product_select"
        )

        selected_forecast_store_product_id = store_product_map[
            selected_forecast_store_product
        ]

        days_count = st.number_input(
            "Количество дней прогноза",
            min_value=1,
            max_value=30,
            value=7,
            step=1
        )

        col1, col2, _ = st.columns([1, 1, 4])

        with col1:
            if st.button("Сформировать прогноз", width="stretch"):
                response = requests.post(
                    f"{API_URL}/forecasts/generate",
                    json={
                        "store_product_id": selected_forecast_store_product_id,
                        "days_count": int(days_count)
                    }
                )

                if response.status_code == 200:
                    result = response.json()

                    st.session_state[
                        f"forecast_metrics_{selected_forecast_store_product_id}"
                    ] = result["metrics"]

                    forecasts = result["forecasts"]

                    set_local_flash_message(
                        "forecast_generate",
                        f"Прогноз сформирован. Количество точек: {len(forecasts)}"
                    )

                    st.rerun()
                else:
                    show_api_error(
                        response,
                        "Ошибка при формировании прогноза"
                    )

        show_local_flash_message("forecast_generate")

        with col2:
            if st.button("Удалить прогноз", width="stretch"):
                response = requests.delete(
                    f"{API_URL}/forecasts/store-product/"
                    f"{selected_forecast_store_product_id}"
                )

                if response.status_code == 200:
                    set_local_flash_message(
                        "forecast_delete",
                        "Прогноз успешно удалён"
                    )

                    st.rerun()
                else:
                    show_api_error(
                        response,
                        "Ошибка при удалении прогноза"
                    )

        show_local_flash_message("forecast_delete")

        prices_response = requests.get(
            f"{API_URL}/prices/product/{product_id}"
        )

        forecasts = get_store_product_forecasts(
            selected_forecast_store_product_id
        )

        if prices_response.status_code == 200:
            prices = prices_response.json()

            prices = [
                price for price in prices
                if price["store_product_id"]
                == selected_forecast_store_product_id
            ]

            if prices:
                prices_df = pd.DataFrame(prices)

                prices_df = prepare_price_chart_dataframe(prices_df)

                fig_forecast = px.line(
                    prices_df,
                    x="checked_at",
                    y="price",
                    markers=True,
                    title=f"Прогноз цены: {selected_product}",
                    labels={
                        "checked_at": "Дата",
                        "price": "Цена"
                    }
                )

                if forecasts:
                    forecasts_df = pd.DataFrame(forecasts)

                    forecasts_df = prepare_price_chart_dataframe(forecasts_df)

                    fig_forecast.add_scatter(
                        x=forecasts_df["forecast_date"],
                        y=forecasts_df["predicted_price"],
                        mode="lines+markers",
                        name="Прогноз",
                        line={
                            "dash": "dash"
                        }
                    )

                    forecasts_table = forecasts_df.rename(
                        columns={
                            "id": "ID",
                            "product_id": "ID товара",
                            "store_product_id": "ID карточки товара",
                            "forecast_date": "Дата прогноза",
                            "predicted_price": "Прогнозируемая цена",
                            "created_at": "Дата формирования"
                        }
                    )

                    forecasts_table["Дата прогноза"] = (
                        forecasts_table["Дата прогноза"]
                        .dt.strftime("%d.%m.%Y")
                    )

                    forecasts_table["Дата формирования"] = pd.to_datetime(
                        forecasts_table["Дата формирования"],
                        format="ISO8601"
                    ).dt.strftime("%d.%m.%Y %H:%M")

                    forecasts_table["Прогнозируемая цена"] = (
                        pd.to_numeric(
                            forecasts_table["Прогнозируемая цена"],
                            errors="coerce"
                        ).round(2)
                    )

                    st.dataframe(
                        forecasts_table[
                            [
                                "ID",
                                "ID карточки товара",
                                "Дата прогноза",
                                "Прогнозируемая цена",
                                "Дата формирования"
                            ]
                        ],
                        width="stretch"
                    )
                else:
                    st.info("Прогноз для выбранной карточки отсутствует")

                fig_forecast.update_layout(
                    xaxis_title="Дата",
                    yaxis_title="Цена",
                    hovermode="x unified"
                )

                fig_forecast.update_xaxes(
                    tickformat="%d.%m.%Y"
                )

                st.plotly_chart(
                    fig_forecast,
                    width="stretch",
                    config={
                        "displaylogo": False,
                        "locale": "ru"
                    }
                )

                metrics_key = (
                    f"forecast_metrics_{selected_forecast_store_product_id}"
                )

                if metrics_key in st.session_state:
                    metrics = st.session_state[metrics_key]

                    st.subheader("Метрики качества прогнозирования")

                    metric_col1, metric_col2, metric_col3 = st.columns(3)

                    with metric_col1:
                        st.metric(
                            "MAE",
                            round(metrics["mae"], 4)
                        )

                    with metric_col2:
                        st.metric(
                            "RMSE",
                            round(metrics["rmse"], 4)
                        )

                    with metric_col3:
                        st.metric(
                            "MAPE (%)",
                            round(metrics["mape"], 4)
                        )
            else:
                st.info("Для выбранной карточки товара нет истории цен")