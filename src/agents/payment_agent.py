import json

from src.tools.payment_tool import (
    create_payment_request,
    complete_payment,
    get_payment_status,
    get_order_payments,
)
from src.tools.order_tool import get_order


# ============================================================
# KENYABIZ AI
# PAYMENT AGENT
# ============================================================

def process_payment_request(order_reference):
    """
    Create a simulated M-PESA-style payment request
    for an existing KenyaBiz AI order.

    This function does NOT process real payments.

    It checks the actual payment records associated
    with the order before creating a new payment request.
    """

    try:

        # ----------------------------------------------------
        # 1. Validate order reference
        # ----------------------------------------------------

        if not order_reference:

            return {
                "status": "ERROR",
                "message": "Please provide an order reference."
            }

        order_reference = (
            order_reference.strip().upper()
        )

        # ----------------------------------------------------
        # 2. Find the order
        # ----------------------------------------------------

        order = get_order(order_reference)

        if not order:

            return {
                "status": "NOT_FOUND",
                "message": (
                    f"No order was found with reference "
                    f"{order_reference}."
                )
            }

        # ----------------------------------------------------
        # 3. Check actual payment records
        # ----------------------------------------------------
        #
        # IMPORTANT:
        #
        # Do not rely only on orders.status.
        #
        # Payment status is stored in the payments table.
        #
        # ----------------------------------------------------

        payment_records = get_order_payments(
            order_reference
        )

        if payment_records.get("status") == "SUCCESS":

            payments = payment_records.get(
                "payments",
                []
            )

            # ------------------------------------------------
            # Find the most recent payment
            # ------------------------------------------------

            if payments:

                latest_payment = payments[0]

                payment_status = str(
                    latest_payment.get(
                        "status",
                        ""
                    )
                ).upper()

                payment_reference = (
                    latest_payment.get(
                        "payment_reference"
                    )
                )

                # --------------------------------------------
                # Already paid
                # --------------------------------------------

                if payment_status == "PAID":

                    return {
                        "status": "ALREADY_PAID",
                        "message": (
                            f"Order {order_reference} "
                            f"has already been paid."
                        ),
                        "order_reference": order_reference,
                        "payment_reference": payment_reference,
                        "amount": latest_payment.get(
                            "amount"
                        ),
                        "currency": "KES",
                        "payment_status": "PAID",
                        "order": order
                    }

                # --------------------------------------------
                # Existing pending payment
                # --------------------------------------------

                if payment_status == "PENDING":

                    return {
                        "status": "PAYMENT_ALREADY_PENDING",
                        "message": (
                            "A payment request already exists "
                            "for this order."
                        ),
                        "order_reference": order_reference,
                        "payment_reference": payment_reference,
                        "amount": latest_payment.get(
                            "amount"
                        ),
                        "currency": "KES",
                        "payment_method": latest_payment.get(
                            "method",
                            "M-PESA-SIMULATION"
                        ),
                        "payment_status": "PENDING",
                        "order": order
                    }

        # ----------------------------------------------------
        # 4. Handle inconsistent database state
        # ----------------------------------------------------
        #
        # If the order says PAID but there is no PAID payment
        # record, we should not silently create another payment.
        #
        # This protects the database from duplicate payments.
        # ----------------------------------------------------

        order_status = str(
            order.get(
                "status",
                "PENDING"
            )
        ).upper()

        if order_status == "PAID":

            return {
                "status": "PAYMENT_STATE_INCONSISTENT",
                "message": (
                    f"Order {order_reference} is marked as "
                    "PAID, but no completed payment record "
                    "was found. Please check the payment records "
                    "before creating another payment request."
                ),
                "order_reference": order_reference,
                "order_status": order_status,
                "order": order
            }

        # ----------------------------------------------------
        # 5. Get order total
        # ----------------------------------------------------

        amount = order.get("total")

        if amount is None:

            return {
                "status": "ERROR",
                "message": (
                    "The order does not contain a valid total."
                )
            }

        # ----------------------------------------------------
        # 6. Create payment request
        # ----------------------------------------------------

        payment_result = create_payment_request(
            order_reference
        )

        if not payment_result:

            return {
                "status": "ERROR",
                "message": (
                    "Unable to create the payment request."
                )
            }

        # ----------------------------------------------------
        # 7. Handle payment-tool error
        # ----------------------------------------------------

        if isinstance(payment_result, dict):

            if payment_result.get("status") == "ERROR":

                return {
                    "status": "ERROR",
                    "message": payment_result.get(
                        "message",
                        "Unable to create the payment request."
                    )
                }

            # ----------------------------------------------
            # Extract payment information
            # ----------------------------------------------

            payment_reference = (
                payment_result.get(
                    "payment_reference"
                )
                or payment_result.get(
                    "reference"
                )
            )

            payment_status = (
                payment_result.get(
                    "payment_status",
                    "PENDING"
                )
            )

            payment_amount = payment_result.get(
                "amount",
                amount
            )

            payment_method = (
                payment_result.get(
                    "method",
                    "M-PESA-SIMULATION"
                )
            )

        # ----------------------------------------------------
        # 8. Handle non-dictionary response
        # ----------------------------------------------------

        else:

            payment_reference = str(
                payment_result
            )

            payment_status = "PENDING"
            payment_amount = amount
            payment_method = "M-PESA-SIMULATION"

        # ----------------------------------------------------
        # 9. Validate payment reference
        # ----------------------------------------------------

        if not payment_reference:

            return {
                "status": "ERROR",
                "message": (
                    "Payment request was created, but "
                    "no payment reference was returned."
                )
            }

        # ----------------------------------------------------
        # 10. Currency
        # ----------------------------------------------------

        currency = order.get(
            "currency",
            "KES"
        )

        # ----------------------------------------------------
        # 11. Return payment request
        # ----------------------------------------------------

        return {
            "status": "PAYMENT_REQUEST_CREATED",
            "message": (
                "Payment request created successfully."
            ),
            "order_reference": order_reference,
            "payment_reference": payment_reference,
            "amount": payment_amount,
            "currency": currency,
            "payment_method": payment_method,
            "payment_status": payment_status,
            "order": order
        }

    except Exception as error:

        return {
            "status": "ERROR",
            "message": (
                f"Unable to process payment: {error}"
            )
        }


