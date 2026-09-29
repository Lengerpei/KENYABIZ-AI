from typing import Optional, List
from pathlib import Path
import re

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from src.tools.product_tool import search_products, check_stock
from src.tools.order_tool import create_order, get_order


# ============================================================
# ENVIRONMENT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


# ============================================================
# LLM
# ============================================================

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
)


# ============================================================
# DATA MODELS
# ============================================================

class CustomerInformation(BaseModel):
    name: str = Field(description="Customer's full name")
    phone: Optional[str] = Field(
        default=None,
        description="Customer phone number"
    )
    email: Optional[str] = Field(
        default=None,
        description="Customer email address"
    )


class OrderItem(BaseModel):
    product_name: str = Field(
        description="Name of the product to order"
    )
    quantity: int = Field(
        description="Quantity requested"
    )


class OrderRequest(BaseModel):
    customer: CustomerInformation
    items: List[OrderItem]


# ============================================================
# STRUCTURED LLM
# ============================================================

structured_llm = llm.with_structured_output(OrderRequest)


# ============================================================
# EXTRACT ORDER INFORMATION
# ============================================================

def extract_order_information(customer_message: str):
    """
    Extract customer information and requested products
    from the customer's message.
    """

    try:
        return structured_llm.invoke(
            f"""
Extract the customer information and order details
from the following customer message.

Customer message:
{customer_message}

Return:
- Customer name
- Phone number if available
- Email if available
- Product names
- Quantities
"""
        )

    except Exception as error:
        raise RuntimeError(
            f"Unable to extract order information: {error}"
        )


# ============================================================
# NORMALIZE PRODUCT NAME
# ============================================================

def normalize_product_name(product_name: str) -> str:
    """
    Normalize product names to improve matching.
    """

    if not product_name:
        return ""

    name = product_name.lower().strip()

    # Remove punctuation
    name = re.sub(r"[^a-z0-9\s]", " ", name)

    # Normalize multiple spaces
    name = re.sub(r"\s+", " ", name)

    # Common plural forms
    plural_map = {
        "chairs": "chair",
        "desks": "desk",
        "tables": "table",
        "phones": "phone",
        "laptops": "laptop",
        "printers": "printer",
        "monitors": "monitor",
    }

    words = name.split()

    normalized_words = [
        plural_map.get(word, word)
        for word in words
    ]

    return " ".join(normalized_words)


# ============================================================
# FIND PRODUCT MATCHES
# ============================================================

def find_product_matches(product_name: str):
    """
    Search for possible product matches.
    """

    if not product_name:
        return []

    normalized_name = normalize_product_name(product_name)

    search_terms = [
        product_name,
        normalized_name,
    ]

    matches = []

    for term in search_terms:

        if not term:
            continue

        try:
            results = search_products(term)
        except Exception:
            continue

        if not results:
            continue

        for product in results:

            product_id = product.get("product_id")

            if not product_id:
                continue

            # Avoid duplicates
            if any(
                item.get("product_id") == product_id
                for item in matches
            ):
                continue

            matches.append(product)

    # Exact normalized match first
    exact_matches = []

    for product in matches:

        product_name_db = product.get(
            "product_name",
            ""
        )

        if (
            normalize_product_name(product_name_db)
            == normalized_name
        ):
            exact_matches.append(product)

    if exact_matches:
        return exact_matches

    # Token-based matching
    requested_tokens = set(
        normalized_name.split()
    )

    token_matches = []

    for product in matches:

        db_name = normalize_product_name(
            product.get("product_name", "")
        )

        db_tokens = set(db_name.split())

        if requested_tokens.issubset(db_tokens):
            token_matches.append(product)

    return token_matches or matches


# ============================================================
# FIND SINGLE PRODUCT
# ============================================================

def find_product(product_name: str):
    """
    Determine whether a product is:
    - FOUND
    - NOT_FOUND
    - AMBIGUOUS
    """

    matches = find_product_matches(product_name)

    if not matches:
        return {
            "status": "NOT_FOUND",
            "product": None,
            "matches": [],
        }

    if len(matches) == 1:
        return {
            "status": "FOUND",
            "product": matches[0],
            "matches": matches,
        }

    return {
        "status": "AMBIGUOUS",
        "product": None,
        "matches": matches,
    }


# ============================================================
# VALIDATE ORDER ITEMS
# ============================================================

