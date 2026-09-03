import pytest
from playwright.sync_api import Page, expect

from saucedemo.page_objects import CartPage, ShopPage
from saucedemo.utils import CartStorage


@pytest.mark.parametrize(
    "sauce_user", ["standard_user"], indirect=True, ids=["standard-user"]
)
@pytest.mark.parametrize("product_count", [1, 2], ids=["first-item", "first-two-items"])
@pytest.mark.smoke
def test_selected_products_are_added_to_cart(
    auth_page: Page,
    product_count: int,
) -> None:
    auth_page.goto("/inventory.html", wait_until="domcontentloaded")
    shop_page = ShopPage(auth_page)

    expect(shop_page.inventory_list).to_be_visible()
    available_product_names = shop_page.product_names()
    assert len(available_product_names) >= product_count
    selected_product_names = available_product_names[:product_count]
    for product_name in selected_product_names:
        shop_page.add_product_to_cart(product_name)

    assert shop_page.cart_count() == product_count

    cart_page = shop_page.open_cart()
    expect(cart_page.cart_list).to_be_visible()

    stored_cart_contents = cart_page.cart_contents()
    assert stored_cart_contents is not None
    assert len(stored_cart_contents) == product_count
    assert cart_page.cart_count() == product_count
    assert sorted(cart_page.item_names()) == sorted(selected_product_names)


@pytest.mark.parametrize(
    "sauce_user", ["standard_user"], indirect=True, ids=["standard-user"]
)
@pytest.mark.parametrize(
    "expected_cart_items",
    [{0: "Sauce Labs Bike Light", 1: "Sauce Labs Bolt T-Shirt"}],
    ids=["bike-light-and-bolt-shirt"],
)
@pytest.mark.regression
def test_cart_renders_products_preloaded_in_local_storage(
    auth_page: Page,
    expected_cart_items: dict[int, str],
) -> None:
    cart_item_ids = list(expected_cart_items)
    expected_product_names = list(expected_cart_items.values())
    auth_page.goto("/inventory.html", wait_until="domcontentloaded")
    CartStorage(auth_page).set_item_ids(cart_item_ids)

    auth_page.goto("/cart.html", wait_until="domcontentloaded")
    cart_page = CartPage(auth_page)

    expect(cart_page.cart_list).to_be_visible()
    assert cart_page.cart_count() == len(expected_product_names)
    assert cart_page.item_names() == expected_product_names