# ============================================================
# COMPLETE PAYMENT
# ============================================================

def process_payment_completion(payment_reference):
    """
    Complete a simulated payment.

    This changes the simulated payment status to PAID
    and updates the associated order to PAID.
    """

    try:

        # ----------------------------------------------------
        # 1. Validate payment reference
        # ----------------------------------------------------

        if not payment_reference:

            return {
                "status": "ERROR",
                "message": (
                    "Please provide a payment reference."
                )
            }

        payment_reference = (
            payment_reference.strip().upper()
        )

        # ----------------------------------------------------
        # 2. Check current payment status first
        # ----------------------------------------------------

        current_status = get_payment_status(
            payment_reference
        )

        if current_status.get("status") == "SUCCESS":

            payment = current_status.get(
                "payment",
                current_status
            )

            if isinstance(payment, dict):

                existing_status = str(
                    payment.get(
                        "payment_status",
                        payment.get(
                            "status",
                            ""
                        )
                    )
                ).upper()

                if existing_status == "PAID":

                    return {
                        "status": "ALREADY_PAID",
                        "message": (
                            f"Payment {payment_reference} "
                            "has already been completed."
                        ),
                        "payment_reference": payment_reference,
                        "payment": payment
                    }

        # ----------------------------------------------------
        # 3. Complete payment
        # ----------------------------------------------------

        result = complete_payment(
            payment_reference
        )

        if not result:

            return {
                "status": "ERROR",
                "message": (
                    "Unable to complete the payment."
                )
            }

        # ----------------------------------------------------
        # 4. Handle error
        # ----------------------------------------------------

        if isinstance(result, dict):

            if result.get("status") == "ERROR":

                return {
                    "status": "ERROR",
                    "message": result.get(
                        "message",
                        "Unable to complete the payment."
                    )
                }

            # ------------------------------------------------
            # Already completed
            # ------------------------------------------------

            if result.get(
                "payment_status"
            ) == "PAID":

                return {
                    "status": "PAYMENT_COMPLETED",
                    "message": (
                        "Payment completed successfully."
                    ),
                    "payment_reference": payment_reference,
                    "payment": result
                }

            return {
                "status": "PAYMENT_COMPLETED",
                "message": (
                    "Payment completed successfully."
                ),
                "payment_reference": payment_reference,
                "payment": result
            }

        # ----------------------------------------------------
        # 5. Non-dictionary response
        # ----------------------------------------------------

        return {
            "status": "PAYMENT_COMPLETED",
            "message": (
                "Payment completed successfully."
            ),
            "payment_reference": payment_reference,
            "payment": result
        }

    except Exception as error:

        return {
            "status": "ERROR",
            "message": (
                f"Unable to complete payment: {error}"
            )
        }


