import re
from pathlib import Path

from src.graph import run_kenyabiz


# ============================================================
# SUPPORT / GENERAL QUESTIONS
# ============================================================

def test_support_company_question():
    """Customer asks a general question about KenyaBiz."""

    result = run_kenyabiz(
        "Can you tell me about KenyaBiz?"
    )

    assert result["destination"] == "support"
    assert result["status"] == "COMPLETED"
    assert result["response"]

    response = result["response"].lower()

    assert "kenyabiz" in response


# ============================================================
# SALES / PRODUCT PRICE
# ============================================================

def test_product_price_question():
    """Customer asks for the price of a product."""

    result = run_kenyabiz(
        "How much is a keyboard?"
    )

    assert result["destination"] == "sales"
    assert result["status"] == "COMPLETED"
    assert result["response"]

    response = result["response"].lower()

    assert "keyboard" in response
    assert "2,800" in response


# ============================================================
# ORDER - START
# ============================================================

def test_new_order_starts_confirmation_flow():
    """Customer starts a valid order and receives confirmation."""

    result = run_kenyabiz(
        "I want to order 2 office chairs."
    )

    assert result["destination"] == "order"
    assert result["status"] == "WAITING"

    assert result["pending_action"] == (
        "ORDER_CONFIRMATION"
    )

    assert result["forced_destination"] == "order"
    assert result["order_confirmed"] is False
    assert result["pending_request"]


# ============================================================
# ORDER - COMPLETE MULTI-TURN FLOW
# ============================================================

def test_complete_order_flow():
    """Customer completes a basic multi-turn order."""

    # --------------------------------------------------------
    # Step 1: Start order
    # --------------------------------------------------------

    result1 = run_kenyabiz(
        "I want to order 2 office chairs."
    )

    assert result1["destination"] == "order"
    assert result1["status"] == "WAITING"

    assert result1["pending_action"] == (
        "ORDER_CONFIRMATION"
    )

    # --------------------------------------------------------
    # Step 2: Confirm order
    # --------------------------------------------------------

    result2 = run_kenyabiz(
        "yes",
        pending_request=result1.get(
            "pending_request"
        ),
        pending_action=result1.get(
            "pending_action"
        ),
        forced_destination=result1.get(
            "forced_destination"
        ),
        order_confirmed=result1.get(
            "order_confirmed",
            False,
        ),
    )

    assert result2["destination"] == "order"
    assert result2["status"] == "WAITING"

    assert result2["pending_action"] == (
        "ORDER_CUSTOMER_NAME"
    )

    assert result2["order_confirmed"] is True

    # --------------------------------------------------------
    # Step 3: Provide customer name
    # --------------------------------------------------------

    result3 = run_kenyabiz(
        "Ambrose Lengerpei",
        pending_request=result2.get(
            "pending_request"
        ),
        pending_action=result2.get(
            "pending_action"
        ),
        forced_destination=result2.get(
            "forced_destination"
        ),
        order_confirmed=result2.get(
            "order_confirmed",
            False,
        ),
        order_reference=result2.get(
            "order_reference"
        ),
        order_status=result2.get(
            "order_status"
        ),
    )

    assert result3["destination"] == "order"
    assert result3["status"] == "COMPLETED"

    assert result3["order_reference"]

    assert re.match(
        r"^KBA-\d{8}-[A-Z0-9]+$",
        result3["order_reference"],
    )

    assert result3["order_status"] == "CONFIRMED"


# ============================================================
# ORDER - INTERRUPTION BY SUPPORT QUESTION
# ============================================================

def test_order_flow_survives_support_question():
    """A support question should not destroy an active order."""

    # --------------------------------------------------------
    # Step 1: Start order
    # --------------------------------------------------------

    result1 = run_kenyabiz(
        "I want to order 2 office chairs."
    )

    assert result1["status"] == "WAITING"
    assert result1["pending_action"] == (
        "ORDER_CONFIRMATION"
    )

    # --------------------------------------------------------
    # Step 2: Ask unrelated support question
    # --------------------------------------------------------

    result2 = run_kenyabiz(
        "What are your payment methods?",
        pending_request=result1.get(
            "pending_request"
        ),
        pending_action=result1.get(
            "pending_action"
        ),
        forced_destination=result1.get(
            "forced_destination"
        ),
        order_confirmed=result1.get(
            "order_confirmed",
            False,
        ),
    )

    assert result2["destination"] == "support"
    assert result2["status"] == "COMPLETED"

    # --------------------------------------------------------
    # Step 3: Verify pending order was preserved
    # --------------------------------------------------------

    assert result2["pending_request"]

    assert result2["pending_action"] == (
        "ORDER_CONFIRMATION"
    )

    assert result2["forced_destination"] == "order"

    assert result2["order_confirmed"] is False


