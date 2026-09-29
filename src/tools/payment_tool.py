from datetime import datetime
import random
import string

from src.database.database import get_connection, initialize_database
from src.tools.order_tool import get_order


# ============================================================
# PAYMENT REFERENCE
# ============================================================

def generate_payment_reference():
    """
    Generate a simulated M-PESA-style payment reference.

    Example:
    MPSA7F3K91
    """

    random_part = "".join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=8
        )
    )

    return f"MPS{random_part}"


# ============================================================
# CREATE PAYMENT REQUEST
# ============================================================

def create_payment_request(order_reference):
    """
    Create a simulated payment request for an existing order.
    """

    # --------------------------------------------------------
    # Get order
    # --------------------------------------------------------

    order = get_order(order_reference)

    if order is None:
        return {
            "status": "ERROR",
            "message": (
                f"Order {order_reference} was not found."
            )
        }

    # --------------------------------------------------------
    # Check if order is already paid
    # --------------------------------------------------------

    if order["status"] == "PAID":
        return {
            "status": "ERROR",
            "message": (
                f"Order {order_reference} has already been paid."
            )
        }

    connection = get_connection()

    try:

        cursor = connection.cursor()

        # ----------------------------------------------------
        # Check for existing pending payment
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                payment_id,
                payment_reference,
                amount,
                method,
                status,
                created_at
            FROM payments
            WHERE order_id = ?
            AND status = 'PENDING'
            ORDER BY payment_id DESC
            LIMIT 1
            """,
            (order["order_id"],)
        )

        existing_payment = cursor.fetchone()

        if existing_payment:

            return {
                "status": "SUCCESS",
                "message": "A pending payment already exists.",
                "order_reference": order_reference,
                "payment_reference": existing_payment[
                    "payment_reference"
                ],
                "amount": existing_payment["amount"],
                "currency": "KES",
                "method": existing_payment["method"],
                "payment_status": existing_payment["status"]
            }

        # ----------------------------------------------------
        # Generate payment reference
        # ----------------------------------------------------

        payment_reference = generate_payment_reference()

        # ----------------------------------------------------
        # Create payment record
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO payments (
                order_id,
                payment_reference,
                amount,
                method,
                status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                order["order_id"],
                payment_reference,
                order["total"],
                "M-PESA-SIMULATION",
                "PENDING"
            )
        )

        connection.commit()

        return {
            "status": "SUCCESS",
            "message": "Payment request created.",
            "order_reference": order_reference,
            "payment_reference": payment_reference,
            "amount": order["total"],
            "currency": "KES",
            "method": "M-PESA-SIMULATION",
            "payment_status": "PENDING"
        }

    except Exception as error:

        connection.rollback()

        return {
            "status": "ERROR",
            "message": (
                f"Unable to create payment request: {error}"
            )
        }

    finally:

        connection.close()


# ============================================================
# COMPLETE SIMULATED PAYMENT
# ============================================================

def complete_payment(payment_reference):
    """
    Simulate successful payment for a payment request.

    In a real system, this would be replaced by a payment
    provider callback/webhook.
    """

    connection = get_connection()

    try:

        cursor = connection.cursor()

        # ----------------------------------------------------
        # Find payment
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                payment_id,
                order_id,
                payment_reference,
                amount,
                method,
                status,
                created_at
            FROM payments
            WHERE payment_reference = ?
            """,
            (payment_reference,)
        )

        payment = cursor.fetchone()

        if payment is None:

            return {
                "status": "ERROR",
                "message": (
                    f"Payment {payment_reference} was not found."
                )
            }

        # ----------------------------------------------------
        # Check payment status
        # ----------------------------------------------------

        if payment["status"] == "PAID":

            return {
                "status": "SUCCESS",
                "message": "Payment has already been completed.",
                "payment_reference": payment_reference,
                "payment_status": "PAID"
            }

        # ----------------------------------------------------
        # Update payment
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE payments
            SET status = 'PAID'
            WHERE payment_reference = ?
            """,
            (payment_reference,)
        )

        # ----------------------------------------------------
        # Update order status
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE orders
            SET status = 'PAID'
            WHERE order_id = ?
            """,
            (payment["order_id"],)
        )

        connection.commit()

        return {
            "status": "SUCCESS",
            "message": "Payment completed successfully.",
            "payment_reference": payment_reference,
            "order_id": payment["order_id"],
            "amount": payment["amount"],
            "currency": "KES",
            "payment_status": "PAID",
            "order_status": "PAID"
        }

    except Exception as error:

        connection.rollback()

        return {
            "status": "ERROR",
            "message": (
                f"Unable to complete payment: {error}"
            )
        }

    finally:

        connection.close()


