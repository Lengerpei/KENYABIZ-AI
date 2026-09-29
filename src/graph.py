import re
from typing import Optional

from langgraph.graph import StateGraph, START, END

from src.state import KenyaBizState

from src.agents.supervisor import route_customer_request

from src.agents.support_agent import (
    get_support_response,
)

from src.agents.sales_agent import (
    process_sales_request,
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
# ROUTING DESTINATIONS
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

def extract_order_reference(text: str) -> Optional[str]:
    if not text:
        return None

    match = re.search(
        r"\bKBA-\d{8}-[A-Z0-9]+\b",
        text.upper(),
    )

    return match.group(0) if match else None


def extract_payment_reference(text: str) -> Optional[str]:
    if not text:
        return None

    match = re.search(
        r"\bMPS[A-Z0-9]+\b",
        text.upper(),
    )

    return match.group(0) if match else None


# ============================================================
# CONFIRMATION DETECTION
# ============================================================

def contains_confirmation(text: str) -> bool:
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
# QUOTATION DETECTION
# ============================================================

def looks_like_quotation_request(text: str) -> bool:
    """
    Detect implicit quotation requests such as:

        I need 5 office chairs and 2 office desks
        How much would 5 chairs and 2 desks cost?
        Give me prices for 5 chairs and 2 desks
        I need a quote for 5 chairs

    This prevents these requests from being treated as
    generic product searches.
    """

    if not text:
        return False

    normalized = text.lower().strip()

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
# ORDER-CONVERSATION DETECTION
# ============================================================

def has_active_order_flow(
    state: KenyaBizState,
) -> bool:
    """
    Determine whether the customer is already inside
    an order conversation.
    """

    pending_action = state.get(
        "pending_action"
    )

    pending_request = state.get(
        "pending_request"
    )

    forced_destination = state.get(
        "forced_destination"
    )

    return (
        forced_destination == "order"
        or pending_action in {
            "ORDER_CONFIRMATION",
            "ORDER_CUSTOMER_NAME",
            "ORDER_CUSTOMER_DETAILS",
        }
        or bool(pending_request)
    )


# ============================================================
# SUPERVISOR NODE
# ============================================================

def supervisor_node(state: KenyaBizState):

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
    # 1. CONTINUE ACTIVE ORDER
    # ========================================================

    if has_active_order_flow(state):

        return {
            "destination": "order",
            "routing_reason": (
                "Continuing an active order conversation."
            ),
        }

    # ========================================================
    # 2. CONTINUE OTHER FORCED DESTINATION
    # ========================================================

    if forced_destination:

        if forced_destination in VALID_DESTINATIONS:

            return {
                "destination": forced_destination,
                "routing_reason": (
                    "Continuing the previous specialist "
                    "conversation."
                ),
            }

    # ========================================================
    # 3. IMPLICIT QUOTATION
    # ========================================================

    if looks_like_quotation_request(
        customer_message
    ):

        return {
            "destination": "sales",
            "routing_reason": (
                "Message contains product quantities "
                "and appears to request pricing or "
                "a quotation."
            ),
        }

    # ========================================================
    # 4. NORMAL SUPERVISOR
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

def support_node(state: KenyaBizState):

    customer_message = state.get(
        "customer_message",
        "",
    )

    result = get_support_response(
        customer_message
    )

    return {
        "response": result.get(
            "answer",
            "I could not prepare a response.",
        ),
        "status": "COMPLETED",
        "pending_request": None,
        "pending_action": None,
        "forced_destination": None,
    }


# ============================================================
# SALES NODE
# ============================================================

def sales_node(state: KenyaBizState):

    customer_message = state.get(
        "customer_message",
        "",
    )

    result = process_sales_request(
        customer_message
    )

    return {
        "response": result.get(
            "response",
            "I could not prepare a sales response.",
        ),
        "status": "COMPLETED",
        "pending_request": None,
        "pending_action": None,
        "forced_destination": None,
    }


# ============================================================
# ORDER NODE
# ============================================================

def order_node(state: KenyaBizState):

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

    # ========================================================
    # DETERMINE WHETHER THIS IS A CONFIRMATION
    # ========================================================

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
    # FIRST ORDER MESSAGE
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
                "pending_request": (
                    customer_message
                ),
                "pending_action": (
                    "ORDER_CONFIRMATION"
                ),
                "forced_destination": "order",
                "order_confirmed": False,
                "order_status": (
                    "PENDING"
                ),
            }

    # ========================================================
    # CONTINUE EXISTING ORDER
    # ========================================================

    result = process_order(
        customer_message,
        confirmed=confirmed,
        pending_request=existing_pending_request,
    )

    response = format_order_response(
        result
    )

    # ========================================================
    # ORDER REFERENCE
    # ========================================================

    order_reference = result.get(
        "order_reference"
    )

    if not order_reference:

        order_data = result.get(
            "order"
        )

        if isinstance(order_data, dict):

            order_reference = order_data.get(
                "order_reference"
            )

    # ========================================================
    # ORDER STATUS
    # ========================================================

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
    # OTHER WAITING STATES
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
            "order_confirmed": (
                confirmed
            ),
            "order_reference": order_reference,
            "order_status": order_status,
        }

    # ========================================================
    # ORDER CREATED SUCCESSFULLY
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
        "pending_request": existing_pending_request,
        "pending_action": pending_action,
        "forced_destination": "order",
        "order_confirmed": confirmed,
        "order_reference": order_reference,
        "order_status": order_status,
    }


