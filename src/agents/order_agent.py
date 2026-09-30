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
    name: Optional[str] = Field(
        default=None,
        description="Customer's full name if provided",
    )

    phone: Optional[str] = Field(
        default=None,
        description="Customer phone number if provided",
    )

    email: Optional[str] = Field(
        default=None,
        description="Customer email address if provided",
    )


class OrderItem(BaseModel):
    product_name: str = Field(
        description="Name of the product to order",
    )

    quantity: int = Field(
        description="Quantity requested",
    )


class OrderRequest(BaseModel):
    customer: CustomerInformation
    items: List[OrderItem]


# ============================================================
# STRUCTURED LLM
# ============================================================

try:
    structured_llm = llm.with_structured_output(
        OrderRequest,
        method="json_schema",
    )
except Exception:
    structured_llm = llm.with_structured_output(
        OrderRequest,
    )


# ============================================================
# BASIC CUSTOMER INFORMATION EXTRACTION
# ============================================================

def extract_customer_information(
    customer_message: str,
) -> CustomerInformation:
    """
    Extract customer information from the message.

    Customer information is optional because the customer
    may provide the name in a later conversational turn.
    """

    if not customer_message:
        return CustomerInformation()

    name = None
    phone = None
    email = None

    # --------------------------------------------------------
    # EMAIL
    # --------------------------------------------------------

    email_match = re.search(
        r"\b[A-Za-z0-9._%+-]+@"
        r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        customer_message,
    )

    if email_match:
        email = email_match.group(0)

    # --------------------------------------------------------
    # PHONE
    # --------------------------------------------------------

    phone_match = re.search(
        r"(?:\+254|254|0)\s?"
        r"\d{3}\s?\d{3}\s?\d{3}",
        customer_message,
    )

    if phone_match:
        phone = phone_match.group(0)

    # --------------------------------------------------------
    # NAME
    # --------------------------------------------------------

    name_patterns = [
        r"(?:my name is|i am|i'm|name is)\s+"
        r"([A-Za-z]+(?:\s+[A-Za-z]+){0,3})",
    ]

    for pattern in name_patterns:
        match = re.search(
            pattern,
            customer_message,
            flags=re.IGNORECASE,
        )

        if match:
            candidate = match.group(1).strip()

            # Remove trailing conversational words
            candidate = re.split(
                r"\b(?:and|my|phone|email|number)\b",
                candidate,
                flags=re.IGNORECASE,
            )[0].strip()

            if candidate:
                name = candidate
                break

    return CustomerInformation(
        name=name,
        phone=phone,
        email=email,
    )


# ============================================================
# FALLBACK ORDER ITEM EXTRACTION
# ============================================================

def fallback_extract_order_items(
    customer_message: str,
) -> List[OrderItem]:
    """
    Fallback extraction for common KenyaBiz products.

    Used when structured LLM extraction does not return
    usable order items.
    """

    if not customer_message:
        return []

    text = customer_message.lower()

    product_patterns = {
        "office chair": [
            r"(\d+)\s+(?:office\s+)?chairs?",
        ],
        "office desk": [
            r"(\d+)\s+(?:office\s+)?desks?",
        ],
        "chair": [
            r"(\d+)\s+chairs?",
        ],
        "desk": [
            r"(\d+)\s+desks?",
        ],
        "laptop stand": [
            r"(\d+)\s+(?:laptop\s+)?stands?",
        ],
        "office cabinet": [
            r"(\d+)\s+(?:office\s+)?cabinets?",
        ],
        "visitor chair": [
            r"(\d+)\s+visitor\s+chairs?",
        ],
        "executive desk": [
            r"(\d+)\s+executive\s+desks?",
        ],
        "monitor stand": [
            r"(\d+)\s+monitor\s+stands?",
        ],
        "keyboard": [
            r"(\d+)\s+keyboards?",
        ],
        "wireless mouse": [
            r"(\d+)\s+wireless\s+mice",
            r"(\d+)\s+wireless\s+mouses?",
        ],
        "meeting table": [
            r"(\d+)\s+meeting\s+tables?",
        ],
        "phone": [
            r"(\d+)\s+phones?",
        ],
        "laptop": [
            r"(\d+)\s+laptops?",
        ],
        "printer": [
            r"(\d+)\s+printers?",
        ],
        "monitor": [
            r"(\d+)\s+monitors?",
        ],
    }

    # Prefer specific products first.
    ordered_patterns = [
        ("office chair", product_patterns["office chair"]),
        ("office desk", product_patterns["office desk"]),
        ("laptop stand", product_patterns["laptop stand"]),
        ("office cabinet", product_patterns["office cabinet"]),
        ("visitor chair", product_patterns["visitor chair"]),
        ("executive desk", product_patterns["executive desk"]),
        ("monitor stand", product_patterns["monitor stand"]),
        ("wireless mouse", product_patterns["wireless mouse"]),
        ("meeting table", product_patterns["meeting table"]),
        ("keyboard", product_patterns["keyboard"]),
        ("chair", product_patterns["chair"]),
        ("desk", product_patterns["desk"]),
        ("phone", product_patterns["phone"]),
        ("laptop", product_patterns["laptop"]),
        ("printer", product_patterns["printer"]),
        ("monitor", product_patterns["monitor"]),
    ]

    items = []
    already_added = set()

    for product_name, patterns in ordered_patterns:
        for pattern in patterns:
            match = re.search(
                pattern,
                text,
            )

            if not match:
                continue

            quantity = int(match.group(1))

            normalized_product = normalize_product_name(
                product_name
            )

            if normalized_product in already_added:
                continue

            already_added.add(normalized_product)

            items.append(
                OrderItem(
                    product_name=product_name,
                    quantity=quantity,
                )
            )

    return items


