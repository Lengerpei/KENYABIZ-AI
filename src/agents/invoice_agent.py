import json
from pathlib import Path

from src.tools.invoice_tool import generate_invoice
from src.tools.order_tool import get_order


# ============================================================
# INVOICE AGENT
# ============================================================

def process_invoice_request(order_reference):
    """
    Generate an invoice for an existing order.

    The Invoice Agent:
    1. Validates the order reference.
    2. Checks that the order exists.
    3. Calls the invoice tool.
    4. Returns invoice information.
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

        order_reference = order_reference.strip().upper()

        # ----------------------------------------------------
        # 2. Check whether the order exists
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
        # 3. Generate the invoice
        # ----------------------------------------------------
        invoice_result = generate_invoice(order_reference)

        # ----------------------------------------------------
        # 4. Handle different possible return formats
        # ----------------------------------------------------
        if isinstance(invoice_result, dict):

            if invoice_result.get("status") == "ERROR":
                return {
                    "status": "ERROR",
                    "message": invoice_result.get(
                        "message",
                        "Unable to generate the invoice."
                    )
                }

            invoice_path = (
                invoice_result.get("invoice_path")
                or invoice_result.get("file_path")
                or invoice_result.get("path")
            )

        else:
            invoice_path = str(invoice_result)

        # ----------------------------------------------------
        # 5. Make sure we received an invoice path
        # ----------------------------------------------------
        if not invoice_path:
            return {
                "status": "ERROR",
                "message": "The invoice was generated but no file path was returned."
            }

        # ----------------------------------------------------
        # 6. Return successful result
        # ----------------------------------------------------
        return {
            "status": "SUCCESS",
            "message": "Invoice generated successfully.",
            "order_reference": order_reference,
            "invoice_path": invoice_path,
            "order": order
        }

    except Exception as error:
        return {
            "status": "ERROR",
            "message": f"Unable to generate invoice: {error}"
        }


# ============================================================
# FORMAT INVOICE RESPONSE
# ============================================================

def format_invoice_response(result):
    """
    Convert the Invoice Agent result into a user-friendly message.
    """

    if result["status"] == "NOT_FOUND":
        return result["message"]

    if result["status"] != "SUCCESS":
        return (
            "I could not generate the invoice.\n\n"
            + result["message"]
        )

    order = result["order"]

    lines = [
        "Invoice generated successfully.",
        "",
        f"Order reference: {result['order_reference']}",
        f"Customer: {order['customer_name']}",
        "",
        "Order summary:"
    ]

    for item in order["items"]:

        line_total = item.get(
            "line_total",
            item.get("total_price", 0)
        )

        lines.append(
            f"- {item['product_name']} x {item['quantity']}: "
            f"KES {line_total:,.2f}"
        )

    lines.extend([
        "",
        f"Subtotal: KES {order['subtotal']:,.2f}",
        f"Delivery fee: KES {order['delivery_fee']:,.2f}",
        f"Total: KES {order['total']:,.2f}",
        "",
        f"Invoice file: {result['invoice_path']}"
    ])

    return "\n".join(lines)


# ============================================================
# TESTS
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("KENYABIZ AI")
    print("INVOICE AGENT TEST")
    print("=" * 70)

    # --------------------------------------------------------
    # TEST 1: Generate invoice for existing order
    # --------------------------------------------------------

    print("\nTEST 1: GENERATE INVOICE")
    print("-" * 70)

    test_order_reference = "KBA-20260925-P5EP"

    result = process_invoice_request(
        test_order_reference
    )

    print("\nRaw result:")

    print(
        json.dumps(
            result,
            indent=2,
            default=str
        )
    )

    print("\nFormatted response:")
    print(format_invoice_response(result))

    # --------------------------------------------------------
    # TEST 2: Invalid order reference
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TEST 2: INVALID ORDER REFERENCE")
    print("-" * 70)

    invalid_result = process_invoice_request(
        "KBA-INVALID-1234"
    )

    print(
        json.dumps(
            invalid_result,
            indent=2,
            default=str
        )
    )

    print("\nFormatted response:")
    print(format_invoice_response(invalid_result))

    print("\n" + "=" * 70)
    print("INVOICE AGENT TESTS COMPLETE")
    print("=" * 70)