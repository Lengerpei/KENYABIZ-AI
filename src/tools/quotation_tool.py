from pathlib import Path
import os

from dotenv import load_dotenv

from src.tools.product_tool import get_product


# Load environment variables
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


DEFAULT_DELIVERY_FEE = float(
    os.getenv("DEFAULT_DELIVERY_FEE", "2500")
)

CURRENCY = os.getenv("CURRENCY", "KES")


def build_quotation(items, delivery_fee=None):
    """
    Build a quotation for a list of products.

    Expected input:

    items = [
        {"product_id": "P001", "quantity": 5},
        {"product_id": "P002", "quantity": 2}
    ]

    Returns a structured quotation containing:
    - product details
    - quantities
    - line totals
    - subtotal
    - delivery fee
    - total
    """

    if not items:
        return {
            "status": "ERROR",
            "message": "No items were provided."
        }

    if delivery_fee is None:
        delivery_fee = DEFAULT_DELIVERY_FEE

    quotation_items = []
    subtotal = 0.0

    for item in items:

        product_id = item.get("product_id")
        quantity = item.get("quantity")

        # Validate product ID
        if not product_id:
            return {
                "status": "ERROR",
                "message": "A product_id is required for every item."
            }

        # Validate quantity
        if quantity is None:
            return {
                "status": "ERROR",
                "message": f"Quantity is required for product {product_id}."
            }

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return {
                "status": "ERROR",
                "message": (
                    f"Invalid quantity for product {product_id}. "
                    "Quantity must be a whole number."
                )
            }

        if quantity <= 0:
            return {
                "status": "ERROR",
                "message": (
                    f"Quantity for product {product_id} "
                    "must be greater than zero."
                )
            }

        # Get product from database
        product = get_product(product_id)

        if product is None:
            return {
                "status": "ERROR",
                "message": f"Product {product_id} was not found."
            }

        # Check stock
        available_stock = product["stock_quantity"]

        if quantity > available_stock:
            return {
                "status": "ERROR",
                "message": (
                    f"Insufficient stock for {product['product_name']}. "
                    f"Requested: {quantity}, "
                    f"Available: {available_stock}."
                )
            }

        # Calculate line total
        unit_price = float(product["price_kes"])
        line_total = unit_price * quantity

        quotation_items.append(
            {
                "product_id": product["product_id"],
                "product_name": product["product_name"],
                "quantity": quantity,
                "unit_price": unit_price,
                "line_total": line_total,
                "currency": CURRENCY
            }
        )

        subtotal += line_total

    # Calculate final total
    delivery_fee = float(delivery_fee)
    total = subtotal + delivery_fee

    return {
        "status": "READY",
        "currency": CURRENCY,
        "items": quotation_items,
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "total": total
    }


def format_quotation(quotation):
    """
    Convert a quotation dictionary into a human-readable quotation.
    """

    if quotation.get("status") != "READY":
        return quotation.get("message", "Unable to create quotation.")

    lines = []

    lines.append("=" * 60)
    lines.append("KENYABIZ AI - QUOTATION")
    lines.append("=" * 60)

    for item in quotation["items"]:
        lines.append(
            f"{item['product_name']} "
            f"x {item['quantity']} "
            f"@ {quotation['currency']} "
            f"{item['unit_price']:,.2f} "
            f"= {quotation['currency']} "
            f"{item['line_total']:,.2f}"
        )

    lines.append("-" * 60)

    lines.append(
        f"Subtotal:       {quotation['currency']} "
        f"{quotation['subtotal']:,.2f}"
    )

    lines.append(
        f"Delivery Fee:   {quotation['currency']} "
        f"{quotation['delivery_fee']:,.2f}"
    )

    lines.append(
        f"TOTAL:          {quotation['currency']} "
        f"{quotation['total']:,.2f}"
    )

    lines.append("=" * 60)

    return "\n".join(lines)


if __name__ == "__main__":

    print("=" * 60)
    print("KENYABIZ AI")
    print("Quotation Calculator Test")
    print("=" * 60)

    test_items = [
        {
            "product_id": "P001",
            "quantity": 5
        },
        {
            "product_id": "P002",
            "quantity": 2
        }
    ]

    quotation = build_quotation(test_items)

    print()
    print("Quotation result:")
    print(quotation)

    print()
    print("Formatted quotation:")
    print()

    print(format_quotation(quotation))