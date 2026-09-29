import json
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field


# ============================================================
# KENYABIZ AI
# SUPERVISOR AGENT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


# ============================================================
# LLM CONFIGURATION
# ============================================================

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)


# ============================================================
# ROUTING DESTINATIONS
# ============================================================

RoutingDestination = Literal[
    "support",
    "sales",
    "order",
    "invoice",
    "payment",
]


# ============================================================
# ROUTING MODEL
# ============================================================

class SupervisorDecision(BaseModel):
    """
    Structured decision produced by the Supervisor Agent.
    """

    destination: RoutingDestination = Field(
        description=(
            "The single specialist agent that should "
            "handle the customer's request."
        )
    )

    reasoning: str = Field(
        description=(
            "Brief explanation of why the request "
            "belongs to the selected specialist."
        )
    )


# ============================================================
# STRUCTURED LLM
# ============================================================

structured_llm = llm.with_structured_output(
    SupervisorDecision
)


# ============================================================
# ROUTING FUNCTION
# ============================================================

def route_customer_request(
    customer_message: str
):
    """
    Route a customer request to exactly one
    KenyaBiz specialist agent.
    """

    if not customer_message or not customer_message.strip():

        return {
            "status": "ERROR",
            "message": (
                "Please provide a customer request."
            )
        }

    prompt = f"""
You are the Supervisor Agent for KenyaBiz AI.

KenyaBiz AI is a fictional Kenyan SME business
assistant.

Your ONLY responsibility is to determine which
specialist agent should handle the customer's request.

Do NOT answer the customer.
Do NOT perform the task.
Do NOT create an order.
Do NOT generate an invoice.
Do NOT create a payment.

Choose exactly ONE specialist.

============================================================
AVAILABLE SPECIALISTS
============================================================

1. SUPPORT

Use SUPPORT for informational questions.

Examples:

- What does KenyaBiz AI do?
- Where is KenyaBiz located?
- What services do you provide?
- How long does delivery take?
- What is your delivery policy?
- What payment methods do you support?
- Can I pay using M-Pesa?
- How do I pay?
- Do you provide invoices?
- What is your refund policy?
- How can I contact you?
- What are your business hours?

IMPORTANT:

Questions ABOUT payment policy or payment methods
belong to SUPPORT.

Questions ABOUT invoices as a general capability
belong to SUPPORT.

Questions ABOUT delivery policy belong to SUPPORT.

============================================================
2. SALES
============================================================

Use SALES when the customer is asking about:

- Products
- Prices
- Product availability
- Product recommendations
- Product comparisons
- Quotations
- Estimated prices

Examples:

- How much is an office chair?
- How much are five office chairs?
- Do you have office desks?
- Which chair would you recommend?
- Give me a quotation for five chairs.

The customer is asking about buying,
but has NOT yet explicitly asked to create/place an order.

============================================================
3. ORDER
============================================================

Use ORDER when the customer wants to CREATE,
PLACE, or CONFIRM an order.

Examples:

- I want to order 5 chairs.
- Place an order for me.
- I want to buy two desks.
- Create an order for 10 chairs.
- Confirm my order.
- Go ahead with the order.

IMPORTANT:

If the customer explicitly wants to create or place
an order, choose ORDER even if prices or products
are mentioned.

============================================================
4. INVOICE
============================================================

Use INVOICE when the customer wants an actual invoice
to be generated, retrieved, or produced for an order.

Examples:

- Generate an invoice for KBA-20260925-P5EP.
- Create my invoice.
- Generate the invoice for my order.
- I need the invoice for KBA-20260925-P5EP.

However:

"Do you provide invoices?"

"What is your invoice policy?"

"Can I get an invoice?"

are informational questions and should normally
go to SUPPORT unless the customer clearly asks
to generate/retrieve a specific invoice.

============================================================
5. PAYMENT
============================================================

Use PAYMENT when the customer wants to perform,
check, or complete a payment transaction.

Examples:

- Create a payment request for KBA-20260925-P5EP.
- Send me the payment request.
- Check payment MPSABC123456.
- Has payment MPSABC123456 gone through?
- I have paid using MPSABC123456.
- Complete my payment.

IMPORTANT:

General questions about payment methods belong to SUPPORT.

For example:

"What payment methods do you support?"

"Can I pay using M-Pesa?"

"How do I pay?"

These are SUPPORT questions.

============================================================
ROUTING PRIORITY
============================================================

Use these rules in order:

1. Explicit order creation/confirmation
   → ORDER

2. Actual invoice generation/retrieval
   → INVOICE

3. Actual payment transaction/status/completion
   → PAYMENT

4. Product, price, stock, recommendation, quotation
   → SALES

5. General information, policies, FAQs
   → SUPPORT

============================================================
CUSTOMER REQUEST
============================================================

{customer_message}
"""

    try:

        decision = structured_llm.invoke(
            prompt
        )

        return {
            "status": "SUCCESS",
            "destination": decision.destination,
            "reasoning": decision.reasoning,
            "customer_message": customer_message,
        }

    except Exception as error:

        return {
            "status": "ERROR",
            "message": (
                f"Unable to route customer request: "
                f"{error}"
            )
        }


