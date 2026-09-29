from pathlib import Path
from datetime import datetime
import random
import string

from src.database.database import get_connection, initialize_database
from src.tools.product_tool import get_product
from src.tools.quotation_tool import build_quotation


def generate_order_reference():
    """
    Generate a unique customer-friendly order reference.

    Example:
    KBA-20260925-A7F3
    """

    date_part = datetime.now().strftime("%Y%m%d")

    random_part = "".join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=4
        )
    )

    return f"KBA-{date_part}-{random_part}"


def create_customer(name, phone=None, email=None):
    """
    Create a customer record and return the customer ID.
    """

    if not name or not name.strip():
        raise ValueError("Customer name is required.")

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO customers (name, phone, email)
            VALUES (?, ?, ?)
            """,
            (
                name.strip(),
                phone,
                email
            )
        )

        customer_id = cursor.lastrowid

        connection.commit()

        return customer_id

    finally:
        connection.close()


def create_order(
    customer_name,
    items,
    phone=None,
    email=None,
    delivery_fee=None
):
    """
    Create a complete customer order.

    The quotation tool is used first to validate the products,
    quantities, stock and calculate the totals.

    Example:

    items = [
        {"product_id": "P001", "quantity": 2},
        {"product_id": "P002", "quantity": 1}
    ]
    """

    # ---------------------------------------------------------
    # STEP 1: Validate customer
    # ---------------------------------------------------------

    if not customer_name or not customer_name.strip():
        return {
            "status": "ERROR",
            "message": "Customer name is required."
        }

    # ---------------------------------------------------------
    # STEP 2: Build quotation
    # ---------------------------------------------------------

    quotation = build_quotation(
        items,
        delivery_fee=delivery_fee
    )

    if quotation["status"] != "READY":
        return {
            "status": "ERROR",
            "message": quotation["message"]
        }

    # ---------------------------------------------------------
    # STEP 3: Create database connection
    # ---------------------------------------------------------

    connection = get_connection()

    try:

        cursor = connection.cursor()

        # -----------------------------------------------------
        # STEP 4: Create customer
        # -----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO customers (name, phone, email)
            VALUES (?, ?, ?)
            """,
            (
                customer_name.strip(),
                phone,
                email
            )
        )

        customer_id = cursor.lastrowid

        # -----------------------------------------------------
        # STEP 5: Generate order reference
        # -----------------------------------------------------

        order_reference = generate_order_reference()

        # -----------------------------------------------------
        # STEP 6: Create order
        # -----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO orders (
                order_reference,
                customer_id,
                subtotal,
                delivery_fee,
                total,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                order_reference,
                customer_id,
                quotation["subtotal"],
                quotation["delivery_fee"],
                quotation["total"],
                "PENDING"
            )
        )

        order_id = cursor.lastrowid

        # -----------------------------------------------------
        # STEP 7: Add order items
        # -----------------------------------------------------

        for item in quotation["items"]:

            cursor.execute(
                """
                INSERT INTO order_items (
                    order_id,
                    product_id,
                    product_name,
                    quantity,
                    unit_price,
                    total_price
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    item["product_id"],
                    item["product_name"],
                    item["quantity"],
                    item["unit_price"],
                    item["line_total"]
                )
            )

        # -----------------------------------------------------
        # STEP 8: Commit transaction
        # -----------------------------------------------------

        connection.commit()

        # -----------------------------------------------------
        # STEP 9: Return order information
        # -----------------------------------------------------

        return {
            "status": "SUCCESS",
            "order_id": order_id,
            "order_reference": order_reference,
            "customer_id": customer_id,
            "customer_name": customer_name.strip(),
            "items": quotation["items"],
            "subtotal": quotation["subtotal"],
            "delivery_fee": quotation["delivery_fee"],
            "total": quotation["total"],
            "currency": quotation["currency"],
            "order_status": "PENDING"
        }

    except Exception as error:

        connection.rollback()

        return {
            "status": "ERROR",
            "message": f"Unable to create order: {error}"
        }

    finally:

        connection.close()


def get_order(order_reference):
    """
    Retrieve an order using its order reference.
    """

    connection = get_connection()

    try:

        cursor = connection.cursor()

        # Get order
        cursor.execute(
            """
            SELECT
                o.order_id,
                o.order_reference,
                o.customer_id,
                c.name AS customer_name,
                c.phone,
                c.email,
                o.subtotal,
                o.delivery_fee,
                o.total,
                o.status,
                o.created_at
            FROM orders o
            JOIN customers c
                ON o.customer_id = c.customer_id
            WHERE o.order_reference = ?
            """,
            (order_reference,)
        )

        order = cursor.fetchone()

        if order is None:
            return None

        order = dict(order)

        # Get order items
        cursor.execute(
            """
            SELECT
                product_id,
                product_name,
                quantity,
                unit_price,
                total_price
            FROM order_items
            WHERE order_id = ?
            """,
            (order["order_id"],)
        )

        order["items"] = [
            dict(item)
            for item in cursor.fetchall()
        ]

        return order

    finally:

        connection.close()


def update_order_status(order_reference, new_status):
    """
    Update the status of an order.

    Possible statuses for our prototype:

    PENDING
    CONFIRMED
    PAID
    PROCESSING
    DELIVERED
    CANCELLED
    """

    allowed_statuses = {
        "PENDING",
        "CONFIRMED",
        "PAID",
        "PROCESSING",
        "DELIVERED",
        "CANCELLED"
    }

    new_status = new_status.upper()

    if new_status not in allowed_statuses:

        return {
            "status": "ERROR",
            "message": (
                f"Invalid order status: {new_status}. "
                f"Allowed statuses: {', '.join(sorted(allowed_statuses))}"
            )
        }

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE orders
            SET status = ?
            WHERE order_reference = ?
            """,
            (
                new_status,
                order_reference
            )
        )

        if cursor.rowcount == 0:

            return {
                "status": "ERROR",
                "message": (
                    f"Order {order_reference} was not found."
                )
            }

        connection.commit()

        return {
            "status": "SUCCESS",
            "order_reference": order_reference,
            "new_status": new_status
        }

    finally:

        connection.close()


