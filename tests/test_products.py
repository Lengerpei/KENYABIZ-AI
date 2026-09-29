import pytest

from src.tools.product_tool import (
    load_products_from_csv,
    get_product,
    search_products,
    check_stock,
    get_products_by_category,
)


@pytest.fixture(scope="module", autouse=True)
def setup_products():
    """
    Load the products from data/products.csv
    into the SQLite database before running tests.
    """
    load_products_from_csv()


def test_get_existing_product():
    product = get_product("P001")

    assert product is not None
    assert product["product_id"] == "P001"
    assert product["product_name"] == "Office Chair"
    assert product["price_kes"] == 8500


def test_get_nonexistent_product():
    product = get_product("P999")

    assert product is None


def test_search_products():
    products = search_products("chair")

    assert len(products) >= 2

    product_names = [
        product["product_name"]
        for product in products
    ]

    assert "Office Chair" in product_names
    assert "Visitor Chair" in product_names


def test_check_stock_available():
    result = check_stock("P001", 5)

    assert result["available"] is True
    assert result["requested_quantity"] == 5
    assert result["available_quantity"] >= 5


def test_check_stock_insufficient():
    result = check_stock("P001", 1000)

    assert result["available"] is False
    assert result["available_quantity"] == 50


def test_check_stock_unknown_product():
    result = check_stock("P999", 5)

    assert result["available"] is False
    assert "not found" in result["message"].lower()


def test_products_by_category():
    products = get_products_by_category("Furniture")

    assert len(products) > 0

    for product in products:
        assert product["category"] == "Furniture"


def test_all_expected_products_exist():
    expected_ids = [
        "P001",
        "P002",
        "P003",
        "P004",
        "P005",
        "P006",
        "P007",
        "P008",
        "P009",
        "P010",
    ]

    for product_id in expected_ids:
        product = get_product(product_id)
        assert product is not None