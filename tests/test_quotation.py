import pytest

from src.tools.product_tool import load_products_from_csv
from src.tools.quotation_tool import build_quotation


@pytest.fixture(scope="module", autouse=True)
def setup_products():
    """
    Load the product catalogue before quotation tests.
    """
    load_products_from_csv()


def test_single_product_quotation():
    result = build_quotation([
        {
            "product_id": "P001",
            "quantity": 2,
        }
    ])

    assert result["status"] == "READY"
    assert result["subtotal"] == 17000
    assert result["delivery_fee"] == 2500
    assert result["total"] == 19500


def test_multiple_product_quotation():
    result = build_quotation([
        {
            "product_id": "P001",
            "quantity": 2,
        },
        {
            "product_id": "P002",
            "quantity": 1,
        },
    ])

    assert result["status"] == "READY"
    assert result["subtotal"] == 32000
    assert result["delivery_fee"] == 2500
    assert result["total"] == 34500


def test_custom_delivery_fee():
    result = build_quotation(
        [
            {
                "product_id": "P001",
                "quantity": 2,
            }
        ],
        delivery_fee=1000,
    )

    assert result["status"] == "READY"
    assert result["subtotal"] == 17000
    assert result["delivery_fee"] == 1000
    assert result["total"] == 18000


def test_quotation_line_items():
    result = build_quotation([
        {
            "product_id": "P001",
            "quantity": 2,
        },
        {
            "product_id": "P002",
            "quantity": 1,
        },
    ])

    assert result["status"] == "READY"
    assert len(result["items"]) == 2

    first_item = result["items"][0]

    assert first_item["product_id"] == "P001"
    assert first_item["product_name"] == "Office Chair"
    assert first_item["quantity"] == 2
    assert first_item["unit_price"] == 8500
    assert first_item["line_total"] == 17000
    assert first_item["currency"] == "KES"


def test_unknown_product():
    result = build_quotation([
        {
            "product_id": "P999",
            "quantity": 1,
        }
    ])

    assert result["status"] == "ERROR"
    assert "P999" in result["message"]
    assert "not found" in result["message"].lower()


def test_insufficient_stock():
    result = build_quotation([
        {
            "product_id": "P001",
            "quantity": 1000,
        }
    ])

    assert result["status"] == "ERROR"
    assert "Insufficient stock" in result["message"]
    assert "1000" in result["message"]
    assert "50" in result["message"]


def test_zero_quantity():
    result = build_quotation([
        {
            "product_id": "P001",
            "quantity": 0,
        }
    ])

    assert result["status"] == "ERROR"
    assert "greater than zero" in result["message"]


def test_negative_quantity():
    result = build_quotation([
        {
            "product_id": "P001",
            "quantity": -2,
        }
    ])

    assert result["status"] == "ERROR"
    assert "greater than zero" in result["message"]