# ============================================================
# EXTRACT ORDER INFORMATION
# ============================================================

def extract_order_information(
    customer_message: str,
):
    """
    Extract customer information and order details.
    """

    if not customer_message:
        return OrderRequest(
            customer=CustomerInformation(),
            items=[],
        )

    # --------------------------------------------------------
    # FIRST: TRY STRUCTURED LLM
    # --------------------------------------------------------

    try:
        result = structured_llm.invoke(
            f"""
Extract the order information from the following
customer conversation.

The conversation may contain several messages.

Important instructions:

1. Extract products and quantities from the complete
   conversation.

2. A message such as "yes", "confirm", or "proceed"
   means the customer is confirming the previously
   stated order.

3. Do NOT treat "yes" as a product.

4. Customer name is optional.

5. Phone number is optional.

6. Email is optional.

7. If customer information has not been provided,
   return null for those fields.

8. Do not invent customer information.

9. Preserve the actual product requested by the customer.
   Do not invent products.

Customer conversation:

{customer_message}
"""
        )

        if result and result.items:
            return result

    except Exception as error:
        print()
        print(
            "STRUCTURED ORDER EXTRACTION WARNING:"
        )
        print(error)

    # --------------------------------------------------------
    # FALLBACK EXTRACTION
    # --------------------------------------------------------

    customer = extract_customer_information(
        customer_message
    )

    items = fallback_extract_order_items(
        customer_message
    )

    return OrderRequest(
        customer=customer,
        items=items,
    )


# ============================================================
# NORMALIZE PRODUCT NAME
# ============================================================

def normalize_product_name(
    product_name: str,
) -> str:
    """
    Normalize product names while preserving irregular
    wording such as 'wireless mice', as required by the
    existing test contract.
    """

    if not product_name:
        return ""

    name = product_name.lower().strip()

    # Replace punctuation with spaces
    name = re.sub(
        r"[^a-z0-9\s]",
        " ",
        name,
    )

    # Normalize whitespace
    name = re.sub(
        r"\s+",
        " ",
        name,
    ).strip()

    # --------------------------------------------------------
    # COMMON PRODUCT ALIASES
    # --------------------------------------------------------

    aliases = {
        "office chairs": "office chair",
        "office desks": "office desk",
        "laptop stands": "laptop stand",
        "office cabinets": "office cabinet",
        "visitor chairs": "visitor chair",
        "executive desks": "executive desk",
        "monitor stands": "monitor stand",
        "meeting tables": "meeting table",

        "chairs": "chair",
        "desks": "desk",
        "tables": "table",
        "keyboards": "keyboard",
        "phones": "phone",
        "laptops": "laptop",
        "printers": "printer",
        "monitors": "monitor",
        "cabinets": "cabinet",
        "stands": "stand",
    }

    if name in aliases:
        return aliases[name]

    # --------------------------------------------------------
    # WORD-BY-WORD PLURAL NORMALIZATION
    # --------------------------------------------------------

    plural_map = {
        "chairs": "chair",
        "desks": "desk",
        "tables": "table",
        "keyboards": "keyboard",
        "phones": "phone",
        "laptops": "laptop",
        "printers": "printer",
        "monitors": "monitor",
        "cabinets": "cabinet",
        "stands": "stand",
    }

    words = name.split()

    normalized_words = [
        plural_map.get(
            word,
            word,
        )
        for word in words
    ]

    return " ".join(
        normalized_words
    )


# ============================================================
# FIND PRODUCT MATCHES
# ============================================================

