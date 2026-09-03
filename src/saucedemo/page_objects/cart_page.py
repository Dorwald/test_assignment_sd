from playwright.sync_api import Page

from saucedemo.utils import CartStorage


class CartPage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.storage = CartStorage(page)
        self.cart_contents_container = page.get_by_test_id("cart-contents-container")
        self.cart_list = self.cart_contents_container.get_by_test_id("cart-list")
        self.cart_items = self.cart_list.get_by_test_id("inventory-item")
        self.item_name_elements = self.cart_items.get_by_test_id("inventory-item-name")
        self.cart_link = page.get_by_test_id("shopping-cart-link")
        self.cart_badge = page.get_by_test_id("shopping-cart-badge")

    def item_names(self) -> list[str]:
        return self.item_name_elements.all_inner_texts()

    def cart_count(self) -> int:
        if self.cart_badge.count() == 0:
            return 0
        return int(self.cart_badge.inner_text())

    def cart_contents_raw(self) -> str | None:
        return self.storage.contents_raw()

    def cart_contents(self) -> list[int] | None:
        return self.storage.contents()
