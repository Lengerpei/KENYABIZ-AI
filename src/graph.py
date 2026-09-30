import re
from typing import Optional

from langgraph.graph import StateGraph, START, END

from src.state import KenyaBizState
from src.agents.supervisor import route_customer_request
from src.agents.support_agent import get_support_response
from src.agents.sales_agent import (
    process_sales_request,
    is_stock_request,
    is_explicit_order_request,
)
from src.agents.order_agent import (
    process_order,
    format_order_response,
)
from src.agents.invoice_agent import (
    process_invoice_request,
    format_invoice_response,
)
from src.agents.payment_agent import (
    process_payment_request,
    process_payment_completion,
    check_payment_status,
    format_payment_request,
    format_payment_completion,
    format_payment_status,
)


# ============================================================
# VALID DESTINATIONS
# ============================================================

VALID_DESTINATIONS = {
    "support",
    "sales",
    "order",
    "invoice",
    "payment",
}


# ============================================================
# REFERENCE EXTRACTION
# ============================================================

def extract_order_reference(
    text: str,
) -> Optional[str]:

    if not text:
        return None

    match = re.search(
        r"\bKBA-\d{8}-[A-Z0-9]+\b",
        text.upper(),
    )

    return match.group(0) if match else None


def extract_payment_reference(
    text: str,
) -> Optional[str]:

    if not text:
        return None

    match = re.search(
        r"\bMPS[A-Z0-9]+\b",
        text.upper(),
    )

    return match.group(0) if match else None


# ============================================================
# INVOICE DETECTION
# ============================================================

def looks_like_invoice_request(
    text: str,
) -> bool:

    if not text:
        return False

    normalized = re.sub(
        r"\s+",
        " ",
        text.lower().strip(),
    )

    invoice_terms = [
        "invoice",
        "invoicing",
        "bill",
        "billing",
        "receipt",
    ]

    return any(
        term in normalized
        for term in invoice_terms
    )


# ============================================================
# PAYMENT DETECTION
# ============================================================

def looks_like_payment_request(
    text: str,
) -> bool:

    if not text:
        return False

    normalized = re.sub(
        r"\s+",
        " ",
        text.lower().strip(),
    )

    payment_phrases = [
        "make payment",
        "make a payment",
        "i want to pay",
        "i need to pay",
        "i would like to pay",
        "i want payment",
        "pay for my order",
        "pay for the order",
        "payment for my order",
        "payment for the order",
        "how do i pay",
        "how can i pay",
        "mpesa",
        "m-pesa",
        "m pesa",
    ]

    return any(
        phrase in normalized
        for phrase in payment_phrases
    )


# ============================================================
# CONFIRMATION DETECTION
# ============================================================

def contains_confirmation(
    text: str,
) -> bool:

    if not text:
        return False

    normalized = re.sub(
        r"\s+",
        " ",
        text.lower().strip(),
    )

    confirmation_phrases = [
        "yes",
        "yes please",
        "confirm",
        "confirmed",
        "proceed",
        "go ahead",
        "place the order",
        "place it",
        "confirm order",
        "confirm the order",
        "i confirm",
        "i want to proceed",
        "please proceed",
        "that's correct",
        "that is correct",
        "correct",
        "okay",
        "ok",
    ]

    return any(
        phrase == normalized
        or phrase in normalized
        for phrase in confirmation_phrases
    )


# ============================================================
# NEGATIVE / ORDER RESPONSE DETECTION
# ============================================================

def contains_order_decline(
    text: str,
) -> bool:

    if not text:
        return False

    normalized = re.sub(
        r"\s+",
        " ",
        text.lower().strip(),
    )

    decline_phrases = [
        "no",
        "no thanks",
        "no thank you",
        "cancel",
        "cancel it",
        "cancel the order",
        "do not proceed",
        "don't proceed",
        "do not place",
        "don't place",
    ]

    return any(
        phrase == normalized
        or phrase in normalized
        for phrase in decline_phrases
    )


