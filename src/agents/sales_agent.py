"""
KENYABIZ AI
Sales Agent

Responsibilities:
- Product catalogue
- Product search
- Product prices
- Stock checking
- Product recommendations
- Quotations
"""

import re
from typing import Any, Dict, List, Optional

from src.tools.product_tool import (
    get_product,
    search_products,
    check_stock,
    get_products_by_category,
)

from src.tools.quotation_tool import build_quotation


# ============================================================
# PRODUCT ID ALIASES
# ============================================================

PRODUCT_IDS = {
    # --------------------------------------------------------
    # Office furniture
    # --------------------------------------------------------

    "office chair": "P001",
    "office chairs": "P001",

    "office desk": "P002",
    "office desks": "P002",

    "laptop stand": "P003",
    "laptop stands": "P003",

    "office cabinet": "P004",
    "office cabinets": "P004",

    "visitor chair": "P005",
    "visitor chairs": "P005",

    "executive desk": "P006",
    "executive desks": "P006",

    # --------------------------------------------------------
    # Other products
    # --------------------------------------------------------

    "monitor stand": "P007",
    "monitor stands": "P007",

    "keyboard": "P008",
    "keyboards": "P008",

    "wireless mouse": "P009",
    "wireless mice": "P009",

    "meeting table": "P010",
    "meeting tables": "P010",
}


# ============================================================
# NUMBER WORDS
# ============================================================

NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
}


# ============================================================
# GENERAL HELPERS
# ============================================================

def normalize_text(text: str) -> str:
    """Normalize user text for matching."""

    if not text:
        return ""

    return re.sub(
        r"\s+",
        " ",
        text.lower().strip(),
    )


def format_currency(value: float) -> str:
    """Format Kenyan Shillings."""

    return f"KES {value:,.2f}"


# ============================================================
# PRODUCT FIELD HELPERS
# ============================================================

def product_name(product: Dict[str, Any]) -> str:
    """
    Get the product name using the actual database field.
    """

    return str(
        product.get(
            "product_name",
            product.get(
                "name",
                "Unknown product",
            ),
        )
    )


def product_price(product: Dict[str, Any]) -> float:
    """
    Get the product price using the actual database field.
    """

    return float(
        product.get(
            "price_kes",
            product.get(
                "price",
                0,
            ),
        )
    )


def product_stock(product: Dict[str, Any]) -> int:
    """
    Get stock quantity using the actual database field.
    """

    return int(
        product.get(
            "stock_quantity",
            product.get(
                "stock",
                0,
            ),
        )
    )


# ============================================================
# QUANTITY EXTRACTION
# ============================================================

def extract_quantity(
    text: str,
    default: int = 1,
) -> int:
    """
    Extract a general quantity from text.

    Examples:

        "5 office chairs" -> 5
        "five office chairs" -> 5
        "office chairs" -> 1
    """

    text = normalize_text(text)

    # --------------------------------------------------------
    # Numeric quantity
    # --------------------------------------------------------

    match = re.search(
        r"\b(\d+)\b",
        text,
    )

    if match:

        quantity = int(
            match.group(1)
        )

        if quantity > 0:
            return quantity

    # --------------------------------------------------------
    # Number word
    # --------------------------------------------------------

    for word, number in NUMBER_WORDS.items():

        if re.search(
            rf"\b{re.escape(word)}\b",
            text,
        ):
            return number

    return default


def extract_quantity_for_product(
    text: str,
    product_name_text: str,
    default: int = 1,
) -> int:
    """
    Extract the quantity associated with a particular product.

    Examples:

        "5 office chairs"
            -> 5

        "five office chairs"
            -> 5

        "5 office chairs and 2 office desks"

            Office Chair -> 5
            Office Desk  -> 2
    """

    text = normalize_text(text)

    product_name_text = normalize_text(
        product_name_text
    )

    # --------------------------------------------------------
    # Build singular/plural alternatives
    # --------------------------------------------------------

    product_variants = [
        product_name_text
    ]

    if product_name_text.endswith("s"):

        singular = product_name_text[:-1]

        if singular not in product_variants:
            product_variants.append(
                singular
            )

    else:

        plural = product_name_text + "s"

        if plural not in product_variants:
            product_variants.append(
                plural
            )

    # --------------------------------------------------------
    # Find product in text
    # --------------------------------------------------------

    product_position = -1

    for variant in product_variants:

        position = text.find(
            variant
        )

        if position != -1:

            product_position = position
            break

    if product_position == -1:
        return default

    # --------------------------------------------------------
    # Text immediately before product
    # --------------------------------------------------------

    before = text[
        :product_position
    ]

    # --------------------------------------------------------
    # Numeric quantity
    # --------------------------------------------------------

    numeric_match = re.search(
        r"(\d+)\s*$",
        before,
    )

    if numeric_match:

        quantity = int(
            numeric_match.group(1)
        )

        if quantity > 0:
            return quantity

    # --------------------------------------------------------
    # Number-word quantity
    # --------------------------------------------------------

    for word, number in sorted(
        NUMBER_WORDS.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):

        if re.search(
            rf"\b{re.escape(word)}\s*$",
            before,
        ):
            return number

    return default


