import os
import re
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from time import time

import allure
import pytest
from playwright.sync_api import Browser, BrowserContext, Error, Page, Playwright, sync_playwright

from saucedemo.config import (
    ALLURE_RESULTS_DIR,
    BASE_URL,
    BROWSER,
    DEFAULT_TIMEOUT_MS,
    HEADLESS,
    IGNORE_HTTPS_ERRORS,
    LOCALE,
    NAVIGATION_TIMEOUT_MS,
    PLAYWRIGHT_TEST_ID_ATTRIBUTE,
    SAUCEDEMO_COOKIE_DOMAIN,
    SAUCEDEMO_SESSION_COOKIE_NAME,
    SAUCEDEMO_SESSION_COOKIE_TTL_SECONDS,
    TEST_RUNS_DIR,
    TIMEZONE_ID,
    VIEWPORT_HEIGHT,
    VIEWPORT_WIDTH,
)


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    if config.option.allure_report_dir is None:
        config.option.allure_report_dir = str(ALLURE_RESULTS_DIR)


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("playwright-framework")
    group.addoption(
        "--browser",
        choices=("chrome", "chromium", "firefox"),
        default=None,
        help="Override BROWSER from .env.",
    )
    group.addoption("--headed", action="store_true", help="Run with a visible browser window.")
    group.addoption("--timeout-ms", type=int, default=None, help="Override DEFAULT_TIMEOUT_MS from .env.")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[object]) -> Iterator[None]:
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)
    if report.failed and report.when in {"setup", "call"}:
        _capture_failure_artifacts(item)


@pytest.fixture(scope="session")
def browser_name(pytestconfig: pytest.Config) -> str:
    return pytestconfig.getoption("--browser") or BROWSER


@pytest.fixture(scope="session")
def test_run_dir(browser_name: str) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S_%fZ")
    directory = TEST_RUNS_DIR / f"{timestamp}_{browser_name}_{os.getpid()}"
    directory.mkdir(parents=True, exist_ok=False)
    return directory


@pytest.fixture
def artifact_dir(request: pytest.FixtureRequest, test_run_dir: Path) -> Path:
    directory = test_run_dir / _safe_node_id(request.node.nodeid)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


@pytest.fixture(scope="session")
def playwright_instance() -> Iterator[Playwright]:
    with sync_playwright() as playwright:
        if PLAYWRIGHT_TEST_ID_ATTRIBUTE:
            playwright.selectors.set_test_id_attribute(
                PLAYWRIGHT_TEST_ID_ATTRIBUTE
            )
        yield playwright


@pytest.fixture
def sauce_user(request: pytest.FixtureRequest) -> str:
    return request.param


@pytest.fixture
def auth_page(page: Page, sauce_user: str) -> Page:
    """Add a temporary SauceDemo session cookie to a new page."""
    page.context.add_cookies(
        [{
            "name": SAUCEDEMO_SESSION_COOKIE_NAME,
            "value": sauce_user,
            "domain": SAUCEDEMO_COOKIE_DOMAIN,
            "path": "/",
            "expires": int(time()) + SAUCEDEMO_SESSION_COOKIE_TTL_SECONDS,
            "secure": True,
            "sameSite": "Lax",
        }]
    )
    return page


@pytest.fixture(scope="session")
def browser(
    playwright_instance: Playwright,
    pytestconfig: pytest.Config,
    browser_name: str,
) -> Iterator[Browser]:
    launch_options = {
        "headless": False if pytestconfig.getoption("--headed") else HEADLESS,
    }

    if browser_name == "firefox":
        instance = playwright_instance.firefox.launch(**launch_options)
    elif browser_name == "chrome":
        instance = playwright_instance.chromium.launch(channel="chrome", **launch_options)
    else:
        instance = playwright_instance.chromium.launch(**launch_options)

    yield instance
    instance.close()