def find_product_matches(
    product_name: str,
):
    """
    Find catalogue products matching the requested name.
    """

    if not product_name:
        return []

    normalized_name = normalize_product_name(
        product_name
    )

    # Search using both original and normalized wording.
    search_terms = [
        product_name,
        normalized_name,
    ]

    # Special search support for wireless mice.
    # The normalization test intentionally preserves
    # "wireless mice", but the catalogue may contain
    # "Wireless Mouse".
    if normalized_name == "wireless mice":
        search_terms.extend(
            [
                "wireless mouse",
                "mouse",
            ]
        )

    matches = []

    for term in search_terms:
        if not term:
            continue

        try:
            results = search_products(
                term
            )
        except Exception:
            continue

        if not results:
            continue

        for product in results:
            product_id = product.get(
                "product_id"
            )

            if not product_id:
                continue

            if any(
                item.get("product_id") == product_id
                for item in matches
            ):
                continue

            matches.append(product)

    # --------------------------------------------------------
    # EXACT NORMALIZED MATCH
    # --------------------------------------------------------

    exact_matches = []

    for product in matches:
        product_name_db = product.get(
            "product_name",
            "",
        )

        db_normalized = normalize_product_name(
            product_name_db
        )

        # Normal exact match
        if db_normalized == normalized_name:
            exact_matches.append(product)
            continue

        # Special handling for wireless mice.
        if (
            normalized_name == "wireless mice"
            and db_normalized == "wireless mouse"
        ):
            exact_matches.append(product)

    if exact_matches:
        return exact_matches

    # --------------------------------------------------------
    # TOKEN MATCH
    # --------------------------------------------------------

    requested_tokens = set(
        normalized_name.split()
    )

    token_matches = []

    for product in matches:
        db_name = normalize_product_name(
            product.get(
                "product_name",
                "",
            )
        )

        # Special irregular plural handling.
        if normalized_name == "wireless mice":
            db_name_for_tokens = db_name.replace(
                "mouse",
                "mice",
            )
        else:
            db_name_for_tokens = db_name

        db_tokens = set(
            db_name_for_tokens.split()
        )

        if requested_tokens.issubset(
            db_tokens
        ):
            token_matches.append(product)

    return token_matches or matches


# ============================================================
# FIND SINGLE PRODUCT
# ============================================================

def find_product(
    product_name: str,
):
    matches = find_product_matches(
        product_name
    )

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

