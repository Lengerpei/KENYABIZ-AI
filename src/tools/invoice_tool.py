from pathlib import Path
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from src.database.database import initialize_database
from src.tools.order_tool import get_order


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INVOICE_DIRECTORY = PROJECT_ROOT / "invoices"

INVOICE_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# COMPANY INFORMATION
# ============================================================

COMPANY_NAME = "KenyaBiz AI"

COMPANY_DESCRIPTION = (
    "Multi-Agent Business Assistant for Kenyan SMEs"
)

COMPANY_PHONE = "+254 700 000 000"

COMPANY_EMAIL = "info@kenyabiz.ai"

COMPANY_LOCATION = "Nairobi, Kenya"


# ============================================================
# GENERATE INVOICE
# ============================================================

def generate_invoice(order_reference):
    """
    Generate a PDF invoice for an existing order.

    Parameters
    ----------
    order_reference : str
        Example: KBA-20260925-AB12

    Returns
    -------
    dict
        Invoice generation result.
    """

    # --------------------------------------------------------
    # Retrieve order
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
    # Invoice filename
    # --------------------------------------------------------

    invoice_filename = (
        f"invoice_{order_reference}.pdf"
    )

    invoice_path = (
        INVOICE_DIRECTORY / invoice_filename
    )

    # --------------------------------------------------------
    # PDF document
    # --------------------------------------------------------

    document = SimpleDocTemplate(
        str(invoice_path),
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    # --------------------------------------------------------
    # Styles
    # --------------------------------------------------------

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Title"],
        fontSize=22,
        leading=26,
        alignment=TA_CENTER,
        spaceAfter=10,
    )

    company_style = ParagraphStyle(
        "CompanyStyle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
    )

    heading_style = ParagraphStyle(
        "HeadingStyle",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        spaceBefore=10,
        spaceAfter=6,
    )

    normal_style = ParagraphStyle(
        "NormalCustom",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
    )

    right_style = ParagraphStyle(
        "RightStyle",
        parent=normal_style,
        alignment=TA_RIGHT,
    )

    # --------------------------------------------------------
    # Build PDF content
    # --------------------------------------------------------

    elements = []

    # Company header
    elements.append(
        Paragraph(
            COMPANY_NAME,
            title_style
        )
    )

    elements.append(
        Paragraph(
            COMPANY_DESCRIPTION,
            company_style
        )
    )

    elements.append(
        Paragraph(
            f"{COMPANY_LOCATION} | "
            f"{COMPANY_PHONE} | "
            f"{COMPANY_EMAIL}",
            company_style
        )
    )

    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(
            "INVOICE",
            title_style
        )
    )

    # --------------------------------------------------------
    # Invoice information
    # --------------------------------------------------------

    invoice_date = datetime.now().strftime(
        "%d %B %Y"
    )

    invoice_information = [
        [
            Paragraph(
                f"<b>Invoice Reference:</b><br/>"
                f"{order_reference}",
                normal_style
            ),
            Paragraph(
                f"<b>Invoice Date:</b><br/>"
                f"{invoice_date}",
                normal_style
            ),
        ],
        [
            Paragraph(
                f"<b>Order Status:</b><br/>"
                f"{order['status']}",
                normal_style
            ),
            Paragraph(
                f"<b>Customer:</b><br/>"
                f"{order['customer_name']}",
                normal_style
            ),
        ],
    ]

    invoice_info_table = Table(
        invoice_information,
        colWidths=[250, 250]
    )

    invoice_info_table.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),
            ]
        )
    )

    elements.append(invoice_info_table)

    # --------------------------------------------------------
    # Customer details
    # --------------------------------------------------------

    elements.append(
        Paragraph(
            "Customer Details",
            heading_style
        )
    )

    customer_details = [
        [
            Paragraph(
                "<b>Name</b>",
                normal_style
            ),
            Paragraph(
                order["customer_name"],
                normal_style
            ),
        ],
        [
            Paragraph(
                "<b>Phone</b>",
                normal_style
            ),
            Paragraph(
                order.get("phone") or "Not provided",
                normal_style
            ),
        ],
        [
            Paragraph(
                "<b>Email</b>",
                normal_style
            ),
            Paragraph(
                order.get("email") or "Not provided",
                normal_style
            ),
        ],
    ]

    customer_table = Table(
        customer_details,
        colWidths=[120, 380]
    )

    customer_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.lightgrey
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),
            ]
        )
    )

    elements.append(customer_table)

    elements.append(Spacer(1, 15))

    # --------------------------------------------------------
    # Order items
    # --------------------------------------------------------

    elements.append(
        Paragraph(
            "Order Items",
            heading_style
        )
    )

    item_data = [
        [
            Paragraph("<b>Product</b>", normal_style),
            Paragraph("<b>Qty</b>", right_style),
            Paragraph("<b>Unit Price</b>", right_style),
            Paragraph("<b>Total</b>", right_style),
        ]
    ]

    for item in order["items"]:

        item_data.append(
            [
                Paragraph(
                    item["product_name"],
                    normal_style
                ),
                Paragraph(
                    str(item["quantity"]),
                    right_style
                ),
                Paragraph(
                    f"KES {item['unit_price']:,.2f}",
                    right_style
                ),
                Paragraph(
                    f"KES {item['total_price']:,.2f}",
                    right_style
                ),
            ]
        )

    item_table = Table(
        item_data,
        colWidths=[250, 50, 100, 100],
        repeatRows=1
    )

    item_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),
                (
                    "ALIGN",
                    (1, 1),
                    (-1, -1),
                    "RIGHT"
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),
            ]
        )
    )

    elements.append(item_table)

    elements.append(Spacer(1, 15))

    # --------------------------------------------------------
    # Totals
    # --------------------------------------------------------

    totals_data = [
        [
            Paragraph("<b>Subtotal</b>", right_style),
            Paragraph(
                f"<b>KES {order['subtotal']:,.2f}</b>",
                right_style
            ),
        ],
        [
            Paragraph("<b>Delivery Fee</b>", right_style),
            Paragraph(
                f"<b>KES {order['delivery_fee']:,.2f}</b>",
                right_style
            ),
        ],
        [
            Paragraph("<b>TOTAL</b>", right_style),
            Paragraph(
                f"<b>KES {order['total']:,.2f}</b>",
                right_style
            ),
        ],
    ]

    totals_table = Table(
        totals_data,
        colWidths=[350, 150]
    )

    totals_table.setStyle(
        TableStyle(
            [
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "RIGHT"
                ),
                (
                    "LINEABOVE",
                    (0, 2),
                    (-1, 2),
                    1,
                    colors.black
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),
            ]
        )
    )

    elements.append(totals_table)

    elements.append(Spacer(1, 25))

    # --------------------------------------------------------
    # Footer
    # --------------------------------------------------------

    elements.append(
        Paragraph(
            "Thank you for choosing KenyaBiz AI.",
            company_style
        )
    )

    elements.append(
        Paragraph(
            "This invoice was generated automatically by "
            "the KenyaBiz AI multi-agent business assistant.",
            company_style
        )
    )

    # --------------------------------------------------------
    # Generate PDF
    # --------------------------------------------------------

    document.build(elements)

    return {
        "status": "SUCCESS",
        "invoice_reference": order_reference,
        "invoice_filename": invoice_filename,
        "invoice_path": str(invoice_path),
        "order_reference": order_reference,
        "customer_name": order["customer_name"],
        "total": order["total"],
        "currency": order.get("currency", "KES")
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("KENYABIZ AI")
    print("Invoice Tool Test")
    print("=" * 60)

    # Make sure database exists
    initialize_database()

    # Create an order for testing
    from src.tools.order_tool import create_order

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
        customer_name="Invoice Test Customer",
        phone="0712345678",
        email="invoice@example.com",
        items=test_items
    )

    if order["status"] != "SUCCESS":

        print()
        print("ERROR:")
        print(order["message"])

    else:

        print()
        print(
            f"Order created: "
            f"{order['order_reference']}"
        )

        print()
        print("Generating invoice...")

        invoice = generate_invoice(
            order["order_reference"]
        )

        print()
        print("Invoice result:")
        print(invoice)

        if invoice["status"] == "SUCCESS":

            print()
            print("Invoice successfully generated.")

            print()
            print(
                f"File location:\n"
                f"{invoice['invoice_path']}"
            )

    print()
    print("=" * 60)
    print("INVOICE TOOL TEST COMPLETED")
    print("=" * 60)