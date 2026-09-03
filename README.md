# SauceDemo UI tests

UI tests for SauceDemo. The project uses Python, pytest, Playwright and Poetry.

## Setup

You need Python 3.13 and Poetry.

Windows PowerShell:

```powershell
Copy-Item .env_example .env
poetry install --with test
poetry run playwright install chrome firefox
```

Linux:

```bash
cp .env_example .env
poetry install --with test
poetry run playwright install --with-deps chrome firefox
```

The default `.env` values are ready for SauceDemo. Keep this value for page
objects that use `get_by_test_id`:

```env
PLAYWRIGHT_TEST_ID_ATTRIBUTE=data-test
```

## Run tests

```console
poetry run pytest
poetry run pytest -m smoke
poetry run pytest -m regression
poetry run pytest tests/saucedemo
poetry run pytest --browser firefox
poetry run pytest --headed
```

Login tests use the login form. Shop and cart tests use `auth_page`, which adds
a short-lived `session-username` cookie. The test user is set in test
parametrization.

## Project structure

```text
src/saucedemo/
  config.py
  page_objects/
  utils/cart_storage.py
tests/saucedemo/
  conftest.py
  test_login.py
  test_shop_and_cart.py
```

`CartStorage` reads and writes the `cart-contents` value in LocalStorage.

## Docker

Docker Compose reads values from `.env` when the file exists.

```console
docker compose build
docker compose run --rm tests-chrome
docker compose run --rm tests-firefox
```

## Allure report

Test results are saved in `outputs/allure-results`. On a failed test, the
framework also saves a screenshot, page HTML, browser log and Playwright trace.

With the Allure CLI installed, create the report with:

```console
allure generate outputs/allure-results --output outputs/allure-report --clean
allure open outputs/allure-report
```

## Notes

- The page objects include only elements used in the current tests. Other page
  elements are not covered to save time.
- This is a test website. A user is changed with a cookie, and the cart is kept
  in the browser. In a real product, the cart should be cleared when the user
  changes.
- The tests use only a small set of users. New users are easy to add through
  parametrization. Users with visual or other special cases are not covered.