# ============================================================
# CHECK PAYMENT STATUS
# ============================================================

def check_payment_status(payment_reference):
    """
    Retrieve the current status of a simulated payment.
    """

    try:

        # ----------------------------------------------------
        # 1. Validate payment reference
        # ----------------------------------------------------

        if not payment_reference:

            return {
                "status": "ERROR",
                "message": (
                    "Please provide a payment reference."
                )
            }

        payment_reference = (
            payment_reference.strip().upper()
        )

        # ----------------------------------------------------
        # 2. Retrieve payment status
        # ----------------------------------------------------

        result = get_payment_status(
            payment_reference
        )

        # ----------------------------------------------------
        # 3. Payment not found
        # ----------------------------------------------------

        if not result:

            return {
                "status": "NOT_FOUND",
                "message": (
                    f"No payment was found with reference "
                    f"{payment_reference}."
                )
            }

        if result.get("status") == "ERROR":

            return {
                "status": "NOT_FOUND",
                "message": result.get(
                    "message",
                    f"No payment was found with reference "
                    f"{payment_reference}."
                )
            }

        # ----------------------------------------------------
        # 4. Return status
        # ----------------------------------------------------

        return {
            "status": "SUCCESS",
            "payment_reference": payment_reference,
            "payment": result
        }

    except Exception as error:

        return {
            "status": "ERROR",
            "message": (
                f"Unable to check payment status: {error}"
            )
        }


# ============================================================
# FORMAT PAYMENT REQUEST RESPONSE
# ============================================================

def format_payment_request(result):
    """
    Convert payment-request result into a
    customer-friendly response.
    """

    status = result.get("status")

    # --------------------------------------------------------
    # Order not found
    # --------------------------------------------------------

    if status == "NOT_FOUND":

        return result["message"]

    # --------------------------------------------------------
    # Already paid
    # --------------------------------------------------------

    if status == "ALREADY_PAID":

        lines = [
            result["message"],
        ]

        if result.get("payment_reference"):

            lines.append(
                f"Payment reference: "
                f"{result['payment_reference']}"
            )

        if result.get("amount") is not None:

            lines.append(
                f"Amount: KES "
                f"{result['amount']:,.2f}"
            )

        return "\n".join(lines)

    # --------------------------------------------------------
    # Existing pending payment
    # --------------------------------------------------------

    if status == "PAYMENT_ALREADY_PENDING":

        return "\n".join([
            "A payment request already exists.",
            "",
            f"Order reference: "
            f"{result['order_reference']}",
            f"Payment reference: "
            f"{result['payment_reference']}",
            f"Amount: "
            f"{result['currency']} "
            f"{result['amount']:,.2f}",
            f"Payment method: "
            f"{result['payment_method']}",
            "Payment status: PENDING",
            "",
            "Please use the existing payment request."
        ])

    # --------------------------------------------------------
    # Inconsistent database state
    # --------------------------------------------------------

    if status == "PAYMENT_STATE_INCONSISTENT":

        return result["message"]

    # --------------------------------------------------------
    # Error
    # --------------------------------------------------------

    if status != "PAYMENT_REQUEST_CREATED":

        return (
            "I could not create the payment request.\n\n"
            + result.get(
                "message",
                "Unknown payment error."
            )
        )

    # --------------------------------------------------------
    # Successful request
    # --------------------------------------------------------

    amount = result["amount"]

    return "\n".join([
        "Payment request created successfully.",
        "",
        f"Order reference: "
        f"{result['order_reference']}",
        f"Payment reference: "
        f"{result['payment_reference']}",
        f"Amount: "
        f"{result['currency']} {amount:,.2f}",
        f"Payment method: "
        f"{result['payment_method']}",
        f"Payment status: "
        f"{result['payment_status']}",
        "",
        "This is a simulated M-PESA-style payment workflow "
        "for the KenyaBiz AI demonstration."
    ])