@pytest.fixture
def context(
    request: pytest.FixtureRequest,
    browser: Browser,
    artifact_dir: Path,
) -> Iterator[BrowserContext]:
    context_options: dict[str, object] = {
        "ignore_https_errors": IGNORE_HTTPS_ERRORS,
        "locale": LOCALE,
        "timezone_id": TIMEZONE_ID,
        "viewport": {"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
    }
    if BASE_URL:
        context_options["base_url"] = BASE_URL

    browser_context = browser.new_context(**context_options)
    browser_context.tracing.start(screenshots=True, snapshots=True, sources=True)

    yield browser_context

    failed = _test_failed(request.node)
    try:
        if failed and not getattr(request.node, "_failure_artifacts_captured", False):
            _capture_pages(browser_context, artifact_dir)
        _stop_trace(browser_context, artifact_dir if failed else None)
    finally:
        browser_context.close()


@pytest.fixture
def page(
    request: pytest.FixtureRequest,
    context: BrowserContext,
    pytestconfig: pytest.Config,
    browser_name: str,
    artifact_dir: Path,
) -> Iterator[Page]:
    browser_page = context.new_page()
    configured_timeout = pytestconfig.getoption("--timeout-ms")
    browser_page.set_default_timeout(DEFAULT_TIMEOUT_MS if configured_timeout is None else configured_timeout)
    browser_page.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)

    browser_logs: list[str] = []
    setattr(request.node, "_browser_logs", browser_logs)
    browser_page.on("console", lambda message: browser_logs.append(f"console.{message.type}: {message.text}"))
    browser_page.on("pageerror", lambda error: browser_logs.append(f"pageerror: {error}"))

    allure.dynamic.parameter("browser", browser_name)
    yield browser_page

    if _test_failed(request.node) and browser_logs:
        if not getattr(request.node, "_failure_artifacts_captured", False):
            _capture_browser_logs(browser_logs, artifact_dir)


def _capture_failure_artifacts(item: pytest.Item) -> None:
    context = item.funcargs.get("context")
    artifact_dir = item.funcargs.get("artifact_dir")
    if not isinstance(context, BrowserContext) or not isinstance(artifact_dir, Path):
        return

    _capture_pages(context, artifact_dir)
    browser_logs = getattr(item, "_browser_logs", [])
    if browser_logs:
        _capture_browser_logs(browser_logs, artifact_dir)
    setattr(item, "_failure_artifacts_captured", True)


def _capture_browser_logs(browser_logs: list[str], artifact_dir: Path) -> None:
    log_path = artifact_dir / "browser.log"
    log_path.write_text("\n".join(browser_logs) + "\n", encoding="utf-8")
    allure.attach.file(
        str(log_path),
        name="Browser console",
        attachment_type=allure.attachment_type.TEXT,
    )


def _capture_pages(context: BrowserContext, artifact_dir: Path) -> None:
    for index, opened_page in enumerate(context.pages, start=1):
        try:
            screenshot_path = artifact_dir / f"page-{index}.png"
            opened_page.screenshot(path=str(screenshot_path), full_page=True)
            allure.attach.file(
                str(screenshot_path),
                name=f"Failure screenshot {index}",
                attachment_type=allure.attachment_type.PNG,
            )
        except Error as error:
            allure.attach(str(error), name=f"Screenshot error {index}", attachment_type=allure.attachment_type.TEXT)

        try:
            html_path = artifact_dir / f"page-{index}.html"
            html_path.write_text(opened_page.content(), encoding="utf-8")
            allure.attach.file(
                str(html_path),
                name=f"Page HTML {index}",
                attachment_type=allure.attachment_type.HTML,
            )
        except Error as error:
            allure.attach(str(error), name=f"HTML capture error {index}", attachment_type=allure.attachment_type.TEXT)


def _stop_trace(context: BrowserContext, artifact_dir: Path | None) -> None:
    try:
        if artifact_dir is None:
            context.tracing.stop()
            return
        trace_path = artifact_dir / "trace.zip"
        context.tracing.stop(path=str(trace_path))
        allure.attach.file(
            str(trace_path),
            name="Playwright trace",
            attachment_type="application/zip",
            extension="zip",
        )
    except Error as error:
        allure.attach(str(error), name="Trace capture error", attachment_type=allure.attachment_type.TEXT)


def _test_failed(item: pytest.Item) -> bool:
    setup_report = getattr(item, "rep_setup", None)
    call_report = getattr(item, "rep_call", None)
    return bool((setup_report and setup_report.failed) or (call_report and call_report.failed))


def _safe_node_id(nodeid: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", nodeid).strip("_")