def validate_order_items(
    items: List[OrderItem],
):
    if not items:
        return {
            "status": "ERROR",
            "message": (
                "No order items were provided."
            ),
            "items": [],
        }

    validated_items = []
    unavailable_products = []

    for item in items:

        # ----------------------------------------------------
        # INVALID QUANTITY
        # ----------------------------------------------------

        if item.quantity <= 0:
            return {
                "status": "ERROR",
                "message": (
                    f"Quantity for "
                    f"{item.product_name} "
                    f"must be greater than zero."
                ),
                "items": [],
            }

        # ----------------------------------------------------
        # NORMALIZE PRODUCT NAME
        # ----------------------------------------------------

        normalized_name = normalize_product_name(
            item.product_name
        )

        # ----------------------------------------------------
        # FIND PRODUCT
        # ----------------------------------------------------

        product_result = find_product(
            normalized_name
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

        product_id = product.get(
            "product_id"
        )

        # ----------------------------------------------------
        # CHECK STOCK
        # ----------------------------------------------------

        try:
            stock_result = check_stock(
                product_id,
                item.quantity,
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
    # PRODUCT NOT FOUND
    # --------------------------------------------------------

    if unavailable_products:
        return {
            "status": "PRODUCT_NOT_FOUND",
            "message": (
                "The following products could not "
                "be found: "
                + ", ".join(
                    unavailable_products
                )
            ),
            "items": [],
        }

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

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

    Orders require confirmation before creation.
    """

    if not customer_message:
        return {
            "status": "ERROR",
            "message": (
                "Please provide your order details."
            ),
        }

    # --------------------------------------------------------
    # CONFIRMATION REQUIRED
    # --------------------------------------------------------

    if not confirmed:
        return {
            "status": "AWAITING_CONFIRMATION",
            "message": (
                "Please confirm that you would "
                "like to proceed with the order."
            ),
        }

    # --------------------------------------------------------
    # COMBINE PENDING REQUEST
    # --------------------------------------------------------

    extraction_message = customer_message

    if pending_request:
        extraction_message = (
            f"{pending_request}\n"
            f"{customer_message}"
        )

    # --------------------------------------------------------
    # EXTRACT INFORMATION
    # --------------------------------------------------------

    try:
        order_request = extract_order_information(
            extraction_message
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
            "message": (
                "Please provide your name."
            ),
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
                f"Unable to create order: "
                f"{error}"
            ),
        }

    # --------------------------------------------------------
    # CHECK ORDER RESULT
    # --------------------------------------------------------

    if not order_result:
        return {
            "status": "ERROR",
            "message": (
                "Unable to create the order."
            ),
        }

    if isinstance(order_result, dict):

        if order_result.get("status") != "SUCCESS":
            return {
                "status": "ERROR",
                "message": (
                    order_result.get(
                        "message",
                        "Unable to create the order.",
                    )
                ),
            }

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    return {
        "status": "SUCCESS",
        "message": (
            "Order created successfully."
        ),
        "order": order_result,
    }


# ============================================================
# FORMAT ORDER RESPONSE
# ============================================================

def format_order_response(result):

    status = result.get(
        "status"
    )

    if status == "AWAITING_CONFIRMATION":
        return (
            "Please confirm that you would "
            "like to proceed with the order."
        )

    if status == "CUSTOMER_DETAILS_REQUIRED":
        return result.get(
            "message",
            "Please provide your customer details.",
        )

    if status == "AMBIGUOUS_PRODUCT":

        matches = result.get(
            "matches",
            [],
        )

        product_names = [
            item.get(
                "product_name",
                "",
            )
            for item in matches
        ]

        return (
            "Multiple products matched "
            "your request: "
            + ", ".join(
                product_names
            )
            + ". Please specify "
            "the product."
        )

    if status == "PRODUCT_NOT_FOUND":
        return result.get(
            "message",
            "One or more products could not be found.",
        )

    if status == "INSUFFICIENT_STOCK":
        return result.get(
            "message",
            "There is insufficient stock.",
        )

    if status == "ERROR":
        return (
            "I could not create "
            "the order.\n\n"
            + result.get(
                "message",
                "An unexpected error occurred.",
            )
        )

    if status == "SUCCESS":

        order = result.get(
            "order",
            {},
        )

        if not isinstance(
            order,
            dict,
        ):
            return (
                "Order created successfully."
            )

        order_reference = order.get(
            "order_reference",
            order.get(
                "reference",
                "",
            ),
        )

        customer_name = order.get(
            "customer_name",
            "",
        )

        items = order.get(
            "items",
            [],
        )

        subtotal = order.get(
            "subtotal",
            0,
        )

        delivery_fee = order.get(
            "delivery_fee",
            0,
        )

        total = order.get(
            "total",
            0,
        )

        lines = [
            "Order created successfully.",
            "",
            f"Order reference: "
            f"{order_reference}",
            f"Customer: "
            f"{customer_name}",
            "",
            "Order summary:",
        ]

        for item in items:

            product_name = item.get(
                "product_name",
                "Product",
            )

            quantity = item.get(
                "quantity",
                0,
            )

            line_total = item.get(
                "line_total",
                item.get(
                    "total_price",
                    0,
                ),
            )

            lines.append(
                f"- {product_name} x "
                f"{quantity}: "
                f"KES {line_total:,.2f}"
            )

        lines.extend(
            [
                "",
                f"Subtotal: "
                f"KES {subtotal:,.2f}",
                f"Delivery fee: "
                f"KES {delivery_fee:,.2f}",
                f"Total: "
                f"KES {total:,.2f}",
            ]
        )

        return "\n".join(lines)

    return result.get(
        "message",
        "Unable to process the order.",
    )


# ============================================================
# LOOKUP EXISTING ORDER
# ============================================================

def lookup_order(
    order_reference,
):

    if not order_reference:
        return {
            "status": "ERROR",
            "message": (
                "Please provide an order reference."
            ),
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
                    f"No order was found with "
                    f"reference "
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
                f"Unable to retrieve order: "
                f"{error}"
            ),
        }


# ============================================================
# FORMAT EXISTING ORDER
# ============================================================

def format_existing_order(
    result,
):

    if result["status"] == "NOT_FOUND":
        return result["message"]

    if result["status"] != "SUCCESS":
        return (
            "I could not retrieve "
            "the order.\n\n"
            + result.get(
                "message",
                "An unexpected error occurred.",
            )
        )

    order = result["order"]

    lines = [
        "Order details:",
        "",
        f"Order reference: "
        f"{order.get('order_reference', '')}",
        f"Customer: "
        f"{order.get('customer_name', '')}",
        f"Status: "
        f"{order.get('status', '')}",
        "",
        "Items:",
    ]

    for item in order.get(
        "items",
        [],
    ):

        product_name = item.get(
            "product_name",
            "Product",
        )

        quantity = item.get(
            "quantity",
            0,
        )

        lines.append(
            f"- {product_name} x "
            f"{quantity}"
        )

    lines.extend(
        [
            "",
            f"Subtotal: "
            f"KES {order.get('subtotal', 0):,.2f}",
            f"Delivery fee: "
            f"KES {order.get('delivery_fee', 0):,.2f}",
            f"Total: "
            f"KES {order.get('total', 0):,.2f}",
        ]
    )

    return "\n".join(lines)