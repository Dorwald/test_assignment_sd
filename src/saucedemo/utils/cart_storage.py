import json

from playwright.sync_api import Page


class CartStorage:
    """Access SauceDemo cart state in LocalStorage.

    The page must be open on the SauceDemo domain.
    """

    CART_CONTENTS_KEY = "cart-contents"

    def __init__(self, page: Page) -> None:
        self.page = page

    def contents_raw(self) -> str | None:
        return self.page.evaluate(
            "key => window.localStorage.getItem(key)", self.CART_CONTENTS_KEY
        )

    def contents(self) -> list[int] | None:
        """Return cart product IDs after validating JSON data."""
        raw_contents = self.contents_raw()
        if raw_contents is None:
            return None

        item_ids = json.loads(raw_contents)
        if not isinstance(item_ids, list) or any(
            type(item_id) is not int for item_id in item_ids
        ):
            raise ValueError(
                f"{self.CART_CONTENTS_KEY!r} must contain a JSON list of product IDs"
            )
        return item_ids

    def set_item_ids(self, item_ids: list[int]) -> None:
        if any(type(item_id) is not int for item_id in item_ids):
            raise ValueError("Cart product IDs must be integers")
        self.page.evaluate(
            """({ key, itemIds }) => window.localStorage.setItem(
                key, JSON.stringify(itemIds)
            )""",
            {"key": self.CART_CONTENTS_KEY, "itemIds": item_ids},
        )