def validate_order_items(items: List[OrderItem]):
    """
    Validate requested products and stock availability.
    """

    if not items:
        return {
            "status": "ERROR",
            "message": "No order items were provided.",
            "items": [],
        }

    validated_items = []
    unavailable_products = []

    for item in items:

        if item.quantity <= 0:
            return {
                "status": "ERROR",
                "message": (
                    f"Quantity for {item.product_name} "
                    f"must be greater than zero."
                ),
                "items": [],
            }

        product_result = find_product(
            item.product_name
        )

        # ----------------------------------------------------
        # PRODUCT NOT FOUND
        # ----------------------------------------------------

        if product_result["status"] == "NOT_FOUND":

            unavailable_products.append(
                item.product_name
            )

            continue

        # ----------------------------------------------------
        # AMBIGUOUS PRODUCT
        # ----------------------------------------------------

        if product_result["status"] == "AMBIGUOUS":

            return {
                "status": "AMBIGUOUS_PRODUCT",
                "message": (
                    f"Multiple products matched "
                    f"'{item.product_name}'."
                ),
                "matches": product_result["matches"],
                "items": [],
            }

        # ----------------------------------------------------
        # PRODUCT FOUND
        # ----------------------------------------------------

        product = product_result["product"]

        product_id = product.get("product_id")

        try:
            stock_result = check_stock(
                product_id,
                item.quantity
            )
        except Exception:
            stock_result = False

        if not stock_result:

            return {
                "status": "INSUFFICIENT_STOCK",
                "message": (
                    f"Insufficient stock for "
                    f"{product.get('product_name', item.product_name)}."
                ),
                "items": [],
            }

        validated_items.append(
            {
                "product_id": product_id,
                "quantity": item.quantity,
            }
        )

    # --------------------------------------------------------
    # PRODUCT NOT FOUND RESPONSE
    # --------------------------------------------------------

    if unavailable_products:

        return {
            "status": "PRODUCT_NOT_FOUND",
            "message": (
                "The following products could not be found: "
                + ", ".join(unavailable_products)
            ),
            "items": [],
        }

    return {
        "status": "SUCCESS",
        "items": validated_items,
    }


# ============================================================
# PROCESS ORDER
# ============================================================

def process_order(
    customer_message: str,
    confirmed: bool = False,
    pending_request=None,
):
    """
    Process a customer order.

    Orders require confirmation before being created.
    """

    if not customer_message:

        return {
            "status": "ERROR",
            "message": "Please provide your order details.",
        }

    # --------------------------------------------------------
    # CONFIRMATION REQUIRED
    # --------------------------------------------------------

    if not confirmed:

        return {
            "status": "AWAITING_CONFIRMATION",
            "message": (
                "Please confirm that you would like "
                "to proceed with the order."
            ),
        }

    # --------------------------------------------------------
    # COMBINE PENDING REQUEST
    # --------------------------------------------------------

    if pending_request:

        customer_message = (
            f"{pending_request}\n"
            f"{customer_message}"
        )

    # --------------------------------------------------------
    # EXTRACT INFORMATION
    # --------------------------------------------------------

    try:

        order_request = extract_order_information(
            customer_message
        )

    except Exception as error:

        return {
            "status": "ERROR",
            "message": str(error),
        }

    # --------------------------------------------------------
    # CUSTOMER INFORMATION
    # --------------------------------------------------------

    customer = order_request.customer

    if not customer.name:

        return {
            "status": "CUSTOMER_DETAILS_REQUIRED",
            "message": "Please provide your name.",
        }

    # --------------------------------------------------------
    # VALIDATE PRODUCTS
    # --------------------------------------------------------

    validation_result = validate_order_items(
        order_request.items
    )

    if validation_result["status"] != "SUCCESS":

        return validation_result

    # --------------------------------------------------------
    # CREATE ORDER
    # --------------------------------------------------------

    try:

        order_result = create_order(
            customer_name=customer.name,
            items=validation_result["items"],
            phone=customer.phone,
            email=customer.email,
        )

    except Exception as error:

        return {
            "status": "ERROR",
            "message": (
                f"Unable to create order: {error}"
            ),
        }

    # --------------------------------------------------------
    # CHECK ORDER RESULT
    # --------------------------------------------------------

    if not order_result:

        return {
            "status": "ERROR",
            "message": "Unable to create the order.",
        }

    if isinstance(order_result, dict):

        if order_result.get("status") != "SUCCESS":

            return {
                "status": "ERROR",
                "message": order_result.get(
                    "message",
                    "Unable to create the order."
                ),
            }

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    return {
        "status": "SUCCESS",
        "message": "Order created successfully.",
        "order": order_result,
    }


# ============================================================
# FORMAT ORDER RESPONSE
# ============================================================