# ============================================================
# QUOTATION DETECTION
# ============================================================

def looks_like_quotation_request(
    text: str,
) -> bool:

    if not text:
        return False

    normalized = text.lower().strip()

    # --------------------------------------------------------
    # Stock requests must never become quotations.
    # --------------------------------------------------------

    if is_stock_request(normalized):
        return False

    # --------------------------------------------------------
    # Explicit orders must never become quotations.
    # --------------------------------------------------------

    try:
        if is_explicit_order_request(normalized):
            return False
    except Exception:
        pass

    quotation_phrases = [
        "quotation",
        "quote",
        "price quote",
        "pricing",
        "how much would",
        "how much will",
        "how much for",
        "total cost",
        "cost for",
        "cost of",
        "i need",
        "i want",
        "buy",
        "purchase",
    ]

    has_quantity = bool(
        re.search(
            r"\b\d+\b",
            normalized,
        )
    )

    has_number_word = any(
        re.search(
            rf"\b{word}\b",
            normalized,
        )
        for word in [
            "one",
            "two",
            "three",
            "four",
            "five",
            "six",
            "seven",
            "eight",
            "nine",
            "ten",
        ]
    )

    has_quantity = (
        has_quantity
        or has_number_word
    )

    has_multiple_products = (
        " and " in normalized
        and has_quantity
    )

    has_quotation_language = any(
        phrase in normalized
        for phrase in quotation_phrases
    )

    return (
        has_multiple_products
        or (
            has_quantity
            and has_quotation_language
        )
    )


# ============================================================
# ACTIVE ORDER FLOW
# ============================================================

def has_active_order_flow(
    state: KenyaBizState,
) -> bool:

    pending_action = state.get(
        "pending_action"
    )

    forced_destination = state.get(
        "forced_destination"
    )

    order_confirmed = state.get(
        "order_confirmed",
        False,
    )

    return (
        forced_destination == "order"
        or pending_action in {
            "ORDER_CONFIRMATION",
            "ORDER_CUSTOMER_NAME",
            "ORDER_CUSTOMER_DETAILS",
        }
        or (
            order_confirmed
            and pending_action in {
                "ORDER_CUSTOMER_NAME",
                "ORDER_CUSTOMER_DETAILS",
            }
        )
    )


# ============================================================
# ORDER CONTINUATION DETECTION
#
# IMPORTANT:
# An active order should only take priority when the new
# message is actually responding to the current order step.
#
# This allows questions such as:
#   "What are your payment methods?"
#   "What is your delivery policy?"
#   "Can you tell me about KenyaBiz?"
#
# to be answered without destroying the pending order.
# ============================================================

def is_order_continuation(
    state: KenyaBizState,
) -> bool:

    customer_message = state.get(
        "customer_message",
        "",
    )

    pending_action = state.get(
        "pending_action"
    )

    if not customer_message:
        return False

    normalized = re.sub(
        r"\s+",
        " ",
        customer_message.lower().strip(),
    )

    # --------------------------------------------------------
    # Confirmation stage
    # --------------------------------------------------------

    if pending_action == "ORDER_CONFIRMATION":

        if contains_confirmation(
            normalized
        ):
            return True

        if contains_order_decline(
            normalized
        ):
            return True

        # A new explicit order is a new order request.
        try:
            if is_explicit_order_request(
                normalized
            ):
                return True
        except Exception:
            pass

        return False

    # --------------------------------------------------------
    # Customer-name/details stage
    #
    # main.py normally extracts customer details before the
    # graph is called. These simple patterns provide a fallback.
    # --------------------------------------------------------

    if pending_action in {
        "ORDER_CUSTOMER_NAME",
        "ORDER_CUSTOMER_DETAILS",
    }:

        name_patterns = [
            r"^(?:my name is|name is|i am|i'm)\s+.+$",
            r"^this is\s+.+$",
        ]

        if any(
            re.match(
                pattern,
                normalized,
            )
            for pattern in name_patterns
        ):
            return True

        # If the message is short and does not look like a
        # separate business question, allow the Order Agent
        # to process it as customer information.
        question_terms = [
            "what",
            "how",
            "where",
            "when",
            "why",
            "which",
            "can you",
            "tell me",
            "do you",
            "does",
        ]

        if (
            len(normalized.split()) <= 4
            and not any(
                term in normalized
                for term in question_terms
            )
        ):
            return True

        return False

    return False


