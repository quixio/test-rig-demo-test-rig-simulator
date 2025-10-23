import os

SDK_TOKEN = os.getenv("Quix__Sdk__Token", "")
TESTMANAGER_HOST = os.getenv("Testmanager__Host", "0.0.0.0")
TESTMANAGER_PORT = int(os.getenv("Testmanager__Port", "8000"))
TESTMANAGER_TIMEZONE = os.getenv("Testmanager__Timezone", "Europe/London")
TESTMANAGER_LOGLEVEL = os.getenv("Testmanager__Loglevel", "INFO")

def get_api_url() -> str:
    return os.environ.get("Testmanager__Api__Url", "http://localhost:8080")

def get_lake_query_ui_url() -> str:
    url =  os.environ.get("Testmanager__Lake__Query__Ui__Url", "https://query-ui-quixers-testmanagerdemo-dev.az-france-0.app.quix.io")
    if url.endswith("/"):
        return url.removesuffix("/")
    return url

def get_marimo_url() -> str:
    url =  os.environ.get("Testmanager__Marimo__Url", "https://simplemarimo-c42ffa5-quixers-advanceanalyticsdemo-main.az-france-0.app.quix.io")
    if url.endswith("/"):
        return url.removesuffix("/")
    return url

def is_quix_environment() -> bool:
    """Check if running in Quix environment by checking for Quix-specific env vars"""
    return bool(os.environ.get("Quix__Application__Id"))


def is_quix_iframe() -> bool:
    """Check if running in Quix iframe - this needs to be checked at runtime from the page"""
    # This is a placeholder - the actual check needs to happen in the frontend
    # where we have access to the query string
    return False

def get_default_theme() -> str:
    """Get default theme from environment variable"""
    return os.environ.get("Testmanager__Theme", "light").lower()