# ============================================================
# INVOICE NODE
# ============================================================

def invoice_node(state: KenyaBizState):

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

def payment_node(state: KenyaBizState):

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

    if not order_reference:

        order_reference = state.get(
            "order_reference"
        )

    if not payment_reference:

        payment_reference = state.get(
            "payment_reference"
        )

    # ========================================================
    # PAYMENT REFERENCE EXISTS
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

        # ----------------------------------------------------
        # COMPLETE PAYMENT
        # ----------------------------------------------------

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

                payment_status = (
                    payment_data.get(
                        "payment_status",
                        payment_status,
                    )
                )

            return {
                "response": response,
                "status": "COMPLETED",
                "payment_reference": (
                    payment_reference
                ),
                "payment_status": (
                    payment_status
                ),
                "order_reference": (
                    order_reference
                ),
                "pending_action": None,
                "forced_destination": None,
            }

        # ----------------------------------------------------
        # CHECK PAYMENT STATUS
        # ----------------------------------------------------

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

            payment_status = (
                payment_data.get(
                    "payment_status",
                    payment_status,
                )
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
    # CREATE PAYMENT REQUEST
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

            payment_reference = (
                payment_data.get(
                    "payment_reference",
                    payment_reference,
                )
            )

            payment_status = (
                payment_data.get(
                    "payment_status",
                    payment_status,
                )
            )

        return {
            "response": response,
            "status": "COMPLETED",
            "order_reference": order_reference,
            "payment_reference": payment_reference,
            "payment_status": payment_status,
            "pending_action": None,
            "forced_destination": None,
        }

    # ========================================================
    # NO ORDER REFERENCE
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
# SPECIALIST ROUTER
# ============================================================

def specialist_router(state: KenyaBizState):

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


# ============================================================
# COMPILED APPLICATION
# ============================================================

app = build_graph()


# ============================================================
# MAIN RUNNER
# ============================================================

def run_kenyabiz(
    customer_message: str,
    forced_destination: Optional[str] = None,
    conversation_history=None,
    pending_request=None,
    order_confirmed=False,
    pending_action=None,
):
    """
    Run KenyaBiz AI for one conversational turn.

    The caller must pass the state returned from the
    previous turn when using this runner.
    """

    initial_state = {
        "customer_message": customer_message,
        "forced_destination": forced_destination,
        "conversation_history": (
            conversation_history or []
        ),
        "pending_request": pending_request,
        "order_confirmed": order_confirmed,
        "pending_action": pending_action,
    }

    return app.invoke(
        initial_state
    )