def format_order(order):
    """
    Convert an order dictionary into a readable format.
    """

    if order is None:
        return "Order not found."

    lines = []

    lines.append("=" * 60)
    lines.append("KENYABIZ AI - ORDER")
    lines.append("=" * 60)

    lines.append(
        f"Order Reference: {order['order_reference']}"
    )

    lines.append(
        f"Customer: {order['customer_name']}"
    )

    if order.get("phone"):
        lines.append(
            f"Phone: {order['phone']}"
        )

    lines.append(
        f"Status: {order['status']}"
    )

    lines.append("-" * 60)

    for item in order["items"]:

        lines.append(
            f"{item['product_name']} "
            f"x {item['quantity']} "
            f"@ KES {item['unit_price']:,.2f} "
            f"= KES {item['total_price']:,.2f}"
        )

    lines.append("-" * 60)

    lines.append(
        f"Subtotal:       KES {order['subtotal']:,.2f}"
    )

    lines.append(
        f"Delivery Fee:   KES {order['delivery_fee']:,.2f}"
    )

    lines.append(
        f"TOTAL:          KES {order['total']:,.2f}"
    )

    lines.append("=" * 60)

    return "\n".join(lines)


# =============================================================
# TEST
# =============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("KENYABIZ AI")
    print("Order Tool Test")
    print("=" * 60)

    # Make sure the database exists
    initialize_database()

    test_items = [
        {
            "product_id": "P001",
            "quantity": 2
        },
        {
            "product_id": "P002",
            "quantity": 1
        }
    ]

    print()
    print("Creating test order...")

    order = create_order(
        customer_name="Test Customer",
        phone="0712345678",
        email="test@example.com",
        items=test_items
    )

    print()
    print("Order creation result:")
    print(order)

    if order["status"] == "SUCCESS":

        print()
        print("Retrieving order...")

        saved_order = get_order(
            order["order_reference"]
        )

        print()
        print(format_order(saved_order))

        print()
        print("Updating order status...")

        status_result = update_order_status(
            order["order_reference"],
            "CONFIRMED"
        )

        print(status_result)

        print()
        print("Retrieving updated order...")

        updated_order = get_order(
            order["order_reference"]
        )

        print()
        print(format_order(updated_order))

    print()
    print("=" * 60)
    print("ORDER TOOL TEST COMPLETED")
    print("=" * 60)