# ============================================================
# ORDER - CONTINUE AFTER SUPPORT QUESTION
# ============================================================

def test_order_can_continue_after_support_question():
    """Customer can return to the pending order after a support question."""

    # --------------------------------------------------------
    # Step 1: Start order
    # --------------------------------------------------------

    result1 = run_kenyabiz(
        "I want to order 2 office chairs."
    )

    assert result1["status"] == "WAITING"
    assert result1["pending_action"] == (
        "ORDER_CONFIRMATION"
    )

    # --------------------------------------------------------
    # Step 2: Ask support question
    # --------------------------------------------------------

    result2 = run_kenyabiz(
        "What are your payment methods?",
        pending_request=result1.get(
            "pending_request"
        ),
        pending_action=result1.get(
            "pending_action"
        ),
        forced_destination=result1.get(
            "forced_destination"
        ),
        order_confirmed=result1.get(
            "order_confirmed",
            False,
        ),
    )

    assert result2["destination"] == "support"
    assert result2["status"] == "COMPLETED"

    assert result2["pending_action"] == (
        "ORDER_CONFIRMATION"
    )

    # --------------------------------------------------------
    # Step 3: Return to order and confirm
    # --------------------------------------------------------

    result3 = run_kenyabiz(
        "yes",
        pending_request=result2.get(
            "pending_request"
        ),
        pending_action=result2.get(
            "pending_action"
        ),
        forced_destination=result2.get(
            "forced_destination"
        ),
        order_confirmed=result2.get(
            "order_confirmed",
            False,
        ),
    )

    assert result3["destination"] == "order"
    assert result3["status"] == "WAITING"

    assert result3["pending_action"] == (
        "ORDER_CUSTOMER_NAME"
    )

    assert result3["order_confirmed"] is True


# ============================================================
# HELPER - CREATE A CONFIRMED ORDER
# ============================================================

def create_test_order():
    """
    Create a real confirmed order through the graph.

    Returns the final graph state containing the order
    reference and related information.
    """

    # --------------------------------------------------------
    # Step 1: Start order
    # --------------------------------------------------------

    result1 = run_kenyabiz(
        "I want to order 1 keyboard."
    )

    assert result1["destination"] == "order"
    assert result1["status"] == "WAITING"

    assert result1["pending_action"] == (
        "ORDER_CONFIRMATION"
    )

    # --------------------------------------------------------
    # Step 2: Confirm
    # --------------------------------------------------------

    result2 = run_kenyabiz(
        "yes",
        pending_request=result1.get(
            "pending_request"
        ),
        pending_action=result1.get(
            "pending_action"
        ),
        forced_destination=result1.get(
            "forced_destination"
        ),
        order_confirmed=result1.get(
            "order_confirmed",
            False,
        ),
    )

    assert result2["destination"] == "order"
    assert result2["status"] == "WAITING"

    assert result2["pending_action"] == (
        "ORDER_CUSTOMER_NAME"
    )

    # --------------------------------------------------------
    # Step 3: Customer name
    # --------------------------------------------------------

    result3 = run_kenyabiz(
        "Test Customer",
        pending_request=result2.get(
            "pending_request"
        ),
        pending_action=result2.get(
            "pending_action"
        ),
        forced_destination=result2.get(
            "forced_destination"
        ),
        order_confirmed=result2.get(
            "order_confirmed",
            False,
        ),
        order_reference=result2.get(
            "order_reference"
        ),
        order_status=result2.get(
            "order_status"
        ),
    )

    assert result3["destination"] == "order"
    assert result3["status"] == "COMPLETED"
    assert result3["order_status"] == "CONFIRMED"

    assert result3["order_reference"]

    assert re.match(
        r"^KBA-\d{8}-[A-Z0-9]+$",
        result3["order_reference"],
    )

    return result3


