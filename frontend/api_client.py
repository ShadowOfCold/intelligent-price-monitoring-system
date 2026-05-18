import os

import requests
from dotenv import load_dotenv

load_dotenv()
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = os.getenv("API_PORT", "8000")
API_URL = f"http://{API_HOST}:{API_PORT}"


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


def get_product_prices(product_id: int):
    response = requests.get(f"{API_URL}/prices/product/{product_id}")
    if response.status_code == 200:
        return response.json()
    return []


def get_product_anomalies(product_id: int):
    response = requests.get(f"{API_URL}/anomalies/product/{product_id}")
    if response.status_code == 200:
        return response.json()
    return []


def get_product_correlations(product_id: int):
    response = requests.get(f"{API_URL}/correlations/product/{product_id}")
    if response.status_code == 200:
        return response.json()
    return []


def get_store_product_forecasts(store_product_id: int):
    response = requests.get(
        f"{API_URL}/forecasts/store-product/{store_product_id}"
    )

    if response.status_code == 200:
        return response.json()

    return []


def get_reports():
    response = requests.get(f"{API_URL}/reports/")
    if response.status_code == 200:
        return response.json()
    return []


def download_report(report_id: int):
    return requests.get(f"{API_URL}/reports/download/{report_id}")
