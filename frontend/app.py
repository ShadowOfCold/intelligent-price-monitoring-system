import plotly.io as pio
import streamlit as st

from modules.analytics_module import render_analytics_module
from modules.documents_module import render_documents_module
from modules.price_collection_module import render_price_collection_module
from modules.price_history_module import render_price_history_module
from modules.products_module import render_products_module
from modules.reports_module import render_reports_module
from modules.scheduler_module import render_scheduler_module
from modules.store_products_module import render_store_products_module
from modules.stores_module import render_stores_module


st.set_page_config(
    page_title="Система мониторинга цен",
    layout="wide"
)

pio.templates.default = "plotly_white"

st.title("Интеллектуальная система мониторинга цен")

tabs = st.tabs([
    "Товары",
    "Магазины",
    "Карточки товаров",
    "Сбор цен",
    "Документы закупки",
    "История цен",
    "Аналитика",
    "Отчёты",
    "Автоматизация"
])

with tabs[0]:
    render_products_module()

with tabs[1]:
    render_stores_module()

with tabs[2]:
    render_store_products_module()

with tabs[3]:
    render_price_collection_module()

with tabs[4]:
    render_documents_module()

with tabs[5]:
    render_price_history_module()

with tabs[6]:
    render_analytics_module()

with tabs[7]:
    render_reports_module()

with tabs[8]:
    render_scheduler_module()
