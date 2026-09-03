import pytest
from playwright.sync_api import Page, expect

from saucedemo.page_objects import LoginPage, ShopPage


@pytest.mark.parametrize(("username", "password"), [
    ("standard_user", "secret_sauce"),
], ids=["standard-user"])
@pytest.mark.smoke
def test_positive_login(page: Page, username: str, password: str) -> None:
    page.goto("/", wait_until="load")
    login_page = LoginPage(page)

    login_page.login(username, password)

    shop_page = ShopPage(page)
    expect(shop_page.inventory_list).to_be_visible()


@pytest.mark.parametrize(("username", "password", "expected_error"), [
    ("locked_out_user", "secret_sauce", "Epic sadface: Sorry, this user has been locked out."),
], ids=["locked-out-user"])
@pytest.mark.regression
def test_negative_login(
    page: Page,
    username: str,
    password: str,
    expected_error: str,
) -> None:
    page.goto("/", wait_until="load")
    login_page = LoginPage(page)

    login_page.login(username, password)

    expect(login_page.error_message).to_be_visible()
    assert login_page.error_text() == expected_error
