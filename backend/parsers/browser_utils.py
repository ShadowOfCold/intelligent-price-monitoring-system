from pathlib import Path
from shutil import which

from selenium.webdriver.chrome.options import Options


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/118.0.5993.90 Safari/537.36"
)


def find_chrome_binary() -> str:
    possible_paths = [
        which("google-chrome"),
        "/usr/bin/google-chrome",
        which("google-chrome-stable"),
        "/usr/bin/google-chrome-stable",
    ]

    for path in possible_paths:
        if path and Path(path).exists():
            return path

    raise RuntimeError("Не найден браузер Google Chrome")


def get_chrome_options() -> Options:
    options = Options()

    options.binary_location = find_chrome_binary()

    options.add_argument(f"--user-agent={USER_AGENT}")
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    return options