from typing import Any, TypedDict


class KenyaBizState(TypedDict, total=False):
    """
    Shared state used by all KenyaBiz AI agents.

    Supports both single-turn requests and multi-turn
    conversations involving sales, orders, invoices,
    and payments.
    """

    # ========================================================
    # CURRENT CUSTOMER MESSAGE
    # ========================================================

    customer_message: str

    # ========================================================
    # CONVERSATION MEMORY
    # ========================================================

    conversation_history: list[dict[str, str]]

    # ========================================================
    # PENDING WORKFLOW
    # ========================================================

    pending_request: str
    pending_action: str

    # ========================================================
    # CUSTOMER INFORMATION
    # ========================================================

    customer_name: str
    customer_phone: str
    customer_email: str

    # ========================================================
    # ROUTING
    # ========================================================

    destination: str
    forced_destination: str
    routing_reason: str

    # ========================================================
    # ORDER INFORMATION
    # ========================================================

    order_confirmed: bool
    order_status: str
    order_reference: str

    # ========================================================
    # INVOICE INFORMATION
    # ========================================================

    invoice_path: str

    # ========================================================
    # PAYMENT INFORMATION
    # ========================================================

    payment_reference: str
    payment_status: str

    # ========================================================
    # AGENT RESULT
    # ========================================================

    result: dict[str, Any]

    # ========================================================
    # CUSTOMER-FACING RESPONSE
    # ========================================================

    response: str

    # ========================================================
    # GENERAL WORKFLOW STATUS
    # ========================================================

    status: str