# ============================================================
# INVOICE - GENERATE FROM ORDER
# ============================================================

def test_invoice_generation_after_order():
    """A confirmed order can be used to generate an invoice."""

    # --------------------------------------------------------
    # Create confirmed order
    # --------------------------------------------------------

    order_result = create_test_order()

    order_reference = order_result[
        "order_reference"
    ]

    # --------------------------------------------------------
    # Request invoice
    # --------------------------------------------------------

    invoice_result = run_kenyabiz(
        f"Please generate an invoice for {order_reference}.",
        order_reference=order_reference,
        order_status=order_result.get(
            "order_status"
        ),
    )

    assert invoice_result["destination"] == "invoice"
    assert invoice_result["status"] == "COMPLETED"

    assert invoice_result["order_reference"] == (
        order_reference
    )

    assert invoice_result["invoice_path"]

    invoice_path = Path(
        invoice_result["invoice_path"]
    )

    assert invoice_path.exists()


# ============================================================
# PAYMENT - CREATE PAYMENT REQUEST
# ============================================================

def test_payment_request_after_order():
    """A confirmed order can be used to create a payment request."""

    # --------------------------------------------------------
    # Create confirmed order
    # --------------------------------------------------------

    order_result = create_test_order()

    order_reference = order_result[
        "order_reference"
    ]

    # --------------------------------------------------------
    # Request payment
    # --------------------------------------------------------

    payment_result = run_kenyabiz(
        f"I want to pay for order {order_reference}.",
        order_reference=order_reference,
        order_status=order_result.get(
            "order_status"
        ),
    )

    assert payment_result["destination"] == "payment"
    assert payment_result["status"] == "COMPLETED"

    assert payment_result["payment_reference"]

    assert re.match(
        r"^MPS[A-Z0-9]+$",
        payment_result["payment_reference"],
    )

    assert payment_result["order_reference"] == (
        order_reference
    )

    assert payment_result["response"]

    response = payment_result[
        "response"
    ].lower()

    assert "payment" in response


# ============================================================
# PAYMENT - COMPLETE SIMULATED PAYMENT
# ============================================================

def test_complete_payment_flow():
    """Customer can create and complete a simulated payment."""

    # --------------------------------------------------------
    # Step 1: Create confirmed order
    # --------------------------------------------------------

    order_result = create_test_order()

    order_reference = order_result[
        "order_reference"
    ]

    # --------------------------------------------------------
    # Step 2: Create payment request
    # --------------------------------------------------------

    payment_result = run_kenyabiz(
        f"I want to pay for order {order_reference}.",
        order_reference=order_reference,
        order_status=order_result.get(
            "order_status"
        ),
    )

    assert payment_result["destination"] == "payment"
    assert payment_result["status"] == "COMPLETED"

    assert payment_result["payment_reference"]

    payment_reference = (
        payment_result["payment_reference"]
    )

    # --------------------------------------------------------
    # Step 3: Complete simulated payment
    # --------------------------------------------------------

    completion_result = run_kenyabiz(
        f"Complete payment {payment_reference}.",
        order_reference=order_reference,
        order_status=order_result.get(
            "order_status"
        ),
        payment_reference=payment_reference,
        payment_status=payment_result.get(
            "payment_status"
        ),
    )

    assert completion_result["destination"] == "payment"
    assert completion_result["status"] == "COMPLETED"

    assert completion_result[
        "payment_reference"
    ] == payment_reference

    assert completion_result["response"]

    response = completion_result[
        "response"
    ].lower()

    assert "completed" in response


# ============================================================
# PAYMENT - CHECK FINAL PAYMENT STATUS
# ============================================================

