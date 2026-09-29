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

    # Stores previous customer and assistant messages.

    # ========================================================
    # PENDING REQUEST / WORKFLOW
    # ========================================================

    pending_request: str

    # Stores the original customer request while the system
    # is waiting for additional information or confirmation.

    pending_action: str

    # Examples:
    #
    # SALES_QUOTATION
    # ORDER_CONFIRMATION
    # ORDER_CUSTOMER_NAME
    # ORDER_WORKFLOW
    # INVOICE_ORDER_REFERENCE
    # PAYMENT_ORDER_REFERENCE
    # PAYMENT_REFERENCE

    # ========================================================
    # PENDING STRUCTURED ORDER
    # ========================================================

    pending_order: dict[str, Any]

    # Stores the structured order extracted from the customer's
    # original request.
    #
    # Example:
    #
    # {
    #     "customer": {
    #         "name": "Ambrose Lengerpei",
    #         "phone": "0712345678",
    #         "email": "example@email.com"
    #     },
    #     "items": [
    #         {
    #             "product_name": "office chair",
    #             "quantity": 2
    #         }
    #     ]
    # }
    #
    # This allows the confirmation turn ("yes", "proceed", etc.)
    # to reuse the already-extracted order instead of asking the
    # LLM to extract the order again.

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

    # Possible values:
    #
    # support
    # sales
    # order
    # invoice
    # payment

    forced_destination: str

    # Used when the conversation manager already knows which
    # specialist agent should handle the next message.

    routing_reason: str

    # Explanation returned by the supervisor/router.

    # ========================================================
    # ORDER INFORMATION
    # ========================================================

    order_confirmed: bool

    # True when the customer has confirmed the pending order.

    order_status: str

    # Possible values:
    #
    # PENDING
    # CONFIRMED
    # PAID
    # PROCESSING
    # DELIVERED
    # CANCELLED
    # AWAITING_CONFIRMATION
    # CUSTOMER_DETAILS_REQUIRED
    # PRODUCT_NOT_FOUND
    # AMBIGUOUS_PRODUCT
    # INSUFFICIENT_STOCK
    # ERROR

    order_reference: str

    # Example:
    #
    # KBA-20260925-P5EP

    # ========================================================
    # INVOICE INFORMATION
    # ========================================================

    invoice_path: str

    # Example:
    #
    # invoices/invoice_KBA-20260925-P5EP.pdf

    # ========================================================
    # PAYMENT INFORMATION
    # ========================================================

    payment_reference: str

    # Example:
    #
    # MPSABC123456

    # ========================================================
    # AGENT RESULT
    # ========================================================

    result: dict[str, Any]

    # Stores the structured result returned by the specialist
    # agent.

    # ========================================================
    # CUSTOMER-FACING RESPONSE
    # ========================================================

    response: str

    # Final response displayed to the customer.

    # ========================================================
    # GENERAL WORKFLOW STATUS
    # ========================================================

    status: str

    # Examples:
    #
    # COMPLETED
    # WAITING
    # WAITING_FOR_INFORMATION
    # ERROR