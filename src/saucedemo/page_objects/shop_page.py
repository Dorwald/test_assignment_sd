from playwright.sync_api import Locator, Page

from saucedemo.page_objects.cart_page import CartPage


class ShopPage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.inventory_list = page.get_by_test_id("inventory-list")
        self.inventory_items = self.inventory_list.get_by_test_id("inventory-item")
        self.product_name_elements = self.inventory_items.get_by_test_id(
            "inventory-item-name"
        )
        self.cart_link = page.get_by_test_id("shopping-cart-link")
        self.cart_badge = page.get_by_test_id("shopping-cart-badge")

    def product_names(self) -> list[str]:
        return self.product_name_elements.all_inner_texts()

    def add_product_to_cart(self, product_name: str) -> None:
        self.product_card(product_name).get_by_role(
            "button", name="Add to cart", exact=True
        ).click()

    def product_card(self, product_name: str) -> Locator:
        return self.inventory_items.filter(
            has=self.page.get_by_text(product_name, exact=True)
        )

    def cart_count(self) -> int:
        if self.cart_badge.count() == 0:
            return 0
        return int(self.cart_badge.inner_text())

    def open_cart(self) -> CartPage:
        self.cart_link.click()
        return CartPage(self.page)