def format_order_response(result):
    """
    Convert order result into customer-friendly text.
    """

    status = result.get("status")

    # --------------------------------------------------------
    # AWAITING CONFIRMATION
    # --------------------------------------------------------

    if status == "AWAITING_CONFIRMATION":

        return (
            "Please confirm that you would like "
            "to proceed with the order."
        )

    # --------------------------------------------------------
    # CUSTOMER DETAILS REQUIRED
    # --------------------------------------------------------

    if status == "CUSTOMER_DETAILS_REQUIRED":

        return result.get(
            "message",
            "Please provide your customer details."
        )

    # --------------------------------------------------------
    # AMBIGUOUS PRODUCT
    # --------------------------------------------------------

    if status == "AMBIGUOUS_PRODUCT":

        matches = result.get("matches", [])

        product_names = [
            item.get("product_name", "")
            for item in matches
        ]

        return (
            "Multiple products matched your request: "
            + ", ".join(product_names)
            + ". Please specify the product."
        )

    # --------------------------------------------------------
    # PRODUCT NOT FOUND
    # --------------------------------------------------------

    if status == "PRODUCT_NOT_FOUND":

        return result.get(
            "message",
            "One or more products could not be found."
        )

    # --------------------------------------------------------
    # INSUFFICIENT STOCK
    # --------------------------------------------------------

    if status == "INSUFFICIENT_STOCK":

        return result.get(
            "message",
            "There is insufficient stock."
        )

    # --------------------------------------------------------
    # ERROR
    # --------------------------------------------------------

    if status == "ERROR":

        return (
            "I could not create the order.\n\n"
            + result.get(
                "message",
                "An unexpected error occurred."
            )
        )

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    if status == "SUCCESS":

        order = result.get("order", {})

        if not isinstance(order, dict):
            return "Order created successfully."

        order_reference = order.get(
            "order_reference",
            order.get("reference", "")
        )

        customer_name = order.get(
            "customer_name",
            ""
        )

        items = order.get(
            "items",
            []
        )

        subtotal = order.get(
            "subtotal",
            0
        )

        delivery_fee = order.get(
            "delivery_fee",
            0
        )

        total = order.get(
            "total",
            0
        )

        lines = [
            "Order created successfully.",
            "",
            f"Order reference: {order_reference}",
            f"Customer: {customer_name}",
            "",
            "Order summary:",
        ]

        for item in items:

            product_name = item.get(
                "product_name",
                "Product"
            )

            quantity = item.get(
                "quantity",
                0
            )

            line_total = item.get(
                "line_total",
                item.get(
                    "total_price",
                    0
                )
            )

            lines.append(
                f"- {product_name} x {quantity}: "
                f"KES {line_total:,.2f}"
            )

        lines.extend(
            [
                "",
                f"Subtotal: KES {subtotal:,.2f}",
                f"Delivery fee: KES {delivery_fee:,.2f}",
                f"Total: KES {total:,.2f}",
            ]
        )

        return "\n".join(lines)

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    return result.get(
        "message",
        "Unable to process the order."
    )


# ============================================================
# LOOKUP EXISTING ORDER
# ============================================================

def lookup_order(order_reference):
    """
    Retrieve an existing order using its reference.
    """

    if not order_reference:

        return {
            "status": "ERROR",
            "message": "Please provide an order reference.",
        }

    try:

        order_reference = (
            order_reference
            .strip()
            .upper()
        )

        order = get_order(
            order_reference
        )

        if not order:

            return {
                "status": "NOT_FOUND",
                "message": (
                    f"No order was found with reference "
                    f"{order_reference}."
                ),
            }

        return {
            "status": "SUCCESS",
            "order": order,
        }

    except Exception as error:

        return {
            "status": "ERROR",
            "message": (
                f"Unable to retrieve order: {error}"
            ),
        }


# ============================================================
# FORMAT EXISTING ORDER
# ============================================================

def format_existing_order(result):
    """
    Format an existing order for the customer.
    """

    if result["status"] == "NOT_FOUND":

        return result["message"]

    if result["status"] != "SUCCESS":

        return (
            "I could not retrieve the order.\n\n"
            + result.get(
                "message",
                "An unexpected error occurred."
            )
        )

    order = result["order"]

    lines = [
        "Order details:",
        "",
        f"Order reference: {order.get('order_reference', '')}",
        f"Customer: {order.get('customer_name', '')}",
        f"Status: {order.get('status', '')}",
        "",
        "Items:",
    ]

    for item in order.get("items", []):

        product_name = item.get(
            "product_name",
            "Product"
        )

        quantity = item.get(
            "quantity",
            0
        )

        lines.append(
            f"- {product_name} x {quantity}"
        )

    lines.extend(
        [
            "",
            f"Subtotal: KES {order.get('subtotal', 0):,.2f}",
            f"Delivery fee: KES {order.get('delivery_fee', 0):,.2f}",
            f"Total: KES {order.get('total', 0):,.2f}",
        ]
    )

    return "\n".join(lines)