# ============================================================
# FORMAT PAYMENT COMPLETION RESPONSE
# ============================================================

def format_payment_completion(result):
    """
    Convert payment-completion result into
    a customer-friendly response.
    """

    if result["status"] == "ALREADY_PAID":

        return result["message"]

    if result["status"] != "PAYMENT_COMPLETED":

        return (
            "I could not complete the payment.\n\n"
            + result.get(
                "message",
                "Unknown payment error."
            )
        )

    return "\n".join([
        "Payment completed successfully.",
        "",
        f"Payment reference: "
        f"{result['payment_reference']}",
        "",
        "The simulated payment has been marked as PAID."
    ])


# ============================================================
# FORMAT PAYMENT STATUS RESPONSE
# ============================================================

def format_payment_status(result):
    """
    Convert payment-status result into
    a customer-friendly response.
    """

    if result["status"] != "SUCCESS":

        return result["message"]

    payment = result["payment"]

    # --------------------------------------------------------
    # Dictionary response
    # --------------------------------------------------------

    if isinstance(payment, dict):

        payment_status = payment.get(
            "payment_status",
            payment.get(
                "status",
                "UNKNOWN"
            )
        )

        amount = payment.get(
            "amount"
        )

        lines = [
            "Payment status:",
            "",
            f"Payment reference: "
            f"{result['payment_reference']}",
            f"Status: {payment_status}"
        ]

        if payment.get("order_reference"):

            lines.append(
                f"Order reference: "
                f"{payment['order_reference']}"
            )

        if amount is not None:

            lines.append(
                f"Amount: KES {amount:,.2f}"
            )

        if payment.get("method"):

            lines.append(
                f"Payment method: "
                f"{payment['method']}"
            )

        return "\n".join(lines)

    # --------------------------------------------------------
    # Non-dictionary response
    # --------------------------------------------------------

    return "\n".join([
        "Payment status:",
        "",
        f"Payment reference: "
        f"{result['payment_reference']}",
        f"Status: {payment}"
    ])


# ============================================================
# TESTS
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("KENYABIZ AI")
    print("PAYMENT AGENT TEST")
    print("=" * 70)

    # --------------------------------------------------------
    # Test order
    # --------------------------------------------------------

    test_order_reference = "KBA-20260925-P5EP"

    # ========================================================
    # TEST 1
    # Create payment request
    # ========================================================

    print()
    print("TEST 1: CREATE PAYMENT REQUEST")
    print("-" * 70)

    payment_result = process_payment_request(
        test_order_reference
    )

    print()
    print("Raw result:")

    print(
        json.dumps(
            payment_result,
            indent=2,
            default=str
        )
    )

    print()
    print("Formatted response:")

    print(
        format_payment_request(
            payment_result
        )
    )

    # ========================================================
    # TEST 2
    # Check payment status
    # ========================================================

    if payment_result.get(
        "payment_reference"
    ):

        payment_reference = (
            payment_result["payment_reference"]
        )

        print()
        print("=" * 70)
        print("TEST 2: CHECK PAYMENT STATUS")
        print("-" * 70)

        status_result = check_payment_status(
            payment_reference
        )

        print()
        print(
            format_payment_status(
                status_result
            )
        )

        # ====================================================
        # TEST 3
        # Complete simulated payment
        # ====================================================

        print()
        print("=" * 70)
        print("TEST 3: COMPLETE SIMULATED PAYMENT")
        print("-" * 70)

        completion_result = (
            process_payment_completion(
                payment_reference
            )
        )

        print()
        print(
            format_payment_completion(
                completion_result
            )
        )

        # ====================================================
        # TEST 4
        # Check status after payment
        # ====================================================

        print()
        print("=" * 70)
        print("TEST 4: CHECK STATUS AFTER PAYMENT")
        print("-" * 70)

        final_status = check_payment_status(
            payment_reference
        )

        print()
        print(
            format_payment_status(
                final_status
            )
        )

    print()
    print("=" * 70)
    print("PAYMENT AGENT TEST COMPLETE")
    print("=" * 70)