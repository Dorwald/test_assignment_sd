from pathlib import Path

from environs import Env

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
ALLURE_RESULTS_DIR = OUTPUTS_DIR / "allure-results"
TEST_RUNS_DIR = OUTPUTS_DIR / "test-runs"

env = Env()
env.read_env(PROJECT_ROOT / ".env", recurse=False)

BASE_URL = env.str("BASE_URL", "").strip()
BROWSER = env.str("BROWSER", "chrome").strip().lower()
HEADLESS = env.bool("HEADLESS", True)

DEFAULT_TIMEOUT_MS = env.int("DEFAULT_TIMEOUT_MS", 10_000)
NAVIGATION_TIMEOUT_MS = env.int("NAVIGATION_TIMEOUT_MS", 15_000)

VIEWPORT_WIDTH = env.int("VIEWPORT_WIDTH", 1920)
VIEWPORT_HEIGHT = env.int("VIEWPORT_HEIGHT", 1080)

IGNORE_HTTPS_ERRORS = env.bool("IGNORE_HTTPS_ERRORS", False)
LOCALE = env.str("LOCALE", "en-US").strip()
TIMEZONE_ID = env.str("TIMEZONE_ID", "Europe/Belgrade").strip()
PLAYWRIGHT_TEST_ID_ATTRIBUTE = env.str(
    "PLAYWRIGHT_TEST_ID_ATTRIBUTE", ""
).strip()
SAUCEDEMO_SESSION_COOKIE_NAME = env.str(
    "SAUCEDEMO_SESSION_COOKIE_NAME", "session-username"
).strip()
SAUCEDEMO_COOKIE_DOMAIN = env.str(
    "SAUCEDEMO_COOKIE_DOMAIN", "www.saucedemo.com"
).strip()
SAUCEDEMO_SESSION_COOKIE_TTL_SECONDS = env.int(
    "SAUCEDEMO_SESSION_COOKIE_TTL_SECONDS", 7200
)