# ============================================================
# FORMAT RESULT
# ============================================================

def format_routing_result(result):

    if result["status"] != "SUCCESS":

        return (
            "Supervisor could not route the request.\n\n"
            + result["message"]
        )

    return "\n".join([
        "Supervisor decision:",
        "",
        f"Destination: {result['destination']}",
        f"Reason: {result['reasoning']}",
    ])


# ============================================================
# TESTS
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("KENYABIZ AI")
    print("SUPERVISOR AGENT TEST")
    print("=" * 70)

    test_requests = [

        # SUPPORT
        (
            "SUPPORT",
            "Where is KenyaBiz AI located?"
        ),

        (
            "SUPPORT",
            "What payment methods do you support?"
        ),

        (
            "SUPPORT",
            "Can I pay using M-Pesa?"
        ),

        (
            "SUPPORT",
            "How long does delivery take?"
        ),

        (
            "SUPPORT",
            "Do you provide invoices?"
        ),

        # SALES
        (
            "SALES",
            "How much does an office chair cost?"
        ),

        (
            "SALES",
            "How much would 5 office chairs cost?"
        ),

        (
            "SALES",
            "Do you have office desks?"
        ),

        # ORDER
        (
            "ORDER",
            "I want to order 5 office chairs."
        ),

        (
            "ORDER",
            "Please place an order for 2 office desks."
        ),

        (
            "ORDER",
            "I want to buy 2 desks."
        ),

        # INVOICE
        (
            "INVOICE",
            "Generate an invoice for KBA-20260925-P5EP."
        ),

        (
            "INVOICE",
            "Create my invoice for KBA-20260925-P5EP."
        ),

        # PAYMENT
        (
            "PAYMENT",
            "Create a payment request for KBA-20260925-P5EP."
        ),

        (
            "PAYMENT",
            "Check payment MPSABC123456."
        ),

        (
            "PAYMENT",
            "I have paid using MPSABC123456."
        ),
    ]

    passed = 0

    for number, (expected, request) in enumerate(
        test_requests,
        start=1
    ):

        print("\n" + "=" * 70)
        print(f"TEST {number}")
        print("=" * 70)

        print(f"\nCustomer:")
        print(request)

        result = route_customer_request(
            request
        )

        print("\nRaw result:")

        print(
            json.dumps(
                result,
                indent=2,
                default=str
            )
        )

        print("\nFormatted result:")

        print(
            format_routing_result(
                result
            )
        )

        actual = result.get(
            "destination"
        )

        print(
            f"\nExpected: {expected}"
        )

        print(
            f"Actual:   {actual}"
        )

        if actual == expected:

            print("Routing result: PASS")
            passed += 1

        else:

            print("Routing result: REVIEW")

    print("\n" + "=" * 70)

    print(
        f"SUPERVISOR TESTS: "
        f"{passed}/{len(test_requests)} passed"
    )

    print("=" * 70)