def extract_product_quantities(
    text: str,
    products: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Extract product-specific quantities.

    Example:

        "5 office chairs and 2 office desks"

    becomes:

        [
            {
                "product_id": "P001",
                "quantity": 5
            },
            {
                "product_id": "P002",
                "quantity": 2
            }
        ]
    """

    items = []

    for product in products:

        name = product_name(
            product
        )

        quantity = extract_quantity_for_product(
            text,
            name,
            default=1,
        )

        items.append(
            {
                "product_id": product["product_id"],
                "quantity": quantity,
            }
        )

    return items


# ============================================================
# PRODUCT IDENTIFICATION
# ============================================================

def identify_product(
    text: str,
) -> Optional[Dict[str, Any]]:
    """
    Identify a product from:

    - Product ID
    - Product name
    - Product alias
    """

    normalized = normalize_text(
        text
    )

    # --------------------------------------------------------
    # Check product ID
    # --------------------------------------------------------

    product_id_match = re.search(
        r"\bP\d{3}\b",
        normalized.upper(),
    )

    if product_id_match:

        product_id = (
            product_id_match.group(0)
        )

        product = get_product(
            product_id
        )

        if product:
            return product

    # --------------------------------------------------------
    # Check known aliases
    # --------------------------------------------------------

    aliases = sorted(
        PRODUCT_IDS.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )

    for alias, product_id in aliases:

        if re.search(
            rf"\b{re.escape(alias)}\b",
            normalized,
        ):

            product = get_product(
                product_id
            )

            if product:
                return product

    # --------------------------------------------------------
    # Try database search
    # --------------------------------------------------------

    results = search_products(
        normalized
    )

    if results:
        return results[0]

    return None


# ============================================================
# PRODUCT MENTION DETECTION
# ============================================================

def find_mentioned_products(
    text: str,
) -> List[Dict[str, Any]]:
    """
    Identify all known products mentioned in a request.

    This is different from identify_product(), which returns
    only one product.

    Example:

        "5 office chairs and 2 office desks"

    returns:

        P001 Office Chair
        P002 Office Desk
    """

    normalized = normalize_text(
        text
    )

    mentioned_products = []

    # --------------------------------------------------------
    # Match known product aliases
    # --------------------------------------------------------

    aliases = sorted(
        PRODUCT_IDS.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )

    for alias, product_id in aliases:

        if re.search(
            rf"\b{re.escape(alias)}\b",
            normalized,
        ):

            product = get_product(
                product_id
            )

            if product:

                if not any(
                    existing.get("product_id")
                    == product_id
                    for existing in mentioned_products
                ):

                    mentioned_products.append(
                        product
                    )

    # --------------------------------------------------------
    # Match product IDs
    # --------------------------------------------------------

    product_ids = re.findall(
        r"\bP\d{3}\b",
        normalized.upper(),
    )

    for product_id in product_ids:

        product = get_product(
            product_id
        )

        if product:

            if not any(
                existing.get("product_id")
                == product_id
                for existing in mentioned_products
            ):

                mentioned_products.append(
                    product
                )

    return mentioned_products


# ============================================================
# EXPLICIT ORDER DETECTION
# ============================================================

def is_explicit_order_request(
    text: str,
) -> bool:
    """
    Detect language indicating that the customer wants to
    actually place an order.

    These requests should remain with the Order Agent.

    Examples:

        "I want to order 2 office chairs"
        "Please place an order for 5 chairs"
        "I want to buy 3 desks"
        "Please purchase 2 keyboards"
    """

    normalized = normalize_text(
        text
    )

    order_patterns = [

        # ----------------------------------------------------
        # Order
        # ----------------------------------------------------

        r"\border\b",
        r"\bordering\b",
        r"\borders\b",

        # ----------------------------------------------------
        # Place order
        # ----------------------------------------------------

        r"\bplace an order\b",
        r"\bplace my order\b",
        r"\bplace the order\b",

        # ----------------------------------------------------
        # Want to order
        # ----------------------------------------------------

        r"\bi want to order\b",
        r"\bi would like to order\b",
        r"\bi'd like to order\b",
        r"\bi need to order\b",

        # ----------------------------------------------------
        # Buying
        # ----------------------------------------------------

        r"\bi want to buy\b",
        r"\bi would like to buy\b",
        r"\bi'd like to buy\b",
        r"\bi need to buy\b",

        # ----------------------------------------------------
        # Purchase
        # ----------------------------------------------------

        r"\bpurchase\b",
        r"\bpurchase an\b",
        r"\bpurchase a\b",

        # ----------------------------------------------------
        # Proceed
        # ----------------------------------------------------

        r"\bproceed with the order\b",
        r"\bproceed with my order\b",
        r"\bgo ahead with the order\b",
        r"\bgo ahead and order\b",
    ]

    return any(
        re.search(
            pattern,
            normalized,
        )
        for pattern in order_patterns
    )


# ============================================================
# QUANTITY REQUEST DETECTION
# ============================================================

def has_quantity(
    text: str,
) -> bool:
    """
    Determine whether a request contains a quantity.

    Supports both numeric and word quantities.

    Examples:

        "5 office chairs" -> True
        "five office chairs" -> True
        "office chairs" -> False
    """

    normalized = normalize_text(
        text
    )

    # Numeric quantity
    if re.search(
        r"\b\d+\b",
        normalized,
    ):
        return True

    # Number-word quantity
    return any(
        re.search(
            rf"\b{re.escape(word)}\b",
            normalized,
        )
        for word in NUMBER_WORDS
    )


def is_quantity_based_quotation_request(
    text: str,
) -> bool:
    """
    Detect a natural quantity-based quotation request.

    Examples:

        "I need 5 office chairs"
        "I need 5 office chairs and 2 office desks"
        "5 office chairs and 2 office desks"
        "I need five office chairs"

    Explicit order requests are excluded because those belong
    to the Order Agent.
    """

    normalized = normalize_text(
        text
    )

    # --------------------------------------------------------
    # Explicit orders must not become quotations.
    # --------------------------------------------------------

    if is_explicit_order_request(
        normalized
    ):
        return False

    # --------------------------------------------------------
    # There must be at least one quantity.
    # --------------------------------------------------------

    if not has_quantity(
        normalized
    ):
        return False

    # --------------------------------------------------------
    # There must be at least one known product.
    # --------------------------------------------------------

    mentioned_products = find_mentioned_products(
        normalized
    )

    return bool(
        mentioned_products
    )


# ============================================================
# PRODUCT CATALOGUE
# ============================================================

def get_product_catalogue() -> List[Dict[str, Any]]:
    """
    Return all products currently available.

    The current database does not have a get_all_products()
    function, so we retrieve products using the known IDs.
    """

    products = []

    # --------------------------------------------------------
    # Get all known product IDs
    # --------------------------------------------------------

    product_ids = sorted(
        set(
            PRODUCT_IDS.values()
        )
    )

    for product_id in product_ids:

        product = get_product(
            product_id
        )

        if product:

            if not any(
                p["product_id"] == product_id
                for p in products
            ):
                products.append(
                    product
                )

    # --------------------------------------------------------
    # Sort by product ID
    # --------------------------------------------------------

    products.sort(
        key=lambda p: p.get(
            "product_id",
            "",
        )
    )

    return products


def is_product_catalogue_request(
    text: str,
) -> bool:
    """
    Detect requests asking for the product catalogue.
    """

    normalized = normalize_text(
        text
    )

    patterns = [

        # ----------------------------------------------------
        # Products
        # ----------------------------------------------------

        r"\bwhat products do you have\b",
        r"\bwhat products are available\b",
        r"\bwhat products do you sell\b",
        r"\bwhich products do you have\b",
        r"\bwhich products are available\b",

        # ----------------------------------------------------
        # Items
        # ----------------------------------------------------

        r"\bwhat items do you have\b",
        r"\bwhat items are available\b",
        r"\bwhat items do you sell\b",
        r"\bwhich items do you have\b",
        r"\bwhich items are available\b",

        # ----------------------------------------------------
        # Catalogue
        # ----------------------------------------------------

        r"\bshow me your catalogue\b",
        r"\bshow me the catalogue\b",
        r"\bshow your catalogue\b",
        r"\bshow catalogue\b",
        r"\bproduct catalogue\b",
        r"\bproduct catalog\b",

        # ----------------------------------------------------
        # Lists
        # ----------------------------------------------------

        r"\blist your products\b",
        r"\blist the products\b",
        r"\blist products\b",
        r"\blist your items\b",
        r"\blist the items\b",
        r"\blist items\b",

        # ----------------------------------------------------
        # Show all
        # ----------------------------------------------------

        r"\bshow me all products\b",
        r"\bshow me all the products\b",
        r"\bshow all products\b",
        r"\bshow me all items\b",
        r"\bshow me all the items\b",
        r"\bshow all items\b",
        r"\bshow me your products\b",
        r"\bshow me your items\b",

        # ----------------------------------------------------
        # Selling
        # ----------------------------------------------------

        r"\bwhat do you sell\b",
        r"\bwhat are you selling\b",
        r"\bproducts you sell\b",
        r"\bitems you sell\b",

        # ----------------------------------------------------
        # General
        # ----------------------------------------------------

        r"\bwhat do you have\b",
        r"\bwhat is available\b",
        r"\bwhat's available\b",
        r"\bwhats available\b",
    ]

    return any(
        re.search(
            pattern,
            normalized,
        )
        for pattern in patterns
    )


def format_product_catalogue(
    products: List[Dict[str, Any]],
) -> str:
    """
    Format the product catalogue for the customer.
    """

    if not products:

        return (
            "There are currently no products "
            "available in the catalogue."
        )

    lines = [
        "Here are the products currently available:",
        "",
    ]

    for product in products:

        product_id = product.get(
            "product_id",
            "N/A",
        )

        name = product_name(
            product
        )

        price = product_price(
            product
        )

        lines.append(
            f"- {name} ({product_id}) — "
            f"{format_currency(price)} per unit"
        )

    return "\n".join(lines)


def process_product_catalogue_request() -> Dict[str, Any]:
    """
    Process a catalogue request.
    """

    products = get_product_catalogue()

    return {
        "success": bool(products),
        "type": "CATALOGUE",
        "products": products,
        "response": format_product_catalogue(
            products
        ),
    }


# ============================================================
# PRODUCT PRICE
# ============================================================

def process_price_request(
    text: str,
) -> Dict[str, Any]:
    """
    Process a product price request.
    """

    product = identify_product(
        text
    )

    if not product:

        return {
            "success": False,
            "type": "PRICE",
            "response": (
                "I could not identify the product "
                "you are asking about. Please provide "
                "the product name or product ID."
            ),
        }

    quantity = extract_quantity(
        text
    )

    price = product_price(
        product
    )

    total = price * quantity

    name = product_name(
        product
    )

    product_id = product[
        "product_id"
    ]

    if quantity == 1:

        response = (
            f"{name} ({product_id}) costs "
            f"{format_currency(price)} per unit."
        )

    else:

        response = (
            f"{name} ({product_id}) costs "
            f"{format_currency(price)} per unit.\n\n"
            f"{quantity} units: "
            f"{format_currency(total)}"
        )

    return {
        "success": True,
        "type": "PRICE",
        "product": product,
        "quantity": quantity,
        "unit_price": price,
        "total": total,
        "response": response,
    }


# ============================================================
# STOCK
# ============================================================

def process_stock_request(
    text: str,
) -> Dict[str, Any]:
    """
    Process stock availability request.
    """

    product = identify_product(
        text
    )

    if not product:

        return {
            "success": False,
            "type": "STOCK",
            "response": (
                "I could not identify the product "
                "you are asking about. Please provide "
                "the product name or product ID."
            ),
        }

    quantity = extract_quantity(
        text
    )

    product_id = product[
        "product_id"
    ]

    name = product_name(
        product
    )

    stock_result = check_stock(
        product_id,
        quantity,
    )

    available = bool(
        stock_result.get(
            "available",
            False,
        )
    )

    available_quantity = int(
        stock_result.get(
            "available_quantity",
            product_stock(product),
        )
    )

    if available:

        response = (
            f"Yes. We have enough stock for "
            f"{quantity} {name.lower()}.\n\n"
            f"Available stock: "
            f"{available_quantity}"
        )

    else:

        response = (
            f"We do not currently have enough stock "
            f"for {quantity} {name.lower()}.\n\n"
            f"Available stock: "
            f"{available_quantity}"
        )

    return {
        "success": True,
        "type": "STOCK",
        "product": product,
        "quantity": quantity,
        "available": available,
        "stock": available_quantity,
        "response": response,
    }


# ============================================================
# PRODUCT SEARCH
# ============================================================

def process_product_search(
    text: str,
) -> Dict[str, Any]:
    """
    Search for products.
    """

    results = search_products(
        text
    )

    if not results:

        return {
            "success": False,
            "type": "SEARCH",
            "response": (
                "I could not find any products "
                "matching your request."
            ),
        }

    lines = [
        "I found the following products:",
        "",
    ]

    for product in results:

        product_id = product.get(
            "product_id",
            "N/A",
        )

        name = product_name(
            product
        )

        price = product_price(
            product
        )

        lines.append(
            f"- {name} ({product_id}) — "
            f"{format_currency(price)}"
        )

    return {
        "success": True,
        "type": "SEARCH",
        "products": results,
        "response": "\n".join(lines),
    }


# ============================================================
# QUOTATION
# ============================================================

def process_quotation_request(
    text: str,
) -> Dict[str, Any]:
    """
    Build a quotation.

    Supports:

        Give me a quotation for 5 office chairs.

    and:

        Give me a quotation for 5 office chairs
        and 2 office desks.

    and natural requests such as:

        I need 5 office chairs and 2 office desks.
    """

    normalized = normalize_text(
        text
    )

    # --------------------------------------------------------
    # Identify products mentioned in request
    # --------------------------------------------------------

    mentioned_products = find_mentioned_products(
        normalized
    )

    # --------------------------------------------------------
    # No products found
    # --------------------------------------------------------

    if not mentioned_products:

        return {
            "success": False,
            "type": "QUOTATION",
            "response": (
                "I could not identify the products "
                "for the quotation. Please provide "
                "the product names or product IDs."
            ),
        }

    # --------------------------------------------------------
    # Extract individual quantities
    # --------------------------------------------------------

    items = extract_product_quantities(
        normalized,
        mentioned_products,
    )

    # --------------------------------------------------------
    # Build quotation
    # --------------------------------------------------------

    quotation = build_quotation(
        items
    )

    if not quotation:

        return {
            "success": False,
            "type": "QUOTATION",
            "response": (
                "I could not generate the quotation. "
                "Please check the product names, "
                "quantities, and stock availability."
            ),
        }

    # --------------------------------------------------------
    # Handle quotation errors
    # --------------------------------------------------------

    if isinstance(
        quotation,
        dict,
    ):

        if quotation.get(
            "success"
        ) is False:

            message = quotation.get(
                "message",
                quotation.get(
                    "error",
                    "The quotation could not be generated.",
                ),
            )

            return {
                "success": False,
                "type": "QUOTATION",
                "response": str(message),
                "quotation": quotation,
            }

    # --------------------------------------------------------
    # Get totals
    # --------------------------------------------------------

    subtotal = float(
        quotation.get(
            "subtotal",
            0,
        )
    )

    delivery_fee = float(
        quotation.get(
            "delivery_fee",
            0,
        )
    )

    total = float(
        quotation.get(
            "total",
            0,
        )
    )

    # --------------------------------------------------------
    # Build response
    # --------------------------------------------------------

    lines = [
        "Quotation",
        "",
    ]

    line_items = quotation.get(
        "items",
        quotation.get(
            "line_items",
            [],
        ),
    )

    if line_items:

        for item in line_items:

            item_product_name = item.get(
                "product_name",
                item.get(
                    "name",
                    "Product",
                ),
            )

            quantity = int(
                item.get(
                    "quantity",
                    1,
                )
            )

            unit_price = float(
                item.get(
                    "unit_price",
                    item.get(
                        "price",
                        0,
                    ),
                )
            )

            line_total = float(
                item.get(
                    "line_total",
                    item.get(
                        "total",
                        unit_price * quantity,
                    ),
                )
            )

            lines.append(
                f"{item_product_name}: "
                f"{quantity} × "
                f"{format_currency(unit_price)} = "
                f"{format_currency(line_total)}"
            )

    else:

        # ----------------------------------------------------
        # Fallback calculation
        # ----------------------------------------------------

        for item in items:

            product = get_product(
                item["product_id"]
            )

            if not product:
                continue

            quantity = int(
                item["quantity"]
            )

            unit_price = product_price(
                product
            )

            line_total = (
                unit_price * quantity
            )

            lines.append(
                f"{product_name(product)}: "
                f"{quantity} × "
                f"{format_currency(unit_price)} = "
                f"{format_currency(line_total)}"
            )

    lines.extend(
        [
            "",
            f"Subtotal: "
            f"{format_currency(subtotal)}",
            f"Delivery: "
            f"{format_currency(delivery_fee)}",
            f"Total: "
            f"{format_currency(total)}",
        ]
    )

    return {
        "success": True,
        "type": "QUOTATION",
        "items": items,
        "quotation": quotation,
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "total": total,
        "response": "\n".join(lines),
    }


# ============================================================
# RECOMMENDATIONS
# ============================================================

def process_recommendation_request(
    text: str,
) -> Dict[str, Any]:
    """
    Provide simple product recommendations.
    """

    normalized = normalize_text(
        text
    )

    search_text = re.sub(
        r"\b("
        r"recommend|"
        r"recommendation|"
        r"suggest|"
        r"suggestion|"
        r"best|"
        r"good|"
        r"looking for|"
        r"need|"
        r"want|"
        r"show me"
        r")\b",
        "",
        normalized,
    ).strip()

    results = search_products(
        search_text
    )

    if not results:

        products = get_product_catalogue()

        if products:
            results = products[:5]

    if not results:

        return {
            "success": False,
            "type": "RECOMMENDATION",
            "response": (
                "I could not find suitable products "
                "for your request."
            ),
        }

    lines = [
        "Here are some products you may consider:",
        "",
    ]

    for product in results[:5]:

        name = product_name(
            product
        )

        product_id = product.get(
            "product_id",
            "N/A",
        )

        price = product_price(
            product
        )

        lines.append(
            f"- {name} ({product_id}) — "
            f"{format_currency(price)}"
        )

    return {
        "success": True,
        "type": "RECOMMENDATION",
        "products": results[:5],
        "response": "\n".join(lines),
    }


# ============================================================
# REQUEST CLASSIFICATION
# ============================================================

def classify_sales_request(
    text: str,
) -> str:
    """
    Classify a customer request.

    Possible results:

        CATALOGUE
        QUOTATION
        STOCK
        PRICE
        RECOMMENDATION
        SEARCH
    """

    normalized = normalize_text(
        text
    )

    if not normalized:

        return "SEARCH"

    # --------------------------------------------------------
    # Catalogue FIRST
    # --------------------------------------------------------

    if is_product_catalogue_request(
        normalized
    ):
        return "CATALOGUE"

    # --------------------------------------------------------
    # Explicit quotation
    # --------------------------------------------------------

    quotation_patterns = [
        r"\bquotation\b",
        r"\bquote\b",
        r"\bprice quote\b",
        r"\bget me a quote\b",
        r"\bgive me a quote\b",
        r"\bgive me a quotation\b",
        r"\bprepare a quotation\b",
        r"\bprepare a quote\b",
        r"\bquotation for\b",
        r"\bquote for\b",
    ]

    if any(
        re.search(
            pattern,
            normalized,
        )
        for pattern in quotation_patterns
    ):
        return "QUOTATION"

    # --------------------------------------------------------
    # Natural quantity-based quotation
    # --------------------------------------------------------
    #
    # This handles requests such as:
    #
    # "I need 5 office chairs and 2 office desks"
    # "I need five office chairs"
    # "5 office chairs and 2 office desks"
    #
    # Explicit order requests are excluded.
    # --------------------------------------------------------

    if is_quantity_based_quotation_request(
        normalized
    ):
        return "QUOTATION"

    # --------------------------------------------------------
    # Stock
    # --------------------------------------------------------

    stock_patterns = [
        r"\bin stock\b",
        r"\bstock\b",
        r"\bavailable\b",
        r"\bavailability\b",
        r"\bdo you have\b",
        r"\bhow many.*available\b",
        r"\bhow many.*in stock\b",
    ]

    if any(
        re.search(
            pattern,
            normalized,
        )
        for pattern in stock_patterns
    ):
        return "STOCK"

    # --------------------------------------------------------
    # Recommendation
    # --------------------------------------------------------

    recommendation_patterns = [
        r"\brecommend\b",
        r"\brecommendation\b",
        r"\bsuggest\b",
        r"\bsuggestion\b",
        r"\bwhat.*best\b",
        r"\bwhich.*best\b",
        r"\bwhat.*should i buy\b",
        r"\bwhich.*should i buy\b",
    ]

    if any(
        re.search(
            pattern,
            normalized,
        )
        for pattern in recommendation_patterns
    ):
        return "RECOMMENDATION"

    # --------------------------------------------------------
    # Price
    # --------------------------------------------------------

    price_patterns = [
        r"\bhow much\b",
        r"\bprice\b",
        r"\bcost\b",
        r"\bcosts\b",
        r"\bpricing\b",
        r"\brate\b",
        r"\bper unit\b",
    ]

    if any(
        re.search(
            pattern,
            normalized,
        )
        for pattern in price_patterns
    ):
        return "PRICE"

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    search_patterns = [
        r"\bfind\b",
        r"\bsearch\b",
        r"\blooking for\b",
        r"\bdo you sell\b",
        r"\bdo you stock\b",
    ]

    if any(
        re.search(
            pattern,
            normalized,
        )
        for pattern in search_patterns
    ):
        return "SEARCH"

    return "SEARCH"


# ============================================================
# MAIN SALES PROCESSOR
# ============================================================

def process_sales_request(
    customer_message: str,
) -> Dict[str, Any]:
    """
    Main entry point for the Sales Agent.
    """

    if not customer_message:

        return {
            "success": False,
            "type": "UNKNOWN",
            "response": (
                "Please tell me what product or "
                "sales information you need."
            ),
        }

    request_type = classify_sales_request(
        customer_message
    )

    # --------------------------------------------------------
    # Catalogue
    # --------------------------------------------------------

    if request_type == "CATALOGUE":

        return process_product_catalogue_request()

    # --------------------------------------------------------
    # Quotation
    # --------------------------------------------------------

    if request_type == "QUOTATION":

        return process_quotation_request(
            customer_message
        )

    # --------------------------------------------------------
    # Stock
    # --------------------------------------------------------

    if request_type == "STOCK":

        return process_stock_request(
            customer_message
        )

    # --------------------------------------------------------
    # Recommendation
    # --------------------------------------------------------

    if request_type == "RECOMMENDATION":

        return process_recommendation_request(
            customer_message
        )

    # --------------------------------------------------------
    # Price
    # --------------------------------------------------------

    if request_type == "PRICE":

        return process_price_request(
            customer_message
        )

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    if request_type == "SEARCH":

        return process_product_search(
            customer_message
        )

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    return {
        "success": False,
        "type": "UNKNOWN",
        "response": (
            "I could not understand your sales request. "
            "Please ask about products, prices, stock, "
            "recommendations, or quotations."
        ),
    }


# ============================================================
# TESTS
# ============================================================

def run_tests() -> None:
    """
    Run Sales Agent tests.
    """

    print("=" * 70)
    print("KENYABIZ AI")
    print("SALES AGENT TESTS")
    print("=" * 70)

    tests = [

        # ----------------------------------------------------
        # Catalogue
        # ----------------------------------------------------

        (
            "What products do you have?",
            "CATALOGUE",
        ),

        (
            "Show me all products.",
            "CATALOGUE",
        ),

        (
            "What items do you sell?",
            "CATALOGUE",
        ),

        # ----------------------------------------------------
        # Prices
        # ----------------------------------------------------

        (
            "How much is an office chair?",
            "PRICE",
        ),

        (
            "How much is an office desk?",
            "PRICE",
        ),

        (
            "What is the price of an executive desk?",
            "PRICE",
        ),

        (
            "How much is a visitor chair?",
            "PRICE",
        ),

        (
            "How much are 5 office chairs?",
            "PRICE",
        ),

        (
            "What is the price of 2 office desks?",
            "PRICE",
        ),

        # ----------------------------------------------------
        # Stock
        # ----------------------------------------------------

        (
            "Do you have office chairs in stock?",
            "STOCK",
        ),

        (
            "Do you have 10 office chairs in stock?",
            "STOCK",
        ),

        (
            "Is an office desk available?",
            "STOCK",
        ),

        # ----------------------------------------------------
        # Explicit quotations
        # ----------------------------------------------------

        (
            "Give me a quotation for 2 office chairs.",
            "QUOTATION",
        ),

        (
            "Give me a quote for 3 office desks.",
            "QUOTATION",
        ),

        (
            "Prepare a quotation for 5 office chairs.",
            "QUOTATION",
        ),

        (
            "Give me a quotation for 5 office chairs and 2 office desks.",
            "QUOTATION",
        ),

        (
            "Give me a quotation for five office chairs and two office desks.",
            "QUOTATION",
        ),

        # ----------------------------------------------------
        # Natural quantity-based quotations
        # ----------------------------------------------------

        (
            "I need 5 office chairs and 2 office desks.",
            "QUOTATION",
        ),

        (
            "I need five office chairs and two office desks.",
            "QUOTATION",
        ),

        (
            "5 office chairs and 2 office desks.",
            "QUOTATION",
        ),

        (
            "I need 5 office chairs.",
            "QUOTATION",
        ),

        (
            "I need five office desks.",
            "QUOTATION",
        ),

        (
            "I want 3 keyboards.",
            "QUOTATION",
        ),

        # ----------------------------------------------------
        # Explicit orders
        #
        # These are intentionally NOT quotations.
        # They should ultimately be handled by the
        # Order Agent through main.py / graph.py.
        # ----------------------------------------------------

        (
            "I want to order 2 office chairs.",
            "SEARCH",
        ),

        (
            "Please place an order for 5 office chairs.",
            "SEARCH",
        ),

        (
            "I want to buy 3 office desks.",
            "SEARCH",
        ),

        (
            "Please purchase 2 keyboards.",
            "SEARCH",
        ),

        # ----------------------------------------------------
        # Recommendations
        # ----------------------------------------------------

        (
            "Can you recommend an office chair?",
            "RECOMMENDATION",
        ),

        (
            "What office furniture do you recommend?",
            "RECOMMENDATION",
        ),

        # ----------------------------------------------------
        # Product IDs
        # ----------------------------------------------------

        (
            "How much is P001?",
            "PRICE",
        ),

        (
            "Is P002 in stock?",
            "STOCK",
        ),

        # ----------------------------------------------------
        # Actual products P007-P009
        # ----------------------------------------------------

        (
            "How much is a monitor stand?",
            "PRICE",
        ),

        (
            "How much is a keyboard?",
            "PRICE",
        ),

        (
            "How much is a wireless mouse?",
            "PRICE",
        ),
    ]

    passed = 0
    failed = 0

    for number, (
        message,
        expected_type,
    ) in enumerate(
        tests,
        start=1,
    ):

        print()
        print("-" * 70)
        print(f"TEST {number}")
        print(f"Customer: {message}")
        print(f"Expected: {expected_type}")

        try:

            result = process_sales_request(
                message
            )

            actual_type = result.get(
                "type",
                "UNKNOWN",
            )

            success = (
                result.get(
                    "success",
                    False,
                )
                and actual_type
                == expected_type
            )

            print(
                f"Type: {actual_type}"
            )

            print(
                f"Success: "
                f"{result.get('success', False)}"
            )

            print("Response:")

            print(
                result.get(
                    "response",
                    "No response.",
                )
            )

            if success:

                passed += 1

                print(
                    "TEST RESULT: PASS"
                )

            else:

                failed += 1

                print(
                    "TEST RESULT: FAIL"
                )

        except Exception as exc:

            failed += 1

            print(
                "TEST RESULT: FAIL"
            )

            print(
                f"Error: "
                f"{type(exc).__name__}: {exc}"
            )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("SALES AGENT TEST SUMMARY")
    print("=" * 70)

    print(
        f"Total tests : {len(tests)}"
    )

    print(
        f"Passed      : {passed}"
    )

    print(
        f"Failed      : {failed}"
    )

    if failed == 0:

        print()
        print(
            "ALL SALES AGENT TESTS PASSED."
        )

    else:

        print()
        print(
            "Some tests failed. "
            "Review the output above."
        )

    print("=" * 70)


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    run_tests()