def test_payment_status_after_completion():
    """Payment status can be checked after simulated payment."""

    # --------------------------------------------------------
    # Step 1: Create confirmed order
    # --------------------------------------------------------

    order_result = create_test_order()

    order_reference = order_result[
        "order_reference"
    ]

    # --------------------------------------------------------
    # Step 2: Create payment request
    # --------------------------------------------------------

    payment_result = run_kenyabiz(
        f"I want to pay for order {order_reference}.",
        order_reference=order_reference,
        order_status=order_result.get(
            "order_status"
        ),
    )

    assert payment_result["payment_reference"]

    payment_reference = (
        payment_result["payment_reference"]
    )

    # --------------------------------------------------------
    # Step 3: Complete payment
    # --------------------------------------------------------

    completion_result = run_kenyabiz(
        f"Complete payment {payment_reference}.",
        order_reference=order_reference,
        payment_reference=payment_reference,
        payment_status=payment_result.get(
            "payment_status"
        ),
        order_status=order_result.get(
            "order_status"
        ),
    )

    assert completion_result["status"] == "COMPLETED"

    assert completion_result[
        "payment_reference"
    ] == payment_reference

    # --------------------------------------------------------
    # Step 4: Ask for payment status
    # --------------------------------------------------------

    status_result = run_kenyabiz(
        f"What is the status of payment {payment_reference}?",
        order_reference=order_reference,
        payment_reference=payment_reference,
        payment_status="PAID",
        order_status="PAID",
    )

    assert status_result["destination"] == "payment"
    assert status_result["status"] == "COMPLETED"

    assert status_result[
        "payment_reference"
    ] == payment_reference

    assert status_result["response"]

    response = status_result[
        "response"
    ].lower()

    assert "paid" in response


# ============================================================
# EDGE CASES / FAILURE PATHS
# ============================================================

def test_order_unknown_product():
    """
    Unknown products should be detected before confirmation.

    The system should not create an artificial
    ORDER_CONFIRMATION step because the requested product
    does not exist in the catalogue.
    """

    result = run_kenyabiz(
        "I want to order 2 smartphones."
    )

    assert result["destination"] == "order"
    assert result["status"] == "WAITING"

    # No valid order exists to confirm.
    assert result["pending_action"] is None
    assert result["forced_destination"] is None
    assert result["order_confirmed"] is False

    assert result["response"]

    response = result["response"].lower()

    assert (
        "not found" in response
        or "could not be found" in response
    )


def test_order_insufficient_stock():
    """
    An order exceeding available stock should be rejected
    before confirmation.
    """

    result = run_kenyabiz(
        "I want to order 1000 office chairs."
    )

    assert result["destination"] == "order"
    assert result["status"] == "WAITING"

    # No confirmation should be requested for an order
    # that cannot be fulfilled.
    assert result["pending_action"] is None
    assert result["forced_destination"] is None
    assert result["order_confirmed"] is False

    assert result["response"]

    response = result["response"].lower()

    assert "stock" in response


def test_decline_order():
    """Customer can decline an order before it is created."""

    # --------------------------------------------------------
    # Step 1: Start order
    # --------------------------------------------------------

    result1 = run_kenyabiz(
        "I want to order 2 office chairs."
    )

    assert result1["destination"] == "order"
    assert result1["status"] == "WAITING"

    assert result1["pending_action"] == (
        "ORDER_CONFIRMATION"
    )

    assert result1["order_confirmed"] is False

    # --------------------------------------------------------
    # Step 2: Decline order
    # --------------------------------------------------------

    result2 = run_kenyabiz(
        "no",
        pending_request=result1.get(
            "pending_request"
        ),
        pending_action=result1.get(
            "pending_action"
        ),
        forced_destination=result1.get(
            "forced_destination"
        ),
        order_confirmed=result1.get(
            "order_confirmed",
            False,
        ),
    )

    assert result2["destination"] == "order"
    assert result2["status"] == "COMPLETED"

    assert result2["response"]

    # The order workflow should be cleared.
    assert result2["pending_request"] is None
    assert result2["pending_action"] is None
    assert result2["forced_destination"] is None
    assert result2["order_confirmed"] is False

    response = result2[
        "response"
    ].lower()

    assert (
        "cancel" in response
        or "not proceed" in response
        or "not placed" in response
    )


def test_invoice_invalid_order_reference():
    """
    An invalid order reference should not generate an invoice.
    """

    result = run_kenyabiz(
        "Please generate an invoice for KBA-UNKNOWN."
    )

    assert result["destination"] == "invoice"

    assert result["status"] in {
        "WAITING",
        "ERROR",
    }

    assert result["response"]