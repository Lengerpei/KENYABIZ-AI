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
)

from src.tools.quotation_tool import build_quotation


# ============================================================
# PRODUCT ID ALIASES
# ============================================================

PRODUCT_IDS = {
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
    """Normalize customer text."""

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
    Extract a general quantity.

    Examples:
        5 office chairs -> 5
        five office chairs -> 5
        office chairs -> 1
    """

    normalized = normalize_text(text)

    match = re.search(
        r"\b(\d+)\b",
        normalized,
    )

    if match:
        quantity = int(match.group(1))

        if quantity > 0:
            return quantity

    for word, number in NUMBER_WORDS.items():
        if re.search(
            rf"\b{re.escape(word)}\b",
            normalized,
        ):
            return number

    return default


def extract_quantity_for_product(
    text: str,
    product_name_text: str,
    default: int = 1,
) -> int:
    """
    Extract quantity belonging to a particular product.
    """

    normalized = normalize_text(text)
    product_name_text = normalize_text(product_name_text)

    product_variants = [product_name_text]

    if product_name_text.endswith("s"):
        singular = product_name_text[:-1]

        if singular not in product_variants:
            product_variants.append(singular)

    else:
        plural = product_name_text + "s"

        if plural not in product_variants:
            product_variants.append(plural)

    product_position = -1

    for variant in product_variants:
        position = normalized.find(variant)

        if position != -1:
            product_position = position
            break

    if product_position == -1:
        return default

    before = normalized[:product_position]

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
    """Extract quantities for each mentioned product."""

    items = []

    for product in products:

        name = product_name(product)

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
    """Identify one product."""

    normalized = normalize_text(text)

    # --------------------------------------------------------
    # Product ID
    # --------------------------------------------------------

    product_id_match = re.search(
        r"\bP\d{3}\b",
        normalized.upper(),
    )

    if product_id_match:

        product_id = product_id_match.group(0)

        product = get_product(product_id)

        if product:
            return product

    # --------------------------------------------------------
    # Known aliases
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

            product = get_product(product_id)

            if product:
                return product

    # --------------------------------------------------------
    # Database search
    # --------------------------------------------------------

    results = search_products(normalized)

    if results:
        return results[0]

    return None


# ============================================================
# PRODUCT MENTION DETECTION
# ============================================================

def find_mentioned_products(
    text: str,
) -> List[Dict[str, Any]]:
    """Return all known products mentioned."""

    normalized = normalize_text(text)

    mentioned_products = []

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

            product = get_product(product_id)

            if product:

                if not any(
                    existing.get("product_id")
                    == product_id
                    for existing in mentioned_products
                ):
                    mentioned_products.append(product)

    product_ids = re.findall(
        r"\bP\d{3}\b",
        normalized.upper(),
    )

    for product_id in product_ids:

        product = get_product(product_id)

        if product:

            if not any(
                existing.get("product_id")
                == product_id
                for existing in mentioned_products
            ):
                mentioned_products.append(product)

    return mentioned_products


# ============================================================
# EXPLICIT ORDER DETECTION
# ============================================================

def is_explicit_order_request(
    text: str,
) -> bool:
    """
    Detect requests that explicitly want to place an order.
    """

    normalized = normalize_text(text)

    order_patterns = [

        r"\border\b",
        r"\bordering\b",
        r"\borders\b",

        r"\bplace an order\b",
        r"\bplace my order\b",
        r"\bplace the order\b",

        r"\bi want to order\b",
        r"\bi would like to order\b",
        r"\bi'd like to order\b",
        r"\bi need to order\b",

        r"\bi want to buy\b",
        r"\bi would like to buy\b",
        r"\bi'd like to buy\b",
        r"\bi need to buy\b",

        r"\bpurchase\b",

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
# QUANTITY DETECTION
# ============================================================

def has_quantity(
    text: str,
) -> bool:

    normalized = normalize_text(text)

    if re.search(
        r"\b\d+\b",
        normalized,
    ):
        return True

    return any(
        re.search(
            rf"\b{re.escape(word)}\b",
            normalized,
        )
        for word in NUMBER_WORDS
    )


# ============================================================
# STOCK REQUEST DETECTION
# ============================================================

def is_stock_request(
    text: str,
) -> bool:
    """
    Detect requests asking about product availability or stock.

    Examples:
        Do you have office chairs in stock?
        Do you have 100 office chairs in stock?
        Is the office chair available?
        How many office desks do you have?
        How much stock do you have?
    """

    normalized = normalize_text(text)

    if not normalized:
        return False

    stock_patterns = [

        r"\bin stock\b",
        r"\bin-stock\b",
        r"\bstock\b",

        r"\bavailable\b",
        r"\bavailability\b",

        r"\bdo you have\b",

        r"\bis there any\b",
        r"\bare there any\b",

        r"\bhow many.*available\b",
        r"\bhow many.*in stock\b",
        r"\bhow many.*do you have\b",

        r"\bhow much stock\b",
        r"\bhow much.*in stock\b",
    ]

    return any(
        re.search(
            pattern,
            normalized,
        )
        for pattern in stock_patterns
    )


def is_stock_quantity_question(
    text: str,
) -> bool:
    """
    Detect questions asking for the actual stock quantity.

    Examples:
        How many office chairs are available?
        How many office chairs do you have?
        How much stock do you have for office chairs?
    """

    normalized = normalize_text(text)

    quantity_patterns = [
        r"\bhow many\b",
        r"\bhow much stock\b",
        r"\bhow much.*in stock\b",
    ]

    return any(
        re.search(
            pattern,
            normalized,
        )
        for pattern in quantity_patterns
    )


# ============================================================
# QUANTITY-BASED QUOTATION
# ============================================================

def is_quantity_based_quotation_request(
    text: str,
) -> bool:
    """
    Detect natural quotation requests.

    Explicit orders are excluded.
    Stock requests are excluded.
    Price questions are excluded.
    """

    normalized = normalize_text(text)

    # --------------------------------------------------------
    # Stock questions are not quotations.
    # --------------------------------------------------------

    if is_stock_request(normalized):
        return False

    # --------------------------------------------------------
    # Explicit orders belong to Order Agent.
    # --------------------------------------------------------

    if is_explicit_order_request(normalized):
        return False

    # --------------------------------------------------------
    # Direct price questions are PRICE requests.
    # --------------------------------------------------------

    price_patterns = [
        r"\bhow much\b",
        r"\bwhat is the price\b",
        r"\bwhat's the price\b",
        r"\bwhats the price\b",
        r"\bprice of\b",
        r"\bprice for\b",
        r"\bcost of\b",
        r"\bcost for\b",
    ]

    if any(
        re.search(
            pattern,
            normalized,
        )
        for pattern in price_patterns
    ):
        return False

    if not has_quantity(normalized):
        return False

    mentioned_products = find_mentioned_products(
        normalized
    )

    return bool(mentioned_products)


# ============================================================
# PRODUCT CATALOGUE
# ============================================================

def get_product_catalogue() -> List[Dict[str, Any]]:
    """Return all known products."""

    products = []

    product_ids = sorted(
        set(PRODUCT_IDS.values())
    )

    for product_id in product_ids:

        product = get_product(product_id)

        if product:

            if not any(
                p["product_id"] == product_id
                for p in products
            ):
                products.append(product)

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

    normalized = normalize_text(text)

    patterns = [

        r"\bwhat products do you have\b",
        r"\bwhat products are available\b",
        r"\bwhat products do you sell\b",
        r"\bwhich products do you have\b",
        r"\bwhich products are available\b",

        r"\bwhat items do you have\b",
        r"\bwhat items are available\b",
        r"\bwhat items do you sell\b",
        r"\bwhich items do you have\b",
        r"\bwhich items are available\b",

        r"\bshow me your catalogue\b",
        r"\bshow me the catalogue\b",
        r"\bshow your catalogue\b",
        r"\bshow catalogue\b",
        r"\bproduct catalogue\b",
        r"\bproduct catalog\b",

        r"\blist your products\b",
        r"\blist the products\b",
        r"\blist products\b",
        r"\blist your items\b",
        r"\blist the items\b",
        r"\blist items\b",

        r"\bshow me all products\b",
        r"\bshow me all the products\b",
        r"\bshow all products\b",
        r"\bshow me all items\b",
        r"\bshow me all the items\b",
        r"\bshow all items\b",

        r"\bshow me your products\b",
        r"\bshow me your items\b",

        r"\bwhat do you sell\b",
        r"\bwhat are you selling\b",
        r"\bproducts you sell\b",
        r"\bitems you sell\b",

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

        name = product_name(product)
        price = product_price(product)

        lines.append(
            f"- {name} ({product_id}) — "
            f"{format_currency(price)} per unit"
        )

    return "\n".join(lines)


def process_product_catalogue_request() -> Dict[str, Any]:

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

    product = identify_product(text)

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

    quantity = extract_quantity(text)

    price = product_price(product)
    total = price * quantity

    name = product_name(product)
    product_id = product["product_id"]

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

    product = identify_product(text)

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

    product_id = product["product_id"]
    name = product_name(product)

    # --------------------------------------------------------
    # If customer asks for the actual stock quantity
    # --------------------------------------------------------

    if is_stock_quantity_question(text):

        stock_result = check_stock(
            product_id,
            1,
        )

        available_quantity = int(
            stock_result.get(
                "available_quantity",
                product_stock(product),
            )
        )

        response = (
            f"We currently have "
            f"{available_quantity} units of "
            f"{name.lower()} in stock."
        )

        return {
            "success": True,
            "type": "STOCK",
            "product": product,
            "quantity": available_quantity,
            "available": available_quantity > 0,
            "stock": available_quantity,
            "response": response,
        }

    # --------------------------------------------------------
    # Customer is asking whether a specific quantity is
    # available.
    # --------------------------------------------------------

    quantity = extract_quantity(text)

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
    Perform product search.

    Explicit order requests are returned as SEARCH because
    the Sales Agent test suite uses SEARCH as the classification
    for requests that should subsequently be handled by the
    Order Agent.
    """

    # --------------------------------------------------------
    # Explicit order requests
    #
    # The Supervisor/Order Agent handles the actual order.
    # Sales Agent simply identifies this as an order/search
    # type and reports success.
    # --------------------------------------------------------

    if is_explicit_order_request(text):

        product_results = find_mentioned_products(text)

        if product_results:

            product_lines = []

            for product in product_results:

                product_lines.append(
                    f"- {product_name(product)} "
                    f"({product['product_id']}) — "
                    f"{format_currency(product_price(product))}"
                )

            response = (
                "This is an order request. "
                "The Order Agent should handle the order.\n\n"
                "Products identified:\n"
                + "\n".join(product_lines)
            )

        else:

            response = (
                "This is an order request. "
                "The Order Agent should handle the order."
            )

        return {
            "success": True,
            "type": "SEARCH",
            "products": product_results,
            "response": response,
        }

    # --------------------------------------------------------
    # Normal product search
    # --------------------------------------------------------

    results = search_products(text)

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

        name = product_name(product)
        price = product_price(product)

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

    normalized = normalize_text(text)

    # Never generate quotations for stock requests.

    if is_stock_request(normalized):

        return {
            "success": False,
            "type": "STOCK",
            "response": (
                "This appears to be a stock availability "
                "request rather than a quotation request."
            ),
        }

    # Never generate quotations for explicit orders.

    if is_explicit_order_request(normalized):

        return {
            "success": False,
            "type": "SEARCH",
            "response": (
                "This is an order request. "
                "The Order Agent should handle it."
            ),
        }

    mentioned_products = find_mentioned_products(
        normalized
    )

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

    items = extract_product_quantities(
        normalized,
        mentioned_products,
    )

    quotation = build_quotation(items)

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

    if isinstance(quotation, dict):

        if quotation.get("success") is False:

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

        for item in items:

            product = get_product(
                item["product_id"]
            )

            if not product:
                continue

            quantity = int(
                item["quantity"]
            )

            unit_price = product_price(product)

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

    normalized = normalize_text(text)

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

    results = search_products(search_text)

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

        name = product_name(product)

        product_id = product.get(
            "product_id",
            "N/A",
        )

        price = product_price(product)

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

    normalized = normalize_text(text)

    if not normalized:
        return "SEARCH"

    # ========================================================
    # 1. CATALOGUE
    # ========================================================

    if is_product_catalogue_request(normalized):
        return "CATALOGUE"

    # ========================================================
    # 2. STOCK
    #
    # Stock MUST be checked before quotation logic.
    # ========================================================

    if is_stock_request(normalized):
        return "STOCK"

    # ========================================================
    # 3. EXPLICIT QUOTATION
    # ========================================================

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

    # ========================================================
    # 4. EXPLICIT ORDER
    #
    # Explicit orders should not become quotations.
    # ========================================================

    if is_explicit_order_request(normalized):
        return "SEARCH"

    # ========================================================
    # 5. PRICE
    #
    # IMPORTANT:
    # Price must come BEFORE natural quantity quotation.
    #
    # This fixes:
    #   How much are 5 office chairs?
    #   What is the price of 2 office desks?
    # ========================================================

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

    # ========================================================
    # 6. NATURAL QUANTITY QUOTATION
    # ========================================================

    if is_quantity_based_quotation_request(normalized):
        return "QUOTATION"

    # ========================================================
    # 7. RECOMMENDATION
    # ========================================================

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

    # ========================================================
    # 8. SEARCH
    # ========================================================

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

    if request_type == "CATALOGUE":

        return process_product_catalogue_request()

    if request_type == "QUOTATION":

        return process_quotation_request(
            customer_message
        )

    if request_type == "STOCK":

        return process_stock_request(
            customer_message
        )

    if request_type == "RECOMMENDATION":

        return process_recommendation_request(
            customer_message
        )

    if request_type == "PRICE":

        return process_price_request(
            customer_message
        )

    if request_type == "SEARCH":

        return process_product_search(
            customer_message
        )

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
# SALES AGENT TESTS
# ============================================================

def run_tests() -> None:

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
            "Do you have 100 office chairs in stock?",
            "STOCK",
        ),

        (
            "Is an office desk available?",
            "STOCK",
        ),

        (
            "How many office chairs are available?",
            "STOCK",
        ),

        (
            "How much stock do you have for office chairs?",
            "STOCK",
        ),

        (
            "Is P002 in stock?",
            "STOCK",
        ),

        # ----------------------------------------------------
        # Quotations
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
        # Natural quotations
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
        # Products P007-P009
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

    for number, (message, expected_type) in enumerate(
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
                result.get("success", False)
                and actual_type == expected_type
            )

            print(f"Type: {actual_type}")

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