# ============================================================
# CHECK PAYMENT STATUS
# ============================================================

def get_payment_status(payment_reference):
    """
    Retrieve the current status of a payment.
    """

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                p.payment_id,
                p.order_id,
                o.order_reference,
                p.payment_reference,
                p.amount,
                p.method,
                p.status,
                p.created_at
            FROM payments p
            JOIN orders o
                ON p.order_id = o.order_id
            WHERE p.payment_reference = ?
            """,
            (payment_reference,)
        )

        payment = cursor.fetchone()

        if payment is None:

            return {
                "status": "ERROR",
                "message": (
                    f"Payment {payment_reference} was not found."
                )
            }

        return {
            "status": "SUCCESS",
            "payment_id": payment["payment_id"],
            "order_id": payment["order_id"],
            "order_reference": payment["order_reference"],
            "payment_reference": payment["payment_reference"],
            "amount": payment["amount"],
            "currency": "KES",
            "method": payment["method"],
            "payment_status": payment["status"],
            "created_at": payment["created_at"]
        }

    finally:

        connection.close()


# ============================================================
# GET PAYMENTS FOR ORDER
# ============================================================

def get_order_payments(order_reference):
    """
    Retrieve all payment records associated with an order.
    """

    order = get_order(order_reference)

    if order is None:

        return {
            "status": "ERROR",
            "message": (
                f"Order {order_reference} was not found."
            )
        }

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                payment_id,
                payment_reference,
                amount,
                method,
                status,
                created_at
            FROM payments
            WHERE order_id = ?
            ORDER BY payment_id DESC
            """,
            (order["order_id"],)
        )

        payments = [
            dict(payment)
            for payment in cursor.fetchall()
        ]

        return {
            "status": "SUCCESS",
            "order_reference": order_reference,
            "payments": payments
        }

    finally:

        connection.close()


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("KENYABIZ AI")
    print("Payment Tool Test")
    print("=" * 60)

    # --------------------------------------------------------
    # Make sure database exists
    # --------------------------------------------------------

    initialize_database()

    # --------------------------------------------------------
    # Create a test order
    # --------------------------------------------------------

    from src.tools.order_tool import create_order

    test_items = [
        {
            "product_id": "P001",
            "quantity": 1
        },
        {
            "product_id": "P003",
            "quantity": 1
        }
    ]

    print()
    print("Creating test order...")

    order = create_order(
        customer_name="Payment Test Customer",
        phone="0712345678",
        email="payment@example.com",
        items=test_items
    )

    if order["status"] != "SUCCESS":

        print()
        print("ERROR:")
        print(order["message"])

    else:

        order_reference = order["order_reference"]

        print()
        print(
            f"Order created: {order_reference}"
        )

        print(
            f"Order total: KES {order['total']:,.2f}"
        )

        # ----------------------------------------------------
        # Create payment request
        # ----------------------------------------------------

        print()
        print("Creating payment request...")

        payment = create_payment_request(
            order_reference
        )

        print()
        print("Payment request:")
        print(payment)

        if payment["status"] == "SUCCESS":

            payment_reference = payment[
                "payment_reference"
            ]

            # ------------------------------------------------
            # Check status
            # ------------------------------------------------

            print()
            print("Checking payment status...")

            status = get_payment_status(
                payment_reference
            )

            print()
            print(status)

            # ------------------------------------------------
            # Simulate payment
            # ------------------------------------------------

            print()
            print("Completing simulated payment...")

            completed = complete_payment(
                payment_reference
            )

            print()
            print(completed)

            # ------------------------------------------------
            # Check final status
            # ------------------------------------------------

            print()
            print("Checking final payment status...")

            final_status = get_payment_status(
                payment_reference
            )

            print()
            print(final_status)

            # ------------------------------------------------
            # Check order payments
            # ------------------------------------------------

            print()
            print("All payments for order:")

            order_payments = get_order_payments(
                order_reference
            )

            print()
            print(order_payments)

    print()
    print("=" * 60)
    print("PAYMENT TOOL TEST COMPLETED")
    print("=" * 60)