# ============================================================
# SUPERVISOR
# ============================================================

def supervisor_node(
    state: KenyaBizState,
):

    customer_message = state.get(
        "customer_message",
        "",
    )

    if not customer_message:
        return {
            "destination": "support",
            "routing_reason": (
                "No customer message provided."
            ),
        }

    pending_action = state.get(
        "pending_action"
    )

    forced_destination = state.get(
        "forced_destination"
    )

    # ========================================================
    # 1. EXPLICIT INVOICE
    # ========================================================

    if looks_like_invoice_request(
        customer_message
    ):
        return {
            "destination": "invoice",
            "routing_reason": (
                "Customer message explicitly "
                "requests an invoice, bill, or receipt."
            ),
        }

    # ========================================================
    # 2. EXPLICIT PAYMENT
    # ========================================================

    if looks_like_payment_request(
        customer_message
    ):
        return {
            "destination": "payment",
            "routing_reason": (
                "Customer message explicitly "
                "requests payment assistance."
            ),
        }

    # ========================================================
    # 3. CONTINUE INVOICE
    # ========================================================

    if pending_action == (
        "INVOICE_ORDER_REFERENCE"
    ):
        return {
            "destination": "invoice",
            "routing_reason": (
                "Continuing an invoice request "
                "awaiting an order reference."
            ),
        }

    # ========================================================
    # 4. CONTINUE PAYMENT REFERENCE
    # ========================================================

    if pending_action == (
        "PAYMENT_ORDER_REFERENCE"
    ):
        return {
            "destination": "payment",
            "routing_reason": (
                "Continuing a payment request "
                "awaiting an order reference."
            ),
        }

    # ========================================================
    # 5. CONTINUE PAYMENT
    # ========================================================

    if pending_action in {
        "PAYMENT_STATUS",
        "PAYMENT_COMPLETION",
    }:
        return {
            "destination": "payment",
            "routing_reason": (
                "Continuing an existing payment conversation."
            ),
        }

    # ========================================================
    # 6. ORDER REFERENCE + INVOICE
    # ========================================================

    order_reference = extract_order_reference(
        customer_message
    )

    if (
        order_reference
        and looks_like_invoice_request(
            customer_message
        )
    ):
        return {
            "destination": "invoice",
            "routing_reason": (
                "Message contains an order reference "
                "and an invoice request."
            ),
        }

    # ========================================================
    # 7. ORDER REFERENCE + PAYMENT
    # ========================================================

    if (
        order_reference
        and looks_like_payment_request(
            customer_message
        )
    ):
        return {
            "destination": "payment",
            "routing_reason": (
                "Message contains an order reference "
                "and a payment request."
            ),
        }

    # ========================================================
    # 8. EXPLICIT NEW ORDER
    #
    # IMPORTANT:
    # This must happen BEFORE quotation detection.
    # ========================================================

    try:

        if is_explicit_order_request(
            customer_message
        ):
            return {
                "destination": "order",
                "routing_reason": (
                    "Customer explicitly requested "
                    "to place or buy an order."
                ),
            }

    except Exception:
        pass

    # ========================================================
    # 9. CONTINUE ACTIVE ORDER
    #
    # Only continue the order if the current message actually
    # responds to the order step.
    # ========================================================

    if (
        has_active_order_flow(state)
        and is_order_continuation(state)
    ):
        return {
            "destination": "order",
            "routing_reason": (
                "Customer message continues "
                "the current order step."
            ),
        }

    # ========================================================
    # 10. FORCED DESTINATION
    #
    # Do not blindly force an unrelated question back into
    # the previous specialist conversation.
    # ========================================================

    if forced_destination:

        if forced_destination in {
            "invoice",
            "payment",
        }:
            if pending_action in {
                "INVOICE_ORDER_REFERENCE",
                "PAYMENT_ORDER_REFERENCE",
                "PAYMENT_STATUS",
                "PAYMENT_COMPLETION",
            }:
                return {
                    "destination": forced_destination,
                    "routing_reason": (
                        "Continuing the previous "
                        "invoice/payment workflow."
                    ),
                }

        elif forced_destination == "order":

            if is_order_continuation(state):
                return {
                    "destination": "order",
                    "routing_reason": (
                        "Continuing the current "
                        "order workflow."
                    ),
                }

    # ========================================================
    # 11. STOCK / AVAILABILITY
    #
    # This is BEFORE quotation.
    # ========================================================

    if is_stock_request(
        customer_message
    ):
        return {
            "destination": "sales",
            "routing_reason": (
                "Message explicitly asks about "
                "product stock or availability."
            ),
        }

    # ========================================================
    # 12. IMPLICIT QUOTATION
    # ========================================================

    if looks_like_quotation_request(
        customer_message
    ):
        return {
            "destination": "sales",
            "routing_reason": (
                "Message contains product quantities "
                "and appears to request pricing."
            ),
        }

    # ========================================================
    # 13. NORMAL SUPERVISOR
    # ========================================================

    try:

        routing_result = route_customer_request(
            customer_message
        )

        destination = routing_result.get(
            "destination",
            "support",
        )

        reasoning = routing_result.get(
            "reasoning",
            "",
        )

        if destination not in VALID_DESTINATIONS:
            destination = "support"
            reasoning = (
                "Supervisor returned an invalid "
                "destination; using support."
            )

        return {
            "destination": destination,
            "routing_reason": reasoning,
        }

    except Exception as exc:

        print()
        print("SUPERVISOR ERROR:")
        print(exc)

        return {
            "destination": "support",
            "routing_reason": (
                "Supervisor routing failed; "
                "falling back to support."
            ),
        }


# ============================================================
# SUPPORT NODE
# ============================================================

def support_node(
    state: KenyaBizState,
):

    customer_message = state.get(
        "customer_message",
        "",
    )

    result = get_support_response(
        customer_message
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # Preserve any pending order workflow.
    #
    # The customer may ask a support question while an order
    # is waiting for confirmation or customer details.
    # --------------------------------------------------------

    return {
        "response": result.get(
            "answer",
            "I could not prepare a response.",
        ),
        "status": "COMPLETED",

        # Do NOT clear pending order information here.
        "pending_request": state.get(
            "pending_request"
        ),
        "pending_action": state.get(
            "pending_action"
        ),
        "forced_destination": state.get(
            "forced_destination"
        ),

        "order_confirmed": state.get(
            "order_confirmed",
            False,
        ),
        "order_reference": state.get(
            "order_reference"
        ),
        "order_status": state.get(
            "order_status"
        ),

        "invoice_path": state.get(
            "invoice_path"
        ),
        "payment_reference": state.get(
            "payment_reference"
        ),
        "payment_status": state.get(
            "payment_status"
        ),
    }


# ============================================================
# SALES NODE
# ============================================================

def sales_node(
    state: KenyaBizState,
):

    customer_message = state.get(
        "customer_message",
        "",
    )

    result = process_sales_request(
        customer_message
    )

    response = result.get(
        "response",
        "I could not prepare a sales response.",
    )

    sales_status = result.get(
        "status"
    )

    # IMPORTANT:
    # Never treat stock checking as an order quotation.
    stock_request = is_stock_request(
        customer_message
    )

    quotation_created = (
        looks_like_quotation_request(
            customer_message
        )
        and not stock_request
    )

    waiting_for_confirmation = (
        sales_status
        in {
            "AWAITING_CONFIRMATION",
            "QUOTE_READY",
            "QUOTATION_READY",
            "PENDING_CONFIRMATION",
        }
    )

    if (
        quotation_created
        or (
            waiting_for_confirmation
            and not stock_request
        )
    ):
        return {
            "response": response,
            "status": "WAITING",
            "pending_request": customer_message,
            "pending_action": (
                "ORDER_CONFIRMATION"
            ),
            "forced_destination": "order",
            "order_confirmed": False,
        }

    return {
        "response": response,
        "status": "COMPLETED",
        "pending_request": None,
        "pending_action": None,
        "forced_destination": None,
    }


# ============================================================
# ORDER NODE
# ============================================================

def order_node(
    state: KenyaBizState,
):

    customer_message = state.get(
        "customer_message",
        "",
    )

    existing_pending_request = state.get(
        "pending_request"
    )

    pending_action = state.get(
        "pending_action"
    )

    order_confirmed = state.get(
        "order_confirmed",
        False,
    )

    confirmed = (
        order_confirmed
        or pending_action in {
            "ORDER_CUSTOMER_NAME",
            "ORDER_CUSTOMER_DETAILS",
        }
        or (
            bool(existing_pending_request)
            and contains_confirmation(
                customer_message
            )
        )
    )

    # ========================================================
    # NEW ORDER / QUOTATION
    # ========================================================

    if (
        not existing_pending_request
        and not confirmed
    ):

        result = process_order(
            customer_message,
            confirmed=False,
            pending_request=None,
        )

        response = format_order_response(
            result
        )

        if result.get("status") == (
            "AWAITING_CONFIRMATION"
        ):
            return {
                "response": response,
                "status": "WAITING",
                "pending_request": customer_message,
                "pending_action": (
                    "ORDER_CONFIRMATION"
                ),
                "forced_destination": "order",
                "order_confirmed": False,
                "order_status": "PENDING",
            }

        return {
            "response": response,
            "status": "ERROR",
            "pending_request": customer_message,
            "pending_action": None,
            "forced_destination": None,
            "order_confirmed": False,
            "order_status": result.get(
                "status"
            ),
        }

    # ========================================================
    # CONTINUE ORDER
    # ========================================================

    result = process_order(
        customer_message,
        confirmed=confirmed,
        pending_request=existing_pending_request,
    )

    response = format_order_response(
        result
    )

    order_reference = result.get(
        "order_reference"
    )

    if not order_reference:

        order_data = result.get(
            "order"
        )

        if isinstance(
            order_data,
            dict,
        ):
            order_reference = order_data.get(
                "order_reference"
            )

    order_status = result.get(
        "status"
    )

    # ========================================================
    # CUSTOMER DETAILS REQUIRED
    # ========================================================

    if order_status == (
        "CUSTOMER_DETAILS_REQUIRED"
    ):
        return {
            "response": response,
            "status": "WAITING",
            "pending_request": (
                existing_pending_request
            ),
            "pending_action": (
                "ORDER_CUSTOMER_NAME"
            ),
            "forced_destination": "order",
            "order_confirmed": True,
            "order_reference": order_reference,
            "order_status": (
                "CUSTOMER_DETAILS_REQUIRED"
            ),
        }

    # ========================================================
    # ORDER STILL WAITING
    # ========================================================

    waiting_statuses = {
        "AWAITING_CONFIRMATION",
        "AMBIGUOUS_PRODUCT",
        "PRODUCT_NOT_FOUND",
        "INSUFFICIENT_STOCK",
    }

    if order_status in waiting_statuses:

        return {
            "response": response,
            "status": "WAITING",
            "pending_request": (
                existing_pending_request
                or customer_message
            ),
            "pending_action": (
                "ORDER_CONFIRMATION"
            ),
            "forced_destination": "order",
            "order_confirmed": confirmed,
            "order_reference": order_reference,
            "order_status": order_status,
        }

    # ========================================================
    # SUCCESS
    # ========================================================

    if order_status == "SUCCESS":

        return {
            "response": response,
            "status": "COMPLETED",
            "pending_request": None,
            "pending_action": None,
            "forced_destination": None,
            "order_confirmed": True,
            "order_reference": order_reference,
            "order_status": "CONFIRMED",
        }

    # ========================================================
    # ERROR
    # ========================================================

    return {
        "response": response,
        "status": "ERROR",
        "pending_request": (
            existing_pending_request
        ),
        "pending_action": pending_action,
        "forced_destination": None,
        "order_confirmed": confirmed,
        "order_reference": order_reference,
        "order_status": order_status,
    }


# ============================================================
# INVOICE NODE
# ============================================================

def invoice_node(
    state: KenyaBizState,
):

    customer_message = state.get(
        "customer_message",
        "",
    )

    order_reference = extract_order_reference(
        customer_message
    )

    if not order_reference:
        order_reference = state.get(
            "order_reference"
        )

    if not order_reference:

        return {
            "response": (
                "I can help generate the invoice. "
                "Please provide your KenyaBiz order "
                "reference, for example "
                "KBA-20260925-P5EP."
            ),
            "status": "WAITING",
            "pending_action": (
                "INVOICE_ORDER_REFERENCE"
            ),
            "forced_destination": "invoice",
        }

    result = process_invoice_request(
        order_reference
    )

    response = format_invoice_response(
        result
    )

    invoice_status = result.get(
        "status"
    )

    if invoice_status not in {
        "SUCCESS",
        "COMPLETED",
        None,
    }:

        return {
            "response": response,
            "status": "ERROR",
            "order_reference": order_reference,
            "invoice_path": result.get(
                "invoice_path"
            ),
            "pending_action": (
                "INVOICE_ORDER_REFERENCE"
            ),
            "forced_destination": "invoice",
        }

    return {
        "response": response,
        "status": "COMPLETED",
        "order_reference": order_reference,
        "invoice_path": result.get(
            "invoice_path"
        ),
        "pending_action": None,
        "forced_destination": None,
    }


# ============================================================
# PAYMENT NODE
# ============================================================

def payment_node(
    state: KenyaBizState,
):

    customer_message = state.get(
        "customer_message",
        "",
    )

    order_reference = extract_order_reference(
        customer_message
    )

    payment_reference = extract_payment_reference(
        customer_message
    )

    # ========================================================
    # RESTORE SAVED REFERENCES
    # ========================================================

    if not order_reference:
        order_reference = state.get(
            "order_reference"
        )

    if not payment_reference:
        payment_reference = state.get(
            "payment_reference"
        )

    # ========================================================
    # EXISTING PAYMENT REFERENCE
    # ========================================================

    if payment_reference:

        normalized_message = (
            customer_message.lower()
        )

        completion_phrases = [
            "complete payment",
            "confirm payment",
            "i have paid",
            "payment made",
            "mark as paid",
            "i paid",
            "payment completed",
            "paid already",
        ]

        payment_completion_requested = any(
            phrase in normalized_message
            for phrase in completion_phrases
        )

        # ====================================================
        # COMPLETE PAYMENT
        # ====================================================

        if payment_completion_requested:

            result = process_payment_completion(
                payment_reference
            )

            response = format_payment_completion(
                result
            )

            payment_status = result.get(
                "status"
            )

            payment_data = result.get(
                "payment"
            )

            if isinstance(
                payment_data,
                dict,
            ):
                payment_status = payment_data.get(
                    "payment_status",
                    payment_status,
                )

            return {
                "response": response,
                "status": "COMPLETED",
                "payment_reference": (
                    payment_reference
                ),
                "payment_status": payment_status,
                "order_reference": order_reference,
                "pending_action": None,
                "forced_destination": None,
            }

        # ====================================================
        # CHECK PAYMENT STATUS
        # ====================================================

        result = check_payment_status(
            payment_reference
        )

        response = format_payment_status(
            result
        )

        payment_status = result.get(
            "status"
        )

        payment_data = result.get(
            "payment"
        )

        if isinstance(
            payment_data,
            dict,
        ):
            payment_status = payment_data.get(
                "payment_status",
                payment_status,
            )

        return {
            "response": response,
            "status": "COMPLETED",
            "payment_reference": (
                payment_reference
            ),
            "payment_status": payment_status,
            "order_reference": order_reference,
            "pending_action": None,
            "forced_destination": None,
        }

    # ========================================================
    # ORDER REFERENCE AVAILABLE
    # ========================================================

    if order_reference:

        result = process_payment_request(
            order_reference
        )

        response = format_payment_request(
            result
        )

        payment_reference = result.get(
            "payment_reference"
        )

        payment_status = result.get(
            "status"
        )

        payment_data = result.get(
            "payment"
        )

        if isinstance(
            payment_data,
            dict,
        ):

            payment_reference = payment_data.get(
                "payment_reference",
                payment_reference,
            )

            payment_status = payment_data.get(
                "payment_status",
                payment_status,
            )

        return {
            "response": response,
            "status": "COMPLETED",
            "order_reference": order_reference,
            "payment_reference": (
                payment_reference
            ),
            "payment_status": payment_status,
            "pending_action": None,
            "forced_destination": None,
        }

    # ========================================================
    # NEED ORDER REFERENCE
    # ========================================================

    return {
        "response": (
            "I can help you with the payment. "
            "Please provide your KenyaBiz order "
            "reference, for example "
            "KBA-20260925-P5EP."
        ),
        "status": "WAITING",
        "pending_action": (
            "PAYMENT_ORDER_REFERENCE"
        ),
        "forced_destination": "payment",
    }


# ============================================================
# ROUTER
# ============================================================

def specialist_router(
    state: KenyaBizState,
):

    destination = state.get(
        "destination",
        "support",
    )

    return {
        "support": "support",
        "sales": "sales",
        "order": "order",
        "invoice": "invoice",
        "payment": "payment",
    }.get(
        destination,
        "support",
    )


# ============================================================
# BUILD GRAPH
# ============================================================

def build_graph():

    graph = StateGraph(
        KenyaBizState
    )

    graph.add_node(
        "supervisor",
        supervisor_node,
    )

    graph.add_node(
        "support",
        support_node,
    )

    graph.add_node(
        "sales",
        sales_node,
    )

    graph.add_node(
        "order",
        order_node,
    )

    graph.add_node(
        "invoice",
        invoice_node,
    )

    graph.add_node(
        "payment",
        payment_node,
    )

    graph.add_edge(
        START,
        "supervisor",
    )

    graph.add_conditional_edges(
        "supervisor",
        specialist_router,
        {
            "support": "support",
            "sales": "sales",
            "order": "order",
            "invoice": "invoice",
            "payment": "payment",
        },
    )

    graph.add_edge(
        "support",
        END,
    )

    graph.add_edge(
        "sales",
        END,
    )

    graph.add_edge(
        "order",
        END,
    )

    graph.add_edge(
        "invoice",
        END,
    )

    graph.add_edge(
        "payment",
        END,
    )

    return graph.compile()


app = build_graph()


# ============================================================
# PUBLIC GRAPH FUNCTION
# ============================================================

def run_kenyabiz(
    customer_message: str,
    forced_destination: Optional[str] = None,
    conversation_history=None,
    pending_request=None,
    order_confirmed=False,
    pending_action=None,
    order_reference=None,
    order_status=None,
    invoice_path=None,
    payment_reference=None,
    payment_status=None,
):

    initial_state = {
        "customer_message": customer_message,
        "conversation_history": (
            conversation_history or []
        ),
        "forced_destination": (
            forced_destination
        ),
        "pending_request": (
            pending_request
        ),
        "pending_action": (
            pending_action
        ),
        "order_confirmed": (
            order_confirmed
        ),
        "order_reference": (
            order_reference
        ),
        "order_status": (
            order_status
        ),
        "invoice_path": (
            invoice_path
        ),
        "payment_reference": (
            payment_reference
        ),
        "payment_status": (
            payment_status
        ),
    }

    return app.invoke(